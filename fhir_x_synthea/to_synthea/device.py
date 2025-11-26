"""FHIR R4 Device → Synthea Device"""

import logging
from datetime import date

from fhir.resources.device import Device
from synthea_pydantic import Device as SyntheaDevice

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_extension_period,
    extract_extension_reference,
    parse_datetime_to_date,
)

logger = logging.getLogger(__name__)


def convert(src: Device) -> SyntheaDevice:
    """Convert FHIR R4 Device to Synthea Device.

    Args:
        src: FHIR R4 Device resource

    Returns:
        Synthea Device model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract START and STOP from device-use-period extension
    start = None
    stop = None
    device_period = extract_extension_period(
        fhir_resource, "http://synthea.tools/fhir/StructureDefinition/device-use-period"
    )

    if device_period:
        start_str = device_period.get("start")
        if start_str:
            parsed = parse_datetime_to_date(start_str)
            if parsed:
                start = date.fromisoformat(parsed)

        stop_str = device_period.get("end")
        if stop_str:
            parsed = parse_datetime_to_date(stop_str)
            if parsed:
                stop = date.fromisoformat(parsed)

    # Extract PATIENT from extension
    patient = extract_extension_reference(
        fhir_resource, "http://hl7.org/fhir/StructureDefinition/resource-patient"
    )

    # Extract ENCOUNTER from extension
    encounter = extract_extension_reference(
        fhir_resource, "http://hl7.org/fhir/StructureDefinition/resource-encounter"
    )

    # Extract CODE and DESCRIPTION from type
    # R4B Device.type is a list of CodeableConcept
    code = ""
    description = ""
    device_type = fhir_resource.get("type")
    if device_type:
        # Handle list (R4B) or single (R4)
        if isinstance(device_type, list) and device_type:
            first_type = device_type[0]
            code = extract_coding_code(
                first_type, preferred_system="http://snomed.info/sct"
            )
            description = extract_display_or_text(first_type)
        elif isinstance(device_type, dict):
            code = extract_coding_code(
                device_type, preferred_system="http://snomed.info/sct"
            )
            description = extract_display_or_text(device_type)

    # Extract UDI (prefer deviceIdentifier, fallback to carrierHRF)
    udi = ""
    udi_carriers = fhir_resource.get("udiCarrier", [])
    if udi_carriers:
        first_udi = udi_carriers[0]
        device_identifier = first_udi.get("deviceIdentifier", "")
        carrier_hrf = first_udi.get("carrierHRF", "")
        if device_identifier:
            udi = device_identifier
        elif carrier_hrf:
            udi = carrier_hrf

    return SyntheaDevice(
        start=start,
        stop=stop,
        patient=patient or None,
        encounter=encounter or None,
        code=code or "unknown",
        description=description or "Unknown device",
        udi=udi or None,
    )
