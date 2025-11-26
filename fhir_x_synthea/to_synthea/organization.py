"""FHIR R4 Organization → Synthea Organization"""

import logging
from decimal import Decimal

from fhir.resources.organization import Organization
from synthea_pydantic import Organization as SyntheaOrganization

from ..chidian_ext import extract_nested_ext, grab, mapper, to_dict
from ..synthea_lib import to_decimal

logger = logging.getLogger(__name__)


def _extract_geolocation(address: dict | None) -> tuple[Decimal | None, Decimal | None]:
    """Extract lat/lon from address extension."""
    if not address:
        return None, None

    extensions = address.get("extension", [])
    for ext in extensions:
        if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/geolocation":
            lat, lon = None, None
            for sub_ext in ext.get("extension", []):
                value = sub_ext.get("valueDecimal")
                if value is not None:
                    if sub_ext.get("url") == "latitude":
                        lat = Decimal(str(value))
                    elif sub_ext.get("url") == "longitude":
                        lon = Decimal(str(value))
            return lat, lon
    return None, None


def _extract_phones(d: dict) -> str:
    """Extract phone numbers and join with semicolon."""
    telecoms = grab(d, "telecom") or []
    phones = [
        contact.get("value", "")
        for contact in telecoms
        if contact.get("system") == "phone" and contact.get("value")
    ]
    return "; ".join(phones)


@mapper(remove_empty=False)
def _to_synthea_organization(d: dict):
    """Core mapping from dict to Synthea Organization structure."""
    addresses = grab(d, "address") or []
    first_address = addresses[0] if addresses else {}

    lines = first_address.get("line", [])
    address = lines[0] if lines else ""

    lat, lon = _extract_geolocation(first_address)

    # Extract stats from extension
    stats_url = "http://synthea.mitre.org/fhir/StructureDefinition/organization-stats"
    revenue_str = extract_nested_ext(d, stats_url, "revenue", "valueDecimal", "")
    utilization_str = extract_nested_ext(
        d, stats_url, "utilization", "valueInteger", ""
    )

    # Log lossy conversions
    if len(addresses) > 1:
        logger.warning(
            "Organization has %d addresses; only first preserved", len(addresses)
        )

    return {
        "id": grab(d, "id") or None,
        "name": grab(d, "name") or "Unknown Organization",
        "address": address or None,
        "city": first_address.get("city") or None,
        "state": first_address.get("state") or None,
        "zip": first_address.get("postalCode") or None,
        "lat": lat,
        "lon": lon,
        "phone": _extract_phones(d) or None,
        "revenue": to_decimal(revenue_str) if revenue_str else None,
        "utilization": int(utilization_str) if utilization_str else None,
    }


def convert(src: Organization) -> SyntheaOrganization:
    """Convert FHIR R4 Organization to Synthea Organization.

    Args:
        src: FHIR R4 Organization resource

    Returns:
        Synthea Organization model
    """
    return SyntheaOrganization(**_to_synthea_organization(to_dict(src)))
