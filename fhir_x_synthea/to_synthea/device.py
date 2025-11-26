"""
Mapping function for converting FHIR Device resources to Synthea devices.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_extension_period,
    extract_extension_reference,
    extract_reference_id,
    parse_datetime,
)


def map_fhir_device_to_csv(fhir_resource: dict[str, Any]) -> dict[str, Any]:
    """
    Map a FHIR R4 Device resource to a Synthea devices.csv row.

    Args:
        fhir_resource: Dictionary representing a FHIR Device resource

    Returns:
        Dictionary with CSV column names as keys (START, STOP, PATIENT, etc.)
    """

    # Initialize CSV row
    csv_row: dict[str, str] = {
        "START": "",
        "STOP": "",
        "PATIENT": "",
        "ENCOUNTER": "",
        "CODE": "",
        "DESCRIPTION": "",
        "UDI": "",
    }

    # Extract START and STOP from device-use-period extension
    device_period = extract_extension_period(
        fhir_resource, "http://synthea.tools/fhir/StructureDefinition/device-use-period"
    )

    if device_period:
        start = device_period.get("start")
        if start:
            csv_row["START"] = parse_datetime(start)

        stop = device_period.get("end")
        if stop:
            csv_row["STOP"] = parse_datetime(stop)

    # Extract PATIENT reference
    patient = fhir_resource.get("patient")
    if patient:
        csv_row["PATIENT"] = extract_reference_id(patient)

    # Extract ENCOUNTER from extension
    csv_row["ENCOUNTER"] = extract_extension_reference(
        fhir_resource, "http://hl7.org/fhir/StructureDefinition/resource-encounter"
    )

    # Extract CODE and DESCRIPTION from type
    device_type = fhir_resource.get("type")
    if device_type:
        csv_row["CODE"] = extract_coding_code(device_type, "http://snomed.info/sct")
        csv_row["DESCRIPTION"] = extract_display_or_text(device_type)

    # Extract UDI (prefer deviceIdentifier, fallback to carrierHRF)
    udi_carriers = fhir_resource.get("udiCarrier", [])
    if udi_carriers:
        first_udi = udi_carriers[0]
        device_identifier = first_udi.get("deviceIdentifier", "")
        carrier_hrf = first_udi.get("carrierHRF", "")
        if device_identifier:
            csv_row["UDI"] = device_identifier
        elif carrier_hrf:
            csv_row["UDI"] = carrier_hrf

    return csv_row
