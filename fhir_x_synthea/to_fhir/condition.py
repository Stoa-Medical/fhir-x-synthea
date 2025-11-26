"""Synthea Condition → FHIR R4 Condition"""

from fhir.resources.condition import Condition
from synthea_pydantic import Condition as SyntheaCondition

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import (
    clinical_status,
    codeable_concept,
    format_datetime,
    ref,
    verification_status,
)


def _condition_id(d: dict) -> str:
    """Generate deterministic condition ID from patient+start+code."""
    patient_id = grab(d, "patient") or ""
    start = grab(d, "start") or ""
    code = grab(d, "code") or ""
    return f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")


@mapper
def _to_fhir_condition(
    d: dict,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
):
    """Core mapping from dict to FHIR Condition structure."""
    patient_id = grab(d, "patient")
    encounter_id = grab(d, "encounter")
    stop = grab(d, "stop")

    # Use override refs or build from source IDs
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )
    effective_encounter_ref = encounter_ref or (
        f"Encounter/{encounter_id}" if encounter_id else None
    )

    return {
        "resourceType": "Condition",
        "id": _condition_id(d),
        "clinicalStatus": clinical_status(
            is_active=not stop,
            system="http://terminology.hl7.org/CodeSystem/condition-clinical",
        ),
        "verificationStatus": verification_status(
            code="confirmed",
            system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
        ),
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
        "code": codeable_concept(
            system="http://snomed.info/sct",
            code=grab(d, "code"),
            display=grab(d, "description"),
            text=grab(d, "description"),
        ),
        "subject": ref(
            "Patient",
            effective_patient_ref.split("/")[-1] if effective_patient_ref else None,
        ),
        "encounter": ref(
            "Encounter",
            effective_encounter_ref.split("/")[-1] if effective_encounter_ref else None,
        ),
        "onsetDateTime": grab(d, "start", apply=format_datetime),
        "abatementDateTime": grab(d, "stop", apply=format_datetime),
    }


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
    return Condition(**_to_fhir_condition(to_dict(src), patient_ref, encounter_ref))
