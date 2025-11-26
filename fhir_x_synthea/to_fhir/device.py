"""Synthea Device → FHIR R4 Device"""

from typing import Any

from fhir.resources.device import Device
from synthea_pydantic import Device as SyntheaDevice

from ..fhir_lib import format_datetime
from ..utils import to_str


def convert(
    src: SyntheaDevice,
    *,
    patient_ref: str | None = None,
) -> Device:
    """Convert Synthea Device to FHIR R4 Device.

    Args:
        src: Synthea Device model
        patient_ref: Optional patient reference (e.g., "Patient/123")

    Returns:
        FHIR R4 Device resource
    """
    d = src.model_dump()

    # Extract fields
    start = to_str(d.get("start"))
    stop = to_str(d.get("stop"))
    patient_id = to_str(d.get("patient"))
    encounter_id = to_str(d.get("encounter"))
    code = to_str(d.get("code"))
    description = to_str(d.get("description"))
    udi = to_str(d.get("udi"))

    # Determine status
    status = "active" if not stop else "inactive"

    # Generate resource ID
    resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")

    # Build resource
    resource: dict[str, Any] = {
        "resourceType": "Device",
        "id": resource_id,
        "status": status,
    }

    # Extensions
    extensions = []

    # Set device-use-period extension
    if start or stop:
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
            extensions.append(
                {
                    "url": "http://synthea.tools/fhir/StructureDefinition/device-use-period",
                    "valuePeriod": device_period,
                }
            )

    # Set encounter reference via extension
    if encounter_id:
        extensions.append(
            {
                "url": "http://hl7.org/fhir/StructureDefinition/resource-encounter",
                "valueReference": {"reference": f"Encounter/{encounter_id}"},
            }
        )

    # Set patient reference via extension (Device doesn't have direct patient in R4B)
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )
    if effective_patient_ref:
        extensions.append(
            {
                "url": "http://hl7.org/fhir/StructureDefinition/resource-patient",
                "valueReference": {"reference": effective_patient_ref},
            }
        )

    if extensions:
        resource["extension"] = extensions

    # Set type (SNOMED CT)
    if code or description:
        type_obj: dict[str, Any] = {}
        if code:
            type_obj["coding"] = [
                {
                    "system": "http://snomed.info/sct",
                    "code": code,
                    "display": description or None,
                }
            ]
        if description:
            type_obj["text"] = description
        resource["type"] = [type_obj]

    # Set UDI
    if udi:
        resource["udiCarrier"] = [{"deviceIdentifier": udi, "carrierHRF": udi}]

    return Device(**resource)
