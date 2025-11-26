"""Synthea Procedure → FHIR R4 Procedure"""

from typing import Any

from fhir.resources.procedure import Procedure
from synthea_pydantic import Procedure as SyntheaProcedure

from ..fhir_lib import format_datetime
from ..utils import to_str


def convert(
    src: SyntheaProcedure,
    *,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
) -> Procedure:
    """Convert Synthea Procedure to FHIR R4 Procedure.

    Args:
        src: Synthea Procedure model
        patient_ref: Optional patient reference (e.g., "Patient/123")
        encounter_ref: Optional encounter reference (e.g., "Encounter/456")

    Returns:
        FHIR R4 Procedure resource
    """
    d = src.model_dump()

    # Extract fields
    start = to_str(d.get("start"))
    stop = to_str(d.get("stop"))
    patient_id = to_str(d.get("patient"))
    encounter_id = to_str(d.get("encounter"))
    code = to_str(d.get("code"))
    description = to_str(d.get("description"))
    base_cost = d.get("base_cost")
    reason_code = to_str(d.get("reasoncode"))
    reason_description = to_str(d.get("reasondescription"))

    # Generate resource ID
    resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Procedure",
        "id": resource_id,
        "status": "completed",
    }

    # Set performed period or datetime
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            if stop:
                iso_stop = format_datetime(stop)
                if iso_stop:
                    resource["occurrencePeriod"] = {"start": iso_start, "end": iso_stop}
                else:
                    resource["occurrenceDateTime"] = iso_start
            else:
                resource["occurrenceDateTime"] = iso_start

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

    # Set code
    if code or description:
        code_obj: dict[str, Any] = {}
        if code:
            code_obj["coding"] = [
                {
                    "system": "http://snomed.info/sct",
                    "code": code,
                    "display": description or None,
                }
            ]
        if description:
            code_obj["text"] = description
        resource["code"] = code_obj

    # Set reason (R4B uses reason with CodeableReference)
    if reason_code or reason_description:
        concept: dict[str, Any] = {}
        if reason_code:
            concept["coding"] = [
                {
                    "system": "http://snomed.info/sct",
                    "code": reason_code,
                    "display": reason_description or None,
                }
            ]
        if reason_description:
            concept["text"] = reason_description
        resource["reason"] = [{"concept": concept}]

    # Set cost extension
    if base_cost is not None:
        resource["extension"] = [
            {
                "url": "http://example.org/fhir/StructureDefinition/baseCost",
                "valueMoney": {"value": float(base_cost), "currency": "USD"},
            }
        ]

    return Procedure(**resource)
