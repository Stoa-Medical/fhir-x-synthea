"""Synthea Organization → FHIR R4 Organization"""

from typing import Any

from fhir.resources.organization import Organization
from synthea_pydantic import Organization as SyntheaOrganization

from ..utils import split_phones, to_str


def convert(src: SyntheaOrganization) -> Organization:
    """Convert Synthea Organization to FHIR R4 Organization.

    Args:
        src: Synthea Organization model

    Returns:
        FHIR R4 Organization resource
    """
    d = src.model_dump()

    # Extract fields
    org_id = to_str(d.get("id"))
    name = to_str(d.get("name"))
    address = to_str(d.get("address"))
    city = to_str(d.get("city"))
    state = to_str(d.get("state"))
    zip_code = to_str(d.get("zip"))
    phone_str = to_str(d.get("phone"))

    # Handle numeric fields
    lat = d.get("lat")
    lon = d.get("lon")
    revenue = d.get("revenue")
    utilization = d.get("utilization")

    # Build resource
    resource: dict[str, Any] = {"resourceType": "Organization"}

    if org_id:
        resource["id"] = org_id

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

        if lat is not None and lon is not None:
            address_obj.setdefault("extension", []).append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                    "extension": [
                        {"url": "latitude", "valueDecimal": float(lat)},
                        {"url": "longitude", "valueDecimal": float(lon)},
                    ],
                }
            )

        resource["address"] = [address_obj]

    # Set telecom
    phones = split_phones(phone_str)
    if phones:
        resource["telecom"] = [{"system": "phone", "value": phone} for phone in phones]

    # Set extensions for stats
    extensions = []
    if revenue is not None or utilization is not None:
        stats_ext: dict[str, Any] = {
            "url": "http://synthea.mitre.org/fhir/StructureDefinition/organization-stats",
            "extension": [],
        }
        if revenue is not None:
            stats_ext["extension"].append(
                {"url": "revenue", "valueDecimal": float(revenue)}
            )
        if utilization is not None:
            stats_ext["extension"].append(
                {"url": "utilization", "valueInteger": int(utilization)}
            )
        if stats_ext["extension"]:
            extensions.append(stats_ext)

    if extensions:
        resource["extension"] = extensions

    return Organization(**resource)
