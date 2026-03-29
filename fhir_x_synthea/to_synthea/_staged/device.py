"""FHIR R4 Device → Synthea Device"""

import logging
from datetime import date

from fhir.resources.device import Device
from synthea_pydantic import Device as SyntheaDevice

from ..chidian_ext import (
    extract_code,
    extract_display,
    extract_ext_ref,
    grab,
    mapper,
    parse_date,
    to_dict,
)

logger = logging.getLogger(__name__)


def _extract_period_extension(d: dict):
    """Extract start and stop from device-use-period extension."""
    extensions = grab(d, "extension") or []
    for ext in extensions:
        if (
            ext.get("url")
            == "http://synthea.tools/fhir/StructureDefinition/device-use-period"
        ):
            value_period = ext.get("valuePeriod", {})
            return value_period.get("start"), value_period.get("end")
    return None, None


def _extract_device_type(d: dict) -> tuple[str, str]:
    """Extract code and description from type (list in R4B, dict in R4)."""
    device_type = grab(d, "type")
    if not device_type:
        return "", ""

    # Handle list (R4B) or single (R4)
    if isinstance(device_type, list) and device_type:
        first_type = device_type[0]
        code = extract_code({"t": first_type}, "t", system="http://snomed.info/sct")
        desc = extract_display({"t": first_type}, "t")
        return code, desc
    elif isinstance(device_type, dict):
        code = extract_code({"t": device_type}, "t", system="http://snomed.info/sct")
        desc = extract_display({"t": device_type}, "t")
        return code, desc

    return "", ""


def _extract_udi(d: dict) -> str:
    """Extract UDI from udiCarrier."""
    udi_carriers = grab(d, "udiCarrier") or []
    if udi_carriers:
        first_udi = udi_carriers[0]
        return first_udi.get("deviceIdentifier", "") or first_udi.get("carrierHRF", "")
    return ""


@mapper(remove_empty=False)
def _to_synthea_device(d: dict):
    """Core mapping from dict to Synthea Device structure."""
    # Extract period from extension
    start_str, stop_str = _extract_period_extension(d)

    start = None
    if start_str:
        parsed = parse_date({"dt": start_str}, "dt")
        if parsed:
            start = date.fromisoformat(parsed)

    stop = None
    if stop_str:
        parsed = parse_date({"dt": stop_str}, "dt")
        if parsed:
            stop = date.fromisoformat(parsed)

    # Extract patient and encounter from extensions
    patient = extract_ext_ref(
        d, "http://hl7.org/fhir/StructureDefinition/resource-patient"
    )
    encounter = extract_ext_ref(
        d, "http://hl7.org/fhir/StructureDefinition/resource-encounter"
    )

    # Extract type
    code, description = _extract_device_type(d)

    return {
        "start": start,
        "stop": stop,
        "patient": patient or None,
        "encounter": encounter or None,
        "code": code or "unknown",
        "description": description or "Unknown device",
        "udi": _extract_udi(d) or None,
    }


def convert(src: Device) -> SyntheaDevice:
    """Convert FHIR R4 Device to Synthea Device.

    Args:
        src: FHIR R4 Device resource

    Returns:
        Synthea Device model
    """
    return SyntheaDevice(**_to_synthea_device(to_dict(src)))
