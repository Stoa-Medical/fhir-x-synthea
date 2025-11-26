"""Synthea Provider → FHIR R4 Practitioner"""

from typing import Any

from fhir.resources.practitioner import Practitioner
from synthea_pydantic import Provider as SyntheaProvider

from ..fhir_lib import map_gender, split_name
from ..utils import to_str


def convert(src: SyntheaProvider) -> Practitioner:
    """Convert Synthea Provider to FHIR R4 Practitioner.

    Args:
        src: Synthea Provider model

    Returns:
        FHIR R4 Practitioner resource
    """
    d = src.model_dump()

    # Extract fields
    provider_id = to_str(d.get("id"))
    name = to_str(d.get("name"))
    gender = to_str(d.get("gender"))
    address = to_str(d.get("address"))
    city = to_str(d.get("city"))
    state = to_str(d.get("state"))
    zip_code = to_str(d.get("zip"))

    # Handle numeric fields
    lat = d.get("lat")
    lon = d.get("lon")

    # Split name
    given, family = split_name(name)

    # Build resource
    resource: dict[str, Any] = {"resourceType": "Practitioner"}

    if provider_id:
        resource["id"] = provider_id

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

    return Practitioner(**resource)
