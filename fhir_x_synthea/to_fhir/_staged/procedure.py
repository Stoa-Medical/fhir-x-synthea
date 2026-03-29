"""Synthea Procedure → FHIR R4 Procedure"""

from fhir.resources.procedure import Procedure
from synthea_pydantic import Procedure as SyntheaProcedure

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import codeable_concept, format_datetime, ref


def _procedure_id(d: dict) -> str:
    """Generate deterministic procedure ID."""
    patient_id = grab(d, "patient") or ""
    start = grab(d, "start") or ""
    code = grab(d, "code") or ""
    return f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")


def _occurrence(start: str | None, stop: str | None):
    """Build occurrence (period or datetime)."""
    iso_start = format_datetime(start) if start else None
    iso_stop = format_datetime(stop) if stop else None

    if iso_start and iso_stop:
        return {"period": {"start": iso_start, "end": iso_stop}}
    elif iso_start:
        return {"datetime": iso_start}
    return None


def _reason(reason_code: str | None, reason_desc: str | None) -> list | None:
    """Build procedure reason (CodeableReference)."""
    if not reason_code and not reason_desc:
        return None

    concept: dict = {}
    if reason_code:
        coding = {"system": "http://snomed.info/sct", "code": reason_code}
        if reason_desc:
            coding["display"] = reason_desc
        concept["coding"] = [coding]
    if reason_desc:
        concept["text"] = reason_desc

    return [{"concept": concept}] if concept else None


@mapper
def _to_fhir_procedure(
    d: dict,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
):
    """Core mapping from dict to FHIR Procedure structure."""
    patient_id = grab(d, "patient")
    encounter_id = grab(d, "encounter")
    start = grab(d, "start")
    stop = grab(d, "stop")
    base_cost = grab(d, "base_cost")

    # Build effective references
    eff_patient_ref = patient_ref or (f"Patient/{patient_id}" if patient_id else None)
    eff_encounter_ref = encounter_ref or (
        f"Encounter/{encounter_id}" if encounter_id else None
    )

    # Build occurrence
    occ = _occurrence(start, stop)

    return {
        "resourceType": "Procedure",
        "id": _procedure_id(d),
        "status": "completed",
        "code": codeable_concept(
            system="http://snomed.info/sct",
            code=grab(d, "code"),
            display=grab(d, "description"),
            text=grab(d, "description"),
        ),
        "subject": ref(
            "Patient", eff_patient_ref.split("/")[-1] if eff_patient_ref else None
        ),
        "encounter": ref(
            "Encounter", eff_encounter_ref.split("/")[-1] if eff_encounter_ref else None
        ),
        "occurrencePeriod": occ.get("period") if occ and "period" in occ else None,
        "occurrenceDateTime": occ.get("datetime")
        if occ and "datetime" in occ
        else None,
        "reason": _reason(grab(d, "reasoncode"), grab(d, "reasondescription")),
        "extension": [
            {
                "url": "http://example.org/fhir/StructureDefinition/baseCost",
                "valueMoney": {"value": float(base_cost), "currency": "USD"},
            }
        ]
        if base_cost is not None
        else None,
    }


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
    return Procedure(**_to_fhir_procedure(to_dict(src), patient_ref, encounter_ref))
