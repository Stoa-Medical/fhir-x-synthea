"""Synthea Observation → FHIR R4 Observation"""

from typing import Any

from fhir.resources.observation import Observation
from synthea_pydantic import Observation as SyntheaObservation

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import codeable_concept, format_datetime, ref


def _observation_id(d: dict) -> str:
    """Generate deterministic observation ID."""
    patient_id = grab(d, "patient") or ""
    date = grab(d, "date") or ""
    code = grab(d, "code") or ""
    return f"{patient_id}-{date}-{code}".replace(" ", "-").replace(":", "-")


def _category(category_type: str | None):
    """Map Synthea observation type to FHIR category."""
    if not category_type:
        return None

    category_map = {
        "vital-signs": {"code": "vital-signs", "display": "Vital Signs"},
        "laboratory": {"code": "laboratory", "display": "Laboratory"},
        "survey": {"code": "survey", "display": "Survey"},
        "social-history": {"code": "social-history", "display": "Social History"},
        "imaging": {"code": "imaging", "display": "Imaging"},
        "procedure": {"code": "procedure", "display": "Procedure"},
    }

    mapping = category_map.get(category_type.lower().strip())
    if not mapping:
        return None

    return [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    **mapping,
                }
            ]
        }
    ]


def _value(value: Any, units: str | None):
    """Build observation value (Quantity, Boolean, or String)."""
    if value is None:
        return {}

    value_str = str(value)

    # Try numeric
    try:
        numeric_value = float(value_str)
        quantity: dict[str, Any] = {"value": numeric_value}
        if units:
            quantity["unit"] = units
            quantity["code"] = units
            quantity["system"] = "http://unitsofmeasure.org"
        return {"valueQuantity": quantity}
    except (ValueError, TypeError):
        pass

    # Try boolean
    value_lower = value_str.lower()
    if value_lower in ("true", "false"):
        return {"valueBoolean": value_lower == "true"}

    # Default to string
    return {"valueString": value_str}


@mapper
def _to_fhir_observation(
    d: dict,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
):
    """Core mapping from dict to FHIR Observation structure."""
    patient_id = grab(d, "patient")
    encounter_id = grab(d, "encounter")

    # Build effective references
    eff_patient_ref = patient_ref or (f"Patient/{patient_id}" if patient_id else None)
    eff_encounter_ref = encounter_ref or (
        f"Encounter/{encounter_id}" if encounter_id else None
    )

    # Build value
    value_dict = _value(grab(d, "value"), grab(d, "units"))

    return {
        "resourceType": "Observation",
        "id": _observation_id(d),
        "status": "final",
        "code": codeable_concept(
            system="http://loinc.org",
            code=grab(d, "code"),
            display=grab(d, "description"),
            text=grab(d, "description"),
        ),
        "category": _category(grab(d, "type")),
        "subject": ref(
            "Patient", eff_patient_ref.split("/")[-1] if eff_patient_ref else None
        ),
        "encounter": ref(
            "Encounter", eff_encounter_ref.split("/")[-1] if eff_encounter_ref else None
        ),
        "effectiveDateTime": grab(d, "date", apply=format_datetime),
        **value_dict,
    }


def convert(
    src: SyntheaObservation,
    *,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
) -> Observation:
    """Convert Synthea Observation to FHIR R4 Observation.

    Args:
        src: Synthea Observation model
        patient_ref: Optional patient reference (e.g., "Patient/123")
        encounter_ref: Optional encounter reference (e.g., "Encounter/456")

    Returns:
        FHIR R4 Observation resource
    """
    return Observation(**_to_fhir_observation(to_dict(src), patient_ref, encounter_ref))
