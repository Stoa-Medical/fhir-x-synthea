"""Synthea CarePlan → FHIR R4 CarePlan"""

from typing import Any

from fhir.resources.careplan import CarePlan
from synthea_pydantic import CarePlan as SyntheaCarePlan

from ..fhir_lib import format_datetime
from ..utils import to_str


def convert(
    src: SyntheaCarePlan,
    *,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
) -> CarePlan:
    """Convert Synthea CarePlan to FHIR R4 CarePlan.

    Args:
        src: Synthea CarePlan model
        patient_ref: Optional patient reference (e.g., "Patient/123")
        encounter_ref: Optional encounter reference (e.g., "Encounter/456")

    Returns:
        FHIR R4 CarePlan resource
    """
    d = src.model_dump()

    # Extract fields
    careplan_id = to_str(d.get("id"))
    start = to_str(d.get("start"))
    stop = to_str(d.get("stop"))
    patient_id = to_str(d.get("patient"))
    encounter_id = to_str(d.get("encounter"))
    code = to_str(d.get("code"))
    description = to_str(d.get("description"))
    reason_code = to_str(d.get("reasoncode"))
    reason_description = to_str(d.get("reasondescription"))

    # Determine status
    status = "active" if not stop else "completed"

    # Generate resource ID
    resource_id = careplan_id or f"{patient_id}-{start}-{code}".replace(
        " ", "-"
    ).replace(":", "-")

    # Build resource
    resource: dict[str, Any] = {
        "resourceType": "CarePlan",
        "status": status,
        "intent": "plan",
    }

    if resource_id:
        resource["id"] = resource_id

    # Set period
    period: dict[str, Any] = {}
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            period["start"] = iso_start
    if stop:
        iso_stop = format_datetime(stop)
        if iso_stop:
            period["end"] = iso_stop
    if period:
        resource["period"] = period

    # Set subject reference
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )
    if effective_patient_ref:
        resource["subject"] = {"reference": effective_patient_ref}

    # Set encounter reference
    effective_encounter_ref = encounter_ref or (
        f"Encounter/{encounter_id}" if encounter_id else None
    )
    if effective_encounter_ref:
        resource["encounter"] = {"reference": effective_encounter_ref}

    # Set category
    if code:
        resource["category"] = [
            {"coding": [{"system": "http://snomed.info/sct", "code": code}]}
        ]

    # Set description and title
    if description:
        resource["description"] = description
        resource["title"] = description

    # Set addresses (reason) - R4B uses addresses instead of reasonCode
    if reason_code or reason_description:
        addresses_obj: dict[str, Any] = {}
        if reason_code:
            coding = {"system": "http://snomed.info/sct", "code": reason_code}
            if reason_description:
                coding["display"] = reason_description
            addresses_obj["coding"] = [coding]
        if reason_description:
            addresses_obj["text"] = reason_description
        resource["addresses"] = [{"concept": addresses_obj}]

    return CarePlan(**resource)
