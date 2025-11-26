"""Synthea Observation → FHIR R4 Observation"""

from typing import Any

from fhir.resources.observation import Observation
from synthea_pydantic import Observation as SyntheaObservation

from ..fhir_lib import format_datetime
from ..utils import to_str


def _normalize_category(category_type: str) -> dict[str, Any] | None:
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
    if mapping:
        return {
            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
            **mapping,
        }
    return None


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
    d = src.model_dump()

    # Extract fields
    date = to_str(d.get("date"))
    patient_id = to_str(d.get("patient"))
    encounter_id = to_str(d.get("encounter"))
    code = to_str(d.get("code"))
    description = to_str(d.get("description"))
    value = d.get("value")
    units = to_str(d.get("units"))
    category_type = to_str(d.get("type"))

    # Generate resource ID
    resource_id = f"{patient_id}-{date}-{code}".replace(" ", "-").replace(":", "-")

    # Build resource
    resource: dict[str, Any] = {
        "resourceType": "Observation",
        "id": resource_id,
        "status": "final",
    }

    # Set effectiveDateTime
    if date:
        iso_date = format_datetime(date)
        if iso_date:
            resource["effectiveDateTime"] = iso_date

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

    # Set code (LOINC)
    if code or description:
        code_obj: dict[str, Any] = {}
        if code:
            code_obj["coding"] = [
                {
                    "system": "http://loinc.org",
                    "code": code,
                    "display": description or None,
                }
            ]
        if description:
            code_obj["text"] = description
        resource["code"] = code_obj

    # Set category
    category_coding = _normalize_category(category_type)
    if category_coding:
        resource["category"] = [{"coding": [category_coding]}]

    # Set value
    if value is not None:
        value_str = str(value)
        try:
            numeric_value = float(value_str)
            quantity: dict[str, Any] = {"value": numeric_value}
            if units:
                quantity["unit"] = units
                quantity["code"] = units
                quantity["system"] = "http://unitsofmeasure.org"
            resource["valueQuantity"] = quantity
        except (ValueError, TypeError):
            value_lower = value_str.lower()
            if value_lower in ("true", "false"):
                resource["valueBoolean"] = value_lower == "true"
            else:
                resource["valueString"] = value_str

    return Observation(**resource)
