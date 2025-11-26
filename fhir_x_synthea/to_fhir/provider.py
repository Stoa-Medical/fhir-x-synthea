"""Synthea Provider → FHIR R4 Practitioner"""

from fhir.resources.practitioner import Practitioner
from synthea_pydantic import Provider as SyntheaProvider

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import map_gender, split_name


def _geolocation_extension(lat: float | None, lon: float | None):
    """Create geolocation extension if both lat/lon present."""
    if lat is None or lon is None:
        return None
    return {
        "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
        "extension": [
            {"url": "latitude", "valueDecimal": float(lat)},
            {"url": "longitude", "valueDecimal": float(lon)},
        ],
    }


def _name(name_str: str | None):
    """Build FHIR HumanName from name string."""
    given, family = split_name(name_str)
    if not given and not family:
        return None
    return {
        "use": "official",
        "given": [given] if given else None,
        "family": family,
    }


def _address(d: dict):
    """Build FHIR Address from source dict."""
    address = grab(d, "address")
    city = grab(d, "city")
    state = grab(d, "state")
    zip_code = grab(d, "zip")
    lat = grab(d, "lat")
    lon = grab(d, "lon")

    if not any([address, city, state, zip_code, lat is not None and lon is not None]):
        return None

    geo = _geolocation_extension(lat, lon)
    return {
        "line": [address] if address else None,
        "city": city,
        "state": state,
        "postalCode": zip_code,
        "extension": [geo] if geo else None,
    }


@mapper
def _to_fhir_provider(d: dict):
    """Core mapping from dict to FHIR Practitioner structure."""
    name = _name(grab(d, "name"))
    addr = _address(d)

    return {
        "resourceType": "Practitioner",
        "id": grab(d, "id"),
        "name": [name] if name else None,
        "gender": grab(d, "gender", apply=map_gender),
        "address": [addr] if addr else None,
    }


def convert(src: SyntheaProvider) -> Practitioner:
    """Convert Synthea Provider to FHIR R4 Practitioner.

    Args:
        src: Synthea Provider model

    Returns:
        FHIR R4 Practitioner resource
    """
    return Practitioner(**_to_fhir_provider(to_dict(src)))
