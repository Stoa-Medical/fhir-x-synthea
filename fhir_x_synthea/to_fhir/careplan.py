"""Synthea CarePlan → FHIR R4 CarePlan"""

from fhir.resources.careplan import CarePlan
from synthea_pydantic import CarePlan as SyntheaCarePlan

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import format_datetime, period, ref


def _careplan_id(d: dict) -> str:
    """Generate deterministic careplan ID."""
    careplan_id = grab(d, "id")
    if careplan_id:
        return careplan_id
    patient_id = grab(d, "patient") or ""
    start = grab(d, "start") or ""
    code = grab(d, "code") or ""
    return f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")


def _addresses(reason_code: str | None, reason_desc: str | None) -> list | None:
    """Build CarePlan addresses (reason) structure."""
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
def _to_fhir_careplan(
    d: dict,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
):
    """Core mapping from dict to FHIR CarePlan structure."""
    patient_id = grab(d, "patient")
    encounter_id = grab(d, "encounter")
    start = grab(d, "start")
    stop = grab(d, "stop")
    code = grab(d, "code")
    description = grab(d, "description")

    # Build effective references
    eff_patient_ref = patient_ref or (f"Patient/{patient_id}" if patient_id else None)
    eff_encounter_ref = encounter_ref or (
        f"Encounter/{encounter_id}" if encounter_id else None
    )

    # Build period
    care_period = period(
        format_datetime(start) if start else None,
        format_datetime(stop) if stop else None,
    )

    return {
        "resourceType": "CarePlan",
        "id": _careplan_id(d),
        "status": "completed" if stop else "active",
        "intent": "plan",
        "title": description,
        "description": description,
        "category": [{"coding": [{"system": "http://snomed.info/sct", "code": code}]}]
        if code
        else None,
        "subject": ref(
            "Patient", eff_patient_ref.split("/")[-1] if eff_patient_ref else None
        ),
        "encounter": ref(
            "Encounter", eff_encounter_ref.split("/")[-1] if eff_encounter_ref else None
        ),
        "period": care_period,
        "addresses": _addresses(grab(d, "reasoncode"), grab(d, "reasondescription")),
    }


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
    return CarePlan(**_to_fhir_careplan(to_dict(src), patient_ref, encounter_ref))
