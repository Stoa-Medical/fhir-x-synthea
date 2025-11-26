"""
Mapping function for converting Synthea devices.csv rows to FHIR Device resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime


def map_device(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea devices.csv row to a FHIR R4 Device resource.

    Args:
        csv_row: Dictionary with keys like START, STOP, PATIENT, ENCOUNTER, CODE, DESCRIPTION, UDI

    Returns:
        Dictionary representing a FHIR Device resource
    """

    # Extract and process fields
    start = csv_row.get("START", "").strip() if csv_row.get("START") else ""
    stop = csv_row.get("STOP", "").strip() if csv_row.get("STOP") else ""
    patient_id = csv_row.get("PATIENT", "").strip() if csv_row.get("PATIENT") else ""
    encounter_id = (
        csv_row.get("ENCOUNTER", "").strip() if csv_row.get("ENCOUNTER") else ""
    )
    code = csv_row.get("CODE", "").strip() if csv_row.get("CODE") else ""
    description = (
        csv_row.get("DESCRIPTION", "").strip() if csv_row.get("DESCRIPTION") else ""
    )
    udi = csv_row.get("UDI", "").strip() if csv_row.get("UDI") else ""

    # Determine status based on STOP field
    status = "active" if (not stop or stop == "") else "inactive"

    # Generate resource ID from PATIENT+START+CODE
    resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Device",
        "id": resource_id,
        "status": status,
    }

    # Set patient reference (required)
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["patient"] = patient_ref

    # Set device-use-period extension
    device_period: dict[str, Any] = {}
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            device_period["start"] = iso_start
    if stop:
        iso_stop = format_datetime(stop)
        if iso_stop:
            device_period["end"] = iso_stop

    if device_period:
        resource.setdefault("extension", []).append(
            {
                "url": "http://synthea.tools/fhir/StructureDefinition/device-use-period",
                "valuePeriod": device_period,
            }
        )

    # Set encounter reference via extension
    if encounter_id:
        encounter_ref = create_reference("Encounter", encounter_id)
        if encounter_ref:
            resource.setdefault("extension", []).append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/resource-encounter",
                    "valueReference": encounter_ref,
                }
            )

    # Set type (SNOMED CT)
    if code or description:
        type_obj: dict[str, Any] = {}
        if code:
            coding = {"system": "http://snomed.info/sct", "code": code}
            if description:
                coding["display"] = description
            type_obj["coding"] = [coding]
        if description:
            type_obj["text"] = description
        if type_obj:
            resource["type"] = type_obj

    # Set UDI
    if udi:
        resource["udiCarrier"] = [{"deviceIdentifier": udi, "carrierHRF": udi}]

    return resource
