"""FHIR R4 CarePlan → Synthea CarePlan"""

import logging
from datetime import date

from fhir.resources.careplan import CarePlan
from synthea_pydantic import CarePlan as SyntheaCarePlan

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_reference_id,
    parse_datetime_to_date,
)

logger = logging.getLogger(__name__)


def convert(src: CarePlan) -> SyntheaCarePlan:
    """Convert FHIR R4 CarePlan to Synthea CarePlan.

    Args:
        src: FHIR R4 CarePlan resource

    Returns:
        Synthea CarePlan model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract Id
    resource_id = fhir_resource.get("id", "")

    # Extract Start and Stop from period
    start = None
    stop = None
    period = fhir_resource.get("period", {})
    start_str = period.get("start")
    if start_str:
        parsed = parse_datetime_to_date(start_str)
        if parsed:
            start = date.fromisoformat(parsed)

    stop_str = period.get("end")
    if stop_str:
        parsed = parse_datetime_to_date(stop_str)
        if parsed:
            stop = date.fromisoformat(parsed)

    # Extract Patient reference
    patient = ""
    subject = fhir_resource.get("subject")
    if subject:
        patient = extract_reference_id(subject)

    # Extract Encounter reference
    encounter = ""
    encounter_ref = fhir_resource.get("encounter")
    if encounter_ref:
        encounter = extract_reference_id(encounter_ref)

    # Extract Code from category (SNOMED)
    code = ""
    categories = fhir_resource.get("category", [])
    if categories:
        first_category = categories[0]
        code = extract_coding_code(
            first_category, preferred_system="http://snomed.info/sct"
        )

    # Extract Description (prefer description, fallback to title)
    description = fhir_resource.get("description", "")
    if not description:
        description = fhir_resource.get("title", "")

    # Extract ReasonCode and ReasonDescription
    reason_code = ""
    reason_description = ""

    # R4B uses addresses instead of reasonCode
    addresses = fhir_resource.get("addresses", [])
    if addresses:
        first_address = addresses[0]
        # Check if it's a CodeableReference (R4B) or CodeableConcept (R4)
        if "concept" in first_address:
            concept = first_address["concept"]
            reason_code = extract_coding_code(
                concept, preferred_system="http://snomed.info/sct"
            )
            reason_description = extract_display_or_text(concept)
        else:
            reason_code = extract_coding_code(
                first_address, preferred_system="http://snomed.info/sct"
            )
            reason_description = extract_display_or_text(first_address)

    # Fallback to reasonCode if addresses is empty
    if not reason_code:
        reason_codes = fhir_resource.get("reasonCode", [])
        if reason_codes:
            first_reason = reason_codes[0]
            reason_code = extract_coding_code(
                first_reason, preferred_system="http://snomed.info/sct"
            )
            reason_description = extract_display_or_text(first_reason)

    # Log lossy conversions
    if len(categories) > 1:
        logger.warning(
            "CarePlan %s has %d categories; only first preserved",
            src.id,
            len(categories),
        )

    return SyntheaCarePlan(
        id=resource_id or None,
        start=start,
        stop=stop,
        patient=patient or None,
        encounter=encounter or None,
        code=code or "unknown",
        description=description or "Unknown care plan",
        reasoncode=reason_code or None,
        reasondescription=reason_description or None,
    )
