"""FHIR R4 AllergyIntolerance → Synthea Allergy"""

import logging

from fhir.resources.allergyintolerance import AllergyIntolerance
from synthea_pydantic import Allergy

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_coding_system,
    extract_display_or_text,
    extract_reference_id,
    parse_datetime,
)

logger = logging.getLogger(__name__)


def convert(src: AllergyIntolerance) -> Allergy:
    """Convert FHIR R4 AllergyIntolerance to Synthea Allergy.

    Args:
        src: FHIR R4 AllergyIntolerance resource

    Returns:
        Synthea Allergy model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    # Convert to dict for extraction helpers
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract START (prefer recordedDate, fallback to onsetDateTime)
    start = ""
    recorded_date = fhir_resource.get("recordedDate")
    onset_date = fhir_resource.get("onsetDateTime")
    if recorded_date:
        start = parse_datetime(recorded_date)
    elif onset_date:
        start = parse_datetime(onset_date)

    # Extract STOP (lastOccurrence)
    stop = ""
    last_occurrence = fhir_resource.get("lastOccurrence")
    if last_occurrence:
        stop = parse_datetime(last_occurrence)

    # Extract PATIENT reference
    patient = ""
    patient_ref = fhir_resource.get("patient")
    if patient_ref:
        patient = extract_reference_id(patient_ref)

    # Extract ENCOUNTER reference
    encounter = ""
    encounter_ref = fhir_resource.get("encounter")
    if encounter_ref:
        encounter = extract_reference_id(encounter_ref)

    # Extract CODE, SYSTEM, DESCRIPTION from code
    code = ""
    system = ""
    description = ""
    code_obj = fhir_resource.get("code")
    if code_obj:
        code = extract_coding_code(
            code_obj,
            preferred_systems=[
                "http://snomed.info/sct",
                "http://www.nlm.nih.gov/research/umls/rxnorm",
            ],
        )
        system = extract_coding_system(code_obj)
        description = extract_display_or_text(code_obj)

    # Extract TYPE (R4B uses CodeableConcept for type)
    allergy_type = ""
    type_obj = fhir_resource.get("type")
    if type_obj:
        if isinstance(type_obj, dict):
            # Extract code from CodeableConcept
            allergy_type = extract_coding_code(
                type_obj,
                preferred_systems=["http://hl7.org/fhir/allergy-intolerance-type"],
            )
        elif isinstance(type_obj, str):
            allergy_type = type_obj.lower()

    # Extract CATEGORY
    category = ""
    categories = fhir_resource.get("category", [])
    if categories:
        first_category = categories[0]
        if isinstance(first_category, str):
            category = first_category

    # Extract reactions
    reaction1 = ""
    description1 = ""
    severity1 = ""
    reaction2 = ""
    description2 = ""
    severity2 = ""

    reactions = fhir_resource.get("reaction", [])
    if len(reactions) > 0:
        r1 = reactions[0]
        manifestations = r1.get("manifestation", [])
        if manifestations:
            reaction1 = extract_coding_code(
                manifestations[0], preferred_systems=["http://snomed.info/sct"]
            )
        description1 = r1.get("description", "")
        sev = r1.get("severity", "")
        if sev:
            severity1 = sev.upper()

    if len(reactions) > 1:
        r2 = reactions[1]
        manifestations = r2.get("manifestation", [])
        if manifestations:
            reaction2 = extract_coding_code(
                manifestations[0], preferred_systems=["http://snomed.info/sct"]
            )
        description2 = r2.get("description", "")
        sev = r2.get("severity", "")
        if sev:
            severity2 = sev.upper()

    # Log lossy conversions
    if len(reactions) > 2:
        logger.warning(
            "AllergyIntolerance %s has %d reactions; only first 2 preserved",
            src.id,
            len(reactions),
        )

    # Use lowercase field names (synthea_pydantic accepts both but normalizes to lowercase)
    return Allergy(
        start=start or None,
        stop=stop or None,
        patient=patient or None,
        encounter=encounter or None,
        code=code or None,
        system=system or None,
        description=description or None,
        type=allergy_type or None,
        category=category or None,
        reaction1=reaction1 or None,
        description1=description1 or None,
        severity1=severity1 or None,
        reaction2=reaction2 or None,
        description2=description2 or None,
        severity2=severity2 or None,
    )
