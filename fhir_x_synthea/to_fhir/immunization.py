"""Synthea Immunization → FHIR R4 Immunization"""

from fhir.resources.immunization import Immunization
from synthea_pydantic import Immunization as SyntheaImmunization

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import codeable_concept, format_datetime, ref


def _immunization_id(d: dict) -> str:
    """Generate deterministic immunization ID."""
    patient_id = grab(d, "patient") or ""
    date = grab(d, "date") or ""
    code = grab(d, "code") or ""
    return f"{patient_id}-{date}-{code}".replace(" ", "-").replace(":", "-")


@mapper
def _to_fhir_immunization(
    d: dict,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
):
    """Core mapping from dict to FHIR Immunization structure."""
    patient_id = grab(d, "patient")
    encounter_id = grab(d, "encounter")
    base_cost = grab(d, "base_cost")

    # Build effective references
    eff_patient_ref = patient_ref or (f"Patient/{patient_id}" if patient_id else None)
    eff_encounter_ref = encounter_ref or (
        f"Encounter/{encounter_id}" if encounter_id else None
    )

    return {
        "resourceType": "Immunization",
        "id": _immunization_id(d),
        "status": "completed",
        "vaccineCode": codeable_concept(
            system="http://hl7.org/fhir/sid/cvx",
            code=grab(d, "code"),
            display=grab(d, "description"),
            text=grab(d, "description"),
        ),
        "patient": ref(
            "Patient", eff_patient_ref.split("/")[-1] if eff_patient_ref else None
        ),
        "encounter": ref(
            "Encounter", eff_encounter_ref.split("/")[-1] if eff_encounter_ref else None
        ),
        "occurrenceDateTime": grab(d, "date", apply=format_datetime),
        "extension": [
            {
                "url": "http://synthea.mitre.org/fhir/StructureDefinition/immunization-cost",
                "valueDecimal": float(base_cost),
            }
        ]
        if base_cost is not None
        else None,
    }


def convert(
    src: SyntheaImmunization,
    *,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
) -> Immunization:
    """Convert Synthea Immunization to FHIR R4 Immunization.

    Args:
        src: Synthea Immunization model
        patient_ref: Optional patient reference (e.g., "Patient/123")
        encounter_ref: Optional encounter reference (e.g., "Encounter/456")

    Returns:
        FHIR R4 Immunization resource
    """
    return Immunization(
        **_to_fhir_immunization(to_dict(src), patient_ref, encounter_ref)
    )
