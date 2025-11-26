"""FHIR R4 Organization → Synthea Organization"""

import logging
from decimal import Decimal
from typing import Any

from fhir.resources.organization import Organization
from synthea_pydantic import Organization as SyntheaOrganization

from ..synthea_csv_lib import extract_nested_extension

logger = logging.getLogger(__name__)


def _extract_geolocation(
    address: dict[str, Any] | None,
) -> tuple[Decimal | None, Decimal | None]:
    """Extract lat/lon from address extension."""
    if not address:
        return (None, None)

    extensions = address.get("extension", [])
    for ext in extensions:
        if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/geolocation":
            sub_extensions = ext.get("extension", [])
            lat = None
            lon = None
            for sub_ext in sub_extensions:
                url = sub_ext.get("url", "")
                value = sub_ext.get("valueDecimal")
                if value is not None:
                    if url == "latitude":
                        lat = Decimal(str(value))
                    elif url == "longitude":
                        lon = Decimal(str(value))
            return (lat, lon)
    return (None, None)


def convert(src: Organization) -> SyntheaOrganization:
    """Convert FHIR R4 Organization to Synthea Organization.

    Args:
        src: FHIR R4 Organization resource

    Returns:
        Synthea Organization model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract Id
    resource_id = fhir_resource.get("id", "")

    # Extract Name
    name = fhir_resource.get("name", "")

    # Extract Address components
    address = ""
    city = ""
    state = ""
    zip_code = ""
    lat = None
    lon = None

    addresses = fhir_resource.get("address", [])
    if addresses:
        first_address = addresses[0]

        # Address line
        lines = first_address.get("line", [])
        if lines:
            address = lines[0]

        city = first_address.get("city", "")
        state = first_address.get("state", "")
        zip_code = first_address.get("postalCode", "")

        # Geolocation
        lat, lon = _extract_geolocation(first_address)

    # Extract Phone numbers (join with ; )
    telecom = fhir_resource.get("telecom", [])
    phones = []
    for contact in telecom:
        if contact.get("system") == "phone":
            value = contact.get("value", "")
            if value:
                phones.append(value)

    phone = "; ".join(phones) if phones else ""

    # Extract organization stats extensions
    revenue_str = extract_nested_extension(
        fhir_resource,
        "http://synthea.mitre.org/fhir/StructureDefinition/organization-stats",
        "revenue",
        "valueDecimal",
    )
    utilization_str = extract_nested_extension(
        fhir_resource,
        "http://synthea.mitre.org/fhir/StructureDefinition/organization-stats",
        "utilization",
        "valueInteger",
    )

    revenue = Decimal(revenue_str) if revenue_str else None
    utilization = int(utilization_str) if utilization_str else None

    # Log lossy conversions
    if len(addresses) > 1:
        logger.warning(
            "Organization %s has %d addresses; only first preserved",
            src.id,
            len(addresses),
        )

    return SyntheaOrganization(
        id=resource_id or None,
        name=name or "Unknown Organization",
        address=address or None,
        city=city or None,
        state=state or None,
        zip=zip_code or None,
        lat=lat,
        lon=lon,
        phone=phone or None,
        revenue=revenue,
        utilization=utilization,
    )
