"""
Mapping functions for converting Synthea providers.csv rows to FHIR Practitioner and PractitionerRole resources.
"""

from typing import Any

from ..fhir_lib import create_reference, map_gender, split_name


def map_practitioner(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea providers.csv row to a FHIR R4 Practitioner resource.

    Args:
        csv_row: Dictionary with keys like Id, Name, Gender, Address, City, State, Zip, Lat, Lon

    Returns:
        Dictionary representing a FHIR Practitioner resource
    """

    # Extract and process fields
    provider_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    name = csv_row.get("Name", "").strip() if csv_row.get("Name") else ""
    gender = csv_row.get("Gender", "").strip() if csv_row.get("Gender") else ""
    address = csv_row.get("Address", "").strip() if csv_row.get("Address") else ""
    city = csv_row.get("City", "").strip() if csv_row.get("City") else ""
    state = csv_row.get("State", "").strip() if csv_row.get("State") else ""
    zip_code = csv_row.get("Zip", "").strip() if csv_row.get("Zip") else ""
    lat_str = csv_row.get("Lat", "").strip() if csv_row.get("Lat") else ""
    lon_str = csv_row.get("Lon", "").strip() if csv_row.get("Lon") else ""

    # Parse coordinates
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

    # Split name
    given, family = split_name(name)

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Practitioner",
        "id": provider_id if provider_id else "",
    }

    # Set name
    if given or family:
        name_obj: dict[str, Any] = {"use": "official"}
        if given:
            name_obj["given"] = [given]
        if family:
            name_obj["family"] = family
        resource["name"] = [name_obj]

    # Set gender
    mapped_gender = map_gender(gender)
    if mapped_gender:
        resource["gender"] = mapped_gender

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

    return resource


def map_practitioner_role(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea providers.csv row to a FHIR R4 PractitionerRole resource.

    Args:
        csv_row: Dictionary with keys like Id, Organization, Speciality, Encounters, Procedures

    Returns:
        Dictionary representing a FHIR PractitionerRole resource
    """

    # Extract and process fields
    provider_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    organization_id = (
        csv_row.get("Organization", "").strip() if csv_row.get("Organization") else ""
    )
    specialty = (
        csv_row.get("Speciality", "").strip() if csv_row.get("Speciality") else ""
    )
    encounters_str = (
        csv_row.get("Encounters", "").strip() if csv_row.get("Encounters") else ""
    )
    procedures_str = (
        csv_row.get("Procedures", "").strip() if csv_row.get("Procedures") else ""
    )

    # Parse numeric fields
    encounters = None
    if encounters_str:
        try:
            encounters = int(encounters_str)
        except (ValueError, TypeError):
            pass

    procedures = None
    if procedures_str:
        try:
            procedures = int(procedures_str)
        except (ValueError, TypeError):
            pass

    # Generate resource ID
    resource_id = (
        f"prr-{provider_id}-{organization_id}"
        if provider_id and organization_id
        else ""
    )

    # Build base resource
    resource: dict[str, Any] = {"resourceType": "PractitionerRole", "id": resource_id}

    # Set practitioner reference
    if provider_id:
        practitioner_ref = create_reference("Practitioner", provider_id)
        if practitioner_ref:
            resource["practitioner"] = practitioner_ref

    # Set organization reference
    if organization_id:
        org_ref = create_reference("Organization", organization_id)
        if org_ref:
            resource["organization"] = org_ref

    # Set code (specialty)
    if specialty:
        resource["code"] = [{"text": specialty, "coding": [{"display": specialty}]}]

    # Set extensions (provider stats)
    extensions = []

    if encounters is not None or procedures is not None:
        stats_extension: dict[str, Any] = {
            "url": "http://example.org/fhir/StructureDefinition/provider-stats",
            "extension": [],
        }

        if encounters is not None:
            stats_extension["extension"].append(
                {"url": "encounters", "valueInteger": encounters}
            )

        if procedures is not None:
            stats_extension["extension"].append(
                {"url": "procedures", "valueInteger": procedures}
            )

        if stats_extension["extension"]:
            extensions.append(stats_extension)

    if extensions:
        resource["extension"] = extensions

    return resource
