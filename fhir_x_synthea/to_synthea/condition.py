"""FHIR R4 Condition → Synthea Condition"""

import logging
from datetime import date

from fhir.resources.condition import Condition
from synthea_pydantic import Condition as SyntheaCondition

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_reference_id,
    parse_datetime_to_date,
)

logger = logging.getLogger(__name__)


def convert(src: Condition) -> SyntheaCondition:
    """Convert FHIR R4 Condition to Synthea Condition.

    Args:
        src: FHIR R4 Condition resource

    Returns:
        Synthea Condition model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract START from onsetDateTime
    start = None
    onset = fhir_resource.get("onsetDateTime")
    if onset:
        if isinstance(onset, date):
            start = onset
        else:
            parsed = parse_datetime_to_date(str(onset))
            if parsed:
                start = date.fromisoformat(parsed)

    # Extract STOP from abatementDateTime
    stop = None
    abatement = fhir_resource.get("abatementDateTime")
    if abatement:
        if isinstance(abatement, date):
            stop = abatement
        else:
            parsed = parse_datetime_to_date(str(abatement))
            if parsed:
                stop = date.fromisoformat(parsed)

    # Extract PATIENT reference
    patient = ""
    subject = fhir_resource.get("subject")
    if subject:
        patient = extract_reference_id(subject)

    # Extract ENCOUNTER reference
    encounter = ""
    encounter_ref = fhir_resource.get("encounter")
    if encounter_ref:
        encounter = extract_reference_id(encounter_ref)

    # Extract CODE and DESCRIPTION
    code = ""
    description = ""
    code_obj = fhir_resource.get("code")
    if code_obj:
        code = extract_coding_code(code_obj, preferred_system="http://snomed.info/sct")
        description = extract_display_or_text(code_obj)

    # Log lossy conversions
    categories = fhir_resource.get("category", [])
    if len(categories) > 1:
        logger.warning(
            "Condition %s has %d categories; Synthea doesn't support categories",
            src.id,
            len(categories),
        )

    return SyntheaCondition(
        start=start,
        stop=stop,
        patient=patient or None,
        encounter=encounter or None,
        code=code or "unknown",
        description=description or "Unknown condition",
    )
