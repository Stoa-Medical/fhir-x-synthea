"""FHIR R4 Procedure -> Synthea Procedure"""

from fhir.resources.procedure import Procedure
from synthea_pydantic import Procedure as SyntheaProcedure

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


@mapper(remove_empty=False)
def _to_synthea_procedure(d: dict):
    """Core mapping from FHIR Procedure dict to Synthea structure."""
    # Extract occurrence dates
    start = parse_date(d, "occurrencePeriod.start") or parse_date(d, "occurrenceDateTime") or None
    stop = parse_date(d, "occurrencePeriod.end") or None

    # Extract reason
    reasons = grab(d, "reason") or []
    reason_code = ""
    reason_description = ""
    if reasons:
        concept = reasons[0].get("concept", {})
        codings = concept.get("coding", [])
        if codings:
            reason_code = codings[0].get("code", "")
            reason_description = codings[0].get("display", "")
        if not reason_description:
            reason_description = concept.get("text", "")

    # Extract base cost
    base_cost = extract_ext(
        d,
        "http://example.org/fhir/StructureDefinition/baseCost",
        "valueMoney",
        None,
    )
    base_cost_value = None
    if isinstance(base_cost, dict):
        base_cost_value = base_cost.get("value")
    elif base_cost is not None:
        base_cost_value = base_cost

    return {
        "start": start,
        "stop": stop,
        "patient": extract_ref_id(d, "subject") or None,
        "encounter": extract_ref_id(d, "encounter") or None,
        "code": extract_code(d, "code", system="http://snomed.info/sct") or None,
        "description": extract_display(d, "code") or None,
        "base_cost": base_cost_value,
        "reasoncode": reason_code or None,
        "reasondescription": reason_description or None,
    }


def convert(src: Procedure) -> SyntheaProcedure:
    """Convert FHIR R4 Procedure to Synthea Procedure.

    Args:
        src: FHIR R4 Procedure resource

    Returns:
        Synthea Procedure model
    """
    return SyntheaProcedure(**_to_synthea_procedure(to_dict(src)))
