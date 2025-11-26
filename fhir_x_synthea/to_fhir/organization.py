"""
Mapping function for converting Synthea organizations.csv rows to FHIR Organization resources.
"""

import re
from typing import Any


def map_organization(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea organizations.csv row to a FHIR R4 Organization resource.

    Args:
        csv_row: Dictionary with keys like Id, Name, Address, City, State, Zip,
                Lat, Lon, Phone, Revenue, Utilization

    Returns:
        Dictionary representing a FHIR Organization resource
    """

    # Helper to split phone numbers
    def split_phones(phone_str: str | None) -> list[str]:
        if not phone_str or phone_str.strip() == "":
            return []
        # Split on common delimiters: comma, semicolon, slash, pipe
        phones = re.split(r"[,;/|]", phone_str)
        # Trim whitespace and filter empty strings
        return [p.strip() for p in phones if p.strip()]

    # Extract and process fields
    org_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    name = csv_row.get("Name", "").strip() if csv_row.get("Name") else ""
    address = csv_row.get("Address", "").strip() if csv_row.get("Address") else ""
    city = csv_row.get("City", "").strip() if csv_row.get("City") else ""
    state = csv_row.get("State", "").strip() if csv_row.get("State") else ""
    zip_code = csv_row.get("Zip", "").strip() if csv_row.get("Zip") else ""
    lat_str = csv_row.get("Lat", "").strip() if csv_row.get("Lat") else ""
    lon_str = csv_row.get("Lon", "").strip() if csv_row.get("Lon") else ""
    phone_str = csv_row.get("Phone", "").strip() if csv_row.get("Phone") else ""
    revenue_str = csv_row.get("Revenue", "").strip() if csv_row.get("Revenue") else ""
    utilization_str = (
        csv_row.get("Utilization", "").strip() if csv_row.get("Utilization") else ""
    )

    # Parse numeric fields
    lat = None
    lon = None
    if lat_str:
        try:
            lat = float(lat_str)
        except (ValueError, TypeError):
            pass
    if lon_str:
        try:
            lon = float(lon_str)
        except (ValueError, TypeError):
            pass

    revenue = None
    if revenue_str:
        try:
            revenue = float(revenue_str)
        except (ValueError, TypeError):
            pass

    utilization = None
    if utilization_str:
        try:
            utilization = int(utilization_str)
        except (ValueError, TypeError):
            pass

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Organization",
        "id": org_id if org_id else "",
    }

    # Set name (required)
    if name:
        resource["name"] = name

    # Set address
    if address or city or state or zip_code or (lat is not None and lon is not None):
        address_obj: dict[str, Any] = {}

        if address:
            address_obj["line"] = [address]
        if city:
            address_obj["city"] = city
        if state:
            address_obj["state"] = state
        if zip_code:
            address_obj["postalCode"] = zip_code

        # Geolocation extension
        if lat is not None and lon is not None:
            address_obj.setdefault("extension", []).append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                    "extension": [
                        {"url": "latitude", "valueDecimal": lat},
                        {"url": "longitude", "valueDecimal": lon},
                    ],
                }
            )

        resource["address"] = [address_obj]

    # Set telecom (phone numbers)
    phones = split_phones(phone_str)
    if phones:
        resource["telecom"] = [{"system": "phone", "value": phone} for phone in phones]

    # Set extensions (organization stats)
    extensions = []

    if revenue is not None or utilization is not None:
        stats_extension: dict[str, Any] = {
            "url": "http://synthea.mitre.org/fhir/StructureDefinition/organization-stats",
            "extension": [],
        }

        if revenue is not None:
            stats_extension["extension"].append(
                {"url": "revenue", "valueDecimal": revenue}
            )

        if utilization is not None:
            stats_extension["extension"].append(
                {"url": "utilization", "valueInteger": utilization}
            )

        if stats_extension["extension"]:
            extensions.append(stats_extension)

    if extensions:
        resource["extension"] = extensions

    return resource
