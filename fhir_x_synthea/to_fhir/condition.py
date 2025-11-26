"""Synthea Condition → FHIR R4 Condition"""

from typing import Any

from fhir.resources.condition import Condition
from synthea_pydantic import Condition as SyntheaCondition

from ..fhir_lib import (
    create_clinical_status_coding,
    format_datetime,
)
from ..utils import to_str


def convert(
    src: SyntheaCondition,
    *,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
) -> Condition:
    """Convert Synthea Condition to FHIR R4 Condition.

    Args:
        src: Synthea Condition model
        patient_ref: Optional patient reference (e.g., "Patient/123")
        encounter_ref: Optional encounter reference (e.g., "Encounter/456")

    Returns:
        FHIR R4 Condition resource
    """
    d = src.model_dump()

    # Extract and process fields (synthea_pydantic uses lowercase keys)
    start = to_str(d.get("start"))
    stop = to_str(d.get("stop"))
    patient_id = to_str(d.get("patient"))
    encounter_id = to_str(d.get("encounter"))
    code = to_str(d.get("code"))
    description = to_str(d.get("description"))

    # Determine clinical status based on stop field
    is_active = not stop
    clinical_status = create_clinical_status_coding(
        is_active, "http://terminology.hl7.org/CodeSystem/condition-clinical"
    )

    # Generate resource ID from patient+start+code
    resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Condition",
        "id": resource_id,
        "clinicalStatus": clinical_status,
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                    "display": "Confirmed",
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "encounter-diagnosis",
                        "display": "Encounter Diagnosis",
                    }
                ]
            }
        ],
    }

    # Set onsetDateTime from start
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            resource["onsetDateTime"] = iso_start

    # Set abatementDateTime from stop if present
    if stop:
        iso_stop = format_datetime(stop)
        if iso_stop:
            resource["abatementDateTime"] = iso_stop

    # Set subject (patient) reference - use override or from source
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )
    if effective_patient_ref:
        resource["subject"] = {"reference": effective_patient_ref}

    # Set encounter reference - use override or from source
    effective_encounter_ref = encounter_ref or (
        f"Encounter/{encounter_id}" if encounter_id else None
    )
    if effective_encounter_ref:
        resource["encounter"] = {"reference": effective_encounter_ref}

    # Set code (SNOMED CT)
    if code or description:
        code_obj: dict[str, Any] = {}
        if code:
            coding = {"system": "http://snomed.info/sct", "code": code}
            if description:
                coding["display"] = description
            code_obj["coding"] = [coding]
        if description:
            code_obj["text"] = description
        if code_obj:
            resource["code"] = code_obj

    return Condition(**resource)
