"""FHIR R4 Practitioner -> Synthea Provider"""

from fhir.resources.practitioner import Practitioner
from synthea_pydantic import Provider as SyntheaProvider

from ..chidian_ext import grab, mapper, to_dict


def _reverse_gender(gender: str | None) -> str | None:
    """Map FHIR gender back to Synthea gender code."""
    if not gender:
        return None
    gender_map = {"male": "M", "female": "F"}
    return gender_map.get(gender.lower())


def _extract_name(d: dict) -> str:
    """Extract full name from FHIR HumanName array."""
    names = grab(d, "name") or []
    if not names:
        return ""
    name = names[0]
    given = name.get("given", [])
    family = name.get("family", "")
    given_str = given[0] if given else ""
    if given_str and family:
        return f"{given_str} {family}"
    return given_str or family or ""


def _extract_address_field(d: dict, field: str) -> str:
    """Extract a field from the first address."""
    addresses = grab(d, "address") or []
    if not addresses:
        return ""
    return addresses[0].get(field, "") or ""


def _extract_address_line(d: dict) -> str:
    """Extract address line."""
    addresses = grab(d, "address") or []
    if not addresses:
        return ""
    lines = addresses[0].get("line", [])
    return lines[0] if lines else ""


def _extract_geolocation(d: dict) -> tuple[str, str]:
    """Extract lat/lon from address geolocation extension."""
    addresses = grab(d, "address") or []
    if not addresses:
        return ("", "")
    extensions = addresses[0].get("extension", [])
    lat = ""
    lon = ""
    for ext in extensions:
        if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/geolocation":
            nested = ext.get("extension", [])
            for n in nested:
                if n.get("url") == "latitude":
                    lat = str(n.get("valueDecimal", ""))
                elif n.get("url") == "longitude":
                    lon = str(n.get("valueDecimal", ""))
    return (lat, lon)


@mapper(remove_empty=False)
def _to_synthea_provider(d: dict):
    """Core mapping from FHIR Practitioner dict to Synthea structure."""
    lat, lon = _extract_geolocation(d)

    return {
        "id": grab(d, "id") or None,
        "organization": None,
        "name": _extract_name(d) or None,
        "gender": _reverse_gender(grab(d, "gender")),
        "speciality": None,
        "address": _extract_address_line(d) or None,
        "city": _extract_address_field(d, "city") or None,
        "state": _extract_address_field(d, "state") or None,
        "zip": _extract_address_field(d, "postalCode") or None,
        "lat": lat or None,
        "lon": lon or None,
        "encounters": None,
        "procedures": None,
        "immunizations": None,
        "utilization": None,
    }


def convert(src: Practitioner) -> SyntheaProvider:
    """Convert FHIR R4 Practitioner to Synthea Provider.

    Args:
        src: FHIR R4 Practitioner resource

    Returns:
        Synthea Provider model
    """
    return SyntheaProvider(**_to_synthea_provider(to_dict(src)))
