"""FHIR R4 CarePlan → Synthea CarePlan"""

import logging
from datetime import date

from fhir.resources.careplan import CarePlan
from synthea_pydantic import CarePlan as SyntheaCarePlan

from ..chidian_ext import (
    extract_code,
    extract_display,
    extract_ref_id,
    grab,
    mapper,
    parse_date,
    to_dict,
)

logger = logging.getLogger(__name__)


def _extract_reason(d: dict) -> tuple[str, str]:
    """Extract reason code and description from addresses or reasonCode."""
    # R4B uses addresses instead of reasonCode
    addresses = grab(d, "addresses") or []
    if addresses:
        first_address = addresses[0]
        # Check if it's a CodeableReference (R4B) or CodeableConcept (R4)
        if "concept" in first_address:
            concept = first_address["concept"]
            code = extract_code({"c": concept}, "c", system="http://snomed.info/sct")
            desc = extract_display({"c": concept}, "c")
            return code, desc
        else:
            code = extract_code(
                {"c": first_address}, "c", system="http://snomed.info/sct"
            )
            desc = extract_display({"c": first_address}, "c")
            return code, desc

    # Fallback to reasonCode
    reason_codes = grab(d, "reasonCode") or []
    if reason_codes:
        first_reason = reason_codes[0]
        code = extract_code({"c": first_reason}, "c", system="http://snomed.info/sct")
        desc = extract_display({"c": first_reason}, "c")
        return code, desc

    return "", ""


@mapper(remove_empty=False)
def _to_synthea_careplan(d: dict):
    """Core mapping from dict to Synthea CarePlan structure."""
    # Extract period
    period = grab(d, "period") or {}

    start = None
    start_str = period.get("start")
    if start_str:
        parsed = parse_date({"dt": start_str}, "dt")
        if parsed:
            start = date.fromisoformat(parsed)

    stop = None
    stop_str = period.get("end")
    if stop_str:
        parsed = parse_date({"dt": stop_str}, "dt")
        if parsed:
            stop = date.fromisoformat(parsed)

    # Extract code from category
    categories = grab(d, "category") or []
    code = ""
    if categories:
        code = extract_code({"c": categories[0]}, "c", system="http://snomed.info/sct")

    # Extract description
    description = grab(d, "description") or grab(d, "title") or "Unknown care plan"

    # Extract reason
    reason_code, reason_description = _extract_reason(d)

    # Log lossy conversions
    if len(categories) > 1:
        logger.warning(
            "CarePlan has %d categories; only first preserved", len(categories)
        )

    return {
        "id": grab(d, "id") or None,
        "start": start,
        "stop": stop,
        "patient": extract_ref_id(d, "subject") or None,
        "encounter": extract_ref_id(d, "encounter") or None,
        "code": code or "unknown",
        "description": description,
        "reasoncode": reason_code or None,
        "reasondescription": reason_description or None,
    }


def convert(src: CarePlan) -> SyntheaCarePlan:
    """Convert FHIR R4 CarePlan to Synthea CarePlan.

    Args:
        src: FHIR R4 CarePlan resource

    Returns:
        Synthea CarePlan model
    """
    return SyntheaCarePlan(**_to_synthea_careplan(to_dict(src)))
