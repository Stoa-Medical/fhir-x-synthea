"""FHIR R4 Condition → Synthea Condition"""

import logging
from datetime import date

from fhir.resources.condition import Condition
from synthea_pydantic import Condition as SyntheaCondition

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


@mapper(remove_empty=False)
def _to_synthea_condition(d: dict):
    """Core mapping from dict to Synthea Condition structure."""
    # Parse start from onsetDateTime
    start = None
    onset = grab(d, "onsetDateTime")
    if onset:
        if isinstance(onset, date):
            start = onset
        else:
            parsed = parse_date({"dt": onset}, "dt")
            if parsed:
                start = date.fromisoformat(parsed)

    # Parse stop from abatementDateTime
    stop = None
    abatement = grab(d, "abatementDateTime")
    if abatement:
        if isinstance(abatement, date):
            stop = abatement
        else:
            parsed = parse_date({"dt": abatement}, "dt")
            if parsed:
                stop = date.fromisoformat(parsed)

    # Log lossy conversions
    categories = grab(d, "category") or []
    if len(categories) > 1:
        logger.warning(
            "Condition has %d categories; Synthea doesn't support categories",
            len(categories),
        )

    return {
        "start": start,
        "stop": stop,
        "patient": extract_ref_id(d, "subject") or None,
        "encounter": extract_ref_id(d, "encounter") or None,
        "code": extract_code(d, "code", system="http://snomed.info/sct") or "unknown",
        "description": extract_display(d, "code") or "Unknown condition",
    }


def convert(src: Condition) -> SyntheaCondition:
    """Convert FHIR R4 Condition to Synthea Condition.

    Args:
        src: FHIR R4 Condition resource

    Returns:
        Synthea Condition model
    """
    return SyntheaCondition(**_to_synthea_condition(to_dict(src)))
