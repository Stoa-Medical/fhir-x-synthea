"""Synthea Organization → FHIR R4 Organization"""

from fhir.resources.organization import Organization
from synthea_pydantic import Organization as SyntheaOrganization

from ..chidian_ext import grab, mapper, to_dict
from ..utils import split_phones


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


def _telecom(phone_str: str | None):
    """Build telecom array from phone string."""
    phones = split_phones(phone_str)
    if not phones:
        return None
    return [{"system": "phone", "value": phone} for phone in phones]


def _stats_extension(d: dict):
    """Build organization stats extension."""
    revenue = grab(d, "revenue")
    utilization = grab(d, "utilization")

    if revenue is None and utilization is None:
        return None

    nested = []
    if revenue is not None:
        nested.append({"url": "revenue", "valueDecimal": float(revenue)})
    if utilization is not None:
        nested.append({"url": "utilization", "valueInteger": int(utilization)})

    return {
        "url": "http://synthea.mitre.org/fhir/StructureDefinition/organization-stats",
        "extension": nested,
    }


@mapper
def _to_fhir_organization(d: dict):
    """Core mapping from dict to FHIR Organization structure."""
    addr = _address(d)
    stats = _stats_extension(d)

    return {
        "resourceType": "Organization",
        "id": grab(d, "id"),
        "name": grab(d, "name"),
        "address": [addr] if addr else None,
        "telecom": _telecom(grab(d, "phone")),
        "extension": [stats] if stats else None,
    }


def convert(src: SyntheaOrganization) -> Organization:
    """Convert Synthea Organization to FHIR R4 Organization.

    Args:
        src: Synthea Organization model

    Returns:
        FHIR R4 Organization resource
    """
    return Organization(**_to_fhir_organization(to_dict(src)))
