"""Synthea Immunization → FHIR R4 Immunization"""

from typing import Any

from fhir.resources.immunization import Immunization
from synthea_pydantic import Immunization as SyntheaImmunization

from ..fhir_lib import format_datetime
from ..utils import to_str


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
    d = src.model_dump()

    # Extract fields
    date = to_str(d.get("date"))
    patient_id = to_str(d.get("patient"))
    encounter_id = to_str(d.get("encounter"))
    code = to_str(d.get("code"))
    description = to_str(d.get("description"))
    base_cost = d.get("base_cost")

    # Generate resource ID
    resource_id = f"{patient_id}-{date}-{code}".replace(" ", "-").replace(":", "-")

    # Build resource
    resource: dict[str, Any] = {
        "resourceType": "Immunization",
        "id": resource_id,
        "status": "completed",
    }

    # Set occurrence
    if date:
        iso_date = format_datetime(date)
        if iso_date:
            resource["occurrenceDateTime"] = iso_date

    # Set patient reference
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )
    if effective_patient_ref:
        resource["patient"] = {"reference": effective_patient_ref}

    # Set encounter reference
    effective_encounter_ref = encounter_ref or (
        f"Encounter/{encounter_id}" if encounter_id else None
    )
    if effective_encounter_ref:
        resource["encounter"] = {"reference": effective_encounter_ref}

    # Set vaccineCode (CVX)
    if code or description:
        vaccine_code: dict[str, Any] = {}
        if code:
            vaccine_code["coding"] = [
                {
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": code,
                    "display": description or None,
                }
            ]
        if description:
            vaccine_code["text"] = description
        resource["vaccineCode"] = vaccine_code

    # Set cost extension
    if base_cost is not None:
        resource["extension"] = [
            {
                "url": "http://synthea.mitre.org/fhir/StructureDefinition/immunization-cost",
                "valueDecimal": float(base_cost),
            }
        ]

    return Immunization(**resource)
