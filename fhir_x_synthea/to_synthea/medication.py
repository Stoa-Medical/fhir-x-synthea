"""FHIR R4 MedicationRequest → Synthea Medication"""

import logging
from datetime import date

from fhir.resources.medicationrequest import MedicationRequest
from synthea_pydantic import Medication as SyntheaMedication

from ..chidian_ext import (
    extract_code,
    extract_display,
    extract_ext,
    extract_ref_id,
    grab,
    mapper,
    parse_date,
    to_dict,
)
from ..synthea_lib import to_decimal

logger = logging.getLogger(__name__)


def _extract_medication(d: dict) -> tuple[str, str]:
    """Extract medication code and description."""
    # R4B: medication is CodeableReference with concept or reference
    medication = grab(d, "medication")
    if medication:
        if "concept" in medication:
            code = extract_code(
                {"m": medication["concept"]},
                "m",
                system="http://www.nlm.nih.gov/research/umls/rxnorm",
            )
            desc = extract_display({"m": medication["concept"]}, "m")
            return code, desc

    # R4: medicationCodeableConcept
    medication_code = grab(d, "medicationCodeableConcept")
    if medication_code:
        code = extract_code(
            {"m": medication_code},
            "m",
            system="http://www.nlm.nih.gov/research/umls/rxnorm",
        )
        desc = extract_display({"m": medication_code}, "m")
        return code, desc

    return "", ""


def _extract_reason(d: dict) -> tuple[str, str]:
    """Extract reason code and description."""
    # R4B uses reason with CodeableReference
    reasons = grab(d, "reason") or []
    if reasons:
        first_reason = reasons[0]
        if "concept" in first_reason:
            code = extract_code(
                {"r": first_reason["concept"]}, "r", system="http://snomed.info/sct"
            )
            desc = extract_display({"r": first_reason["concept"]}, "r")
            return code, desc

    # R4: reasonCode
    reason_codes = grab(d, "reasonCode") or []
    if reason_codes:
        first_reason = reason_codes[0]
        code = extract_code({"r": first_reason}, "r", system="http://snomed.info/sct")
        desc = extract_display({"r": first_reason}, "r")
        return code, desc

    return "", ""


def _extract_payer(d: dict) -> str:
    """Extract payer from insurance."""
    insurance = grab(d, "insurance") or []
    if insurance:
        first_insurance = insurance[0]
        coverage = (
            first_insurance.get("coverage")
            if isinstance(first_insurance, dict)
            else first_insurance
        )
        if coverage and isinstance(coverage, dict):
            ref = coverage.get("reference", "")
            if "/" in ref:
                return ref.split("/")[-1]
            return ref
    return ""


@mapper(remove_empty=False)
def _to_synthea_medication(d: dict):
    """Core mapping from dict to Synthea Medication structure."""
    # Extract start (prefer authoredOn, fallback to occurrencePeriod.start)
    start = None
    authored_on = grab(d, "authoredOn")
    occurrence_period = grab(d, "occurrencePeriod") or {}

    if authored_on:
        parsed = parse_date({"dt": authored_on}, "dt")
        if parsed:
            start = date.fromisoformat(parsed)
    elif occurrence_period.get("start"):
        parsed = parse_date({"dt": occurrence_period["start"]}, "dt")
        if parsed:
            start = date.fromisoformat(parsed)

    # Extract stop
    stop = None
    if occurrence_period.get("end"):
        parsed = parse_date({"dt": occurrence_period["end"]}, "dt")
        if parsed:
            stop = date.fromisoformat(parsed)

    # Extract medication
    code, description = _extract_medication(d)

    # Extract dispenses
    dispense_request = grab(d, "dispenseRequest") or {}
    repeats_allowed = dispense_request.get("numberOfRepeatsAllowed")
    dispenses = int(repeats_allowed) if repeats_allowed is not None else None

    # Extract reason
    reason_code, reason_description = _extract_reason(d)

    # Extract financial extensions
    base_cost_str = extract_ext(
        d,
        "http://synthea.org/fhir/StructureDefinition/medication-baseCost",
        "valueDecimal",
        "",
    )
    payer_coverage_str = extract_ext(
        d,
        "http://synthea.org/fhir/StructureDefinition/medication-payerCoverage",
        "valueDecimal",
        "",
    )
    total_cost_str = extract_ext(
        d,
        "http://synthea.org/fhir/StructureDefinition/medication-totalCost",
        "valueDecimal",
        "",
    )

    return {
        "start": start,
        "stop": stop,
        "patient": extract_ref_id(d, "subject") or None,
        "payer": _extract_payer(d) or None,
        "encounter": extract_ref_id(d, "encounter") or None,
        "code": code or "unknown",
        "description": description or "Unknown medication",
        "base_cost": to_decimal(base_cost_str) if base_cost_str else None,
        "payer_coverage": to_decimal(payer_coverage_str)
        if payer_coverage_str
        else None,
        "dispenses": dispenses,
        "totalcost": to_decimal(total_cost_str) if total_cost_str else None,
        "reasoncode": reason_code or None,
        "reasondescription": reason_description or None,
    }


def convert(src: MedicationRequest) -> SyntheaMedication:
    """Convert FHIR R4 MedicationRequest to Synthea Medication.

    Args:
        src: FHIR R4 MedicationRequest resource

    Returns:
        Synthea Medication model
    """
    return SyntheaMedication(**_to_synthea_medication(to_dict(src)))
