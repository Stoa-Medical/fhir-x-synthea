"""Synthea Medication → FHIR R4 MedicationRequest"""

from fhir.resources.medicationrequest import MedicationRequest
from synthea_pydantic import Medication as SyntheaMedication

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import codeable_concept, format_datetime, ref


def _medication_id(d: dict) -> str:
    """Generate deterministic medication ID."""
    patient_id = grab(d, "patient") or ""
    start = grab(d, "start") or ""
    code = grab(d, "code") or ""
    return f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")


def _reason(reason_code: str | None, reason_desc: str | None) -> list | None:
    """Build medication reason (CodeableReference)."""
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


def _financial_extensions(d: dict):
    """Build financial extensions."""
    base_cost = grab(d, "base_cost")
    payer_coverage = grab(d, "payer_coverage")
    total_cost = grab(d, "totalcost")

    extensions = []
    if base_cost is not None:
        extensions.append(
            {
                "url": "http://synthea.org/fhir/StructureDefinition/medication-baseCost",
                "valueDecimal": float(base_cost),
            }
        )
    if payer_coverage is not None:
        extensions.append(
            {
                "url": "http://synthea.org/fhir/StructureDefinition/medication-payerCoverage",
                "valueDecimal": float(payer_coverage),
            }
        )
    if total_cost is not None:
        extensions.append(
            {
                "url": "http://synthea.org/fhir/StructureDefinition/medication-totalCost",
                "valueDecimal": float(total_cost),
            }
        )

    return extensions if extensions else None


@mapper
def _to_fhir_medication(
    d: dict,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
):
    """Core mapping from dict to FHIR MedicationRequest structure."""
    patient_id = grab(d, "patient")
    encounter_id = grab(d, "encounter")
    payer_id = grab(d, "payer")
    stop = grab(d, "stop")
    dispenses = grab(d, "dispenses")

    # Build effective references
    eff_patient_ref = patient_ref or (f"Patient/{patient_id}" if patient_id else None)
    eff_encounter_ref = encounter_ref or (
        f"Encounter/{encounter_id}" if encounter_id else None
    )

    # Build medication CodeableConcept
    med_code = codeable_concept(
        system="http://www.nlm.nih.gov/research/umls/rxnorm",
        code=grab(d, "code"),
        display=grab(d, "description"),
        text=grab(d, "description"),
    )

    return {
        "resourceType": "MedicationRequest",
        "id": _medication_id(d),
        "status": "completed" if stop else "active",
        "intent": "order",
        "medication": {"concept": med_code} if med_code else None,
        "subject": ref(
            "Patient", eff_patient_ref.split("/")[-1] if eff_patient_ref else None
        ),
        "encounter": ref(
            "Encounter", eff_encounter_ref.split("/")[-1] if eff_encounter_ref else None
        ),
        "authoredOn": grab(d, "start", apply=format_datetime),
        "insurance": [{"reference": f"Coverage/{payer_id}"}] if payer_id else None,
        "dispenseRequest": {"numberOfRepeatsAllowed": int(dispenses)}
        if dispenses is not None
        else None,
        "reason": _reason(grab(d, "reasoncode"), grab(d, "reasondescription")),
        "extension": _financial_extensions(d),
    }


def convert(
    src: SyntheaMedication,
    *,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
) -> MedicationRequest:
    """Convert Synthea Medication to FHIR R4 MedicationRequest.

    Args:
        src: Synthea Medication model
        patient_ref: Optional patient reference (e.g., "Patient/123")
        encounter_ref: Optional encounter reference (e.g., "Encounter/456")

    Returns:
        FHIR R4 MedicationRequest resource
    """
    return MedicationRequest(
        **_to_fhir_medication(to_dict(src), patient_ref, encounter_ref)
    )
