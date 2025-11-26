"""
Mapping function for converting FHIR AllergyIntolerance resources to Synthea allergies.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_coding_system,
    extract_display_or_text,
    extract_reference_id,
    parse_datetime,
)


def map_fhir_allergy_to_csv(fhir_resource: dict[str, Any]) -> dict[str, Any]:
    """
    Map a FHIR R4 AllergyIntolerance resource to a Synthea allergies.csv row.

    Args:
        fhir_resource: Dictionary representing a FHIR AllergyIntolerance resource

    Returns:
        Dictionary with CSV column names as keys (START, STOP, PATIENT, etc.)
    """

    # Initialize CSV row with empty strings
    csv_row: dict[str, str] = {
        "START": "",
        "STOP": "",
        "PATIENT": "",
        "ENCOUNTER": "",
        "CODE": "",
        "SYSTEM": "",
        "DESCRIPTION": "",
        "TYPE": "",
        "CATEGORY": "",
        "REACTION1": "",
        "DESCRIPTION1": "",
        "SEVERITY1": "",
        "REACTION2": "",
        "DESCRIPTION2": "",
        "SEVERITY2": "",
    }

    # Extract START (prefer recordedDate, fallback to onsetDateTime)
    recorded_date = fhir_resource.get("recordedDate")
    onset_date = fhir_resource.get("onsetDateTime")
    if recorded_date:
        csv_row["START"] = parse_datetime(recorded_date)
    elif onset_date:
        csv_row["START"] = parse_datetime(onset_date)

    # Extract STOP (lastOccurrence)
    last_occurrence = fhir_resource.get("lastOccurrence")
    if last_occurrence:
        csv_row["STOP"] = parse_datetime(last_occurrence)
    else:
        # If clinicalStatus indicates resolved but no lastOccurrence, leave empty
        clinical_status = fhir_resource.get("clinicalStatus", {})
        status_codings = clinical_status.get("coding", [])
        for coding in status_codings:
            code = coding.get("code", "")
            if code in ("resolved", "inactive"):
                csv_row["STOP"] = ""  # Empty as per spec

    # Extract PATIENT reference
    patient_ref = fhir_resource.get("patient")
    if patient_ref:
        csv_row["PATIENT"] = extract_reference_id(patient_ref)

    # Extract ENCOUNTER reference
    encounter_ref = fhir_resource.get("encounter")
    if encounter_ref:
        csv_row["ENCOUNTER"] = extract_reference_id(encounter_ref)

    # Extract CODE, SYSTEM, DESCRIPTION from code
    code_obj = fhir_resource.get("code")
    if code_obj:
        csv_row["CODE"] = extract_coding_code(
            code_obj,
            preferred_systems=[
                "http://snomed.info/sct",
                "http://www.nlm.nih.gov/research/umls/rxnorm",
            ],
        )
        csv_row["SYSTEM"] = extract_coding_system(code_obj)
        csv_row["DESCRIPTION"] = extract_display_or_text(code_obj)

    # Extract TYPE
    allergy_type = fhir_resource.get("type", "")
    if allergy_type:
        csv_row["TYPE"] = allergy_type.lower()

    # Extract CATEGORY
    categories = fhir_resource.get("category", [])
    if categories:
        # Take first category and normalize
        first_category = categories[0]
        if isinstance(first_category, str):
            csv_row["CATEGORY"] = first_category
        # Category is typically just a string in FHIR for AllergyIntolerance

    # Extract reactions
    reactions = fhir_resource.get("reaction", [])
    if len(reactions) > 0:
        reaction1 = reactions[0]

        # REACTION1 code from manifestation
        manifestations = reaction1.get("manifestation", [])
        if manifestations:
            first_manifestation = manifestations[0]
            csv_row["REACTION1"] = extract_coding_code(
                first_manifestation, preferred_systems=["http://snomed.info/sct"]
            )

        # DESCRIPTION1
        csv_row["DESCRIPTION1"] = reaction1.get("description", "")

        # SEVERITY1
        severity = reaction1.get("severity", "")
        if severity:
            csv_row["SEVERITY1"] = severity.upper()

    if len(reactions) > 1:
        reaction2 = reactions[1]

        # REACTION2 code from manifestation
        manifestations = reaction2.get("manifestation", [])
        if manifestations:
            first_manifestation = manifestations[0]
            csv_row["REACTION2"] = extract_coding_code(
                first_manifestation, preferred_systems=["http://snomed.info/sct"]
            )

        # DESCRIPTION2
        csv_row["DESCRIPTION2"] = reaction2.get("description", "")

        # SEVERITY2
        severity = reaction2.get("severity", "")
        if severity:
            csv_row["SEVERITY2"] = severity.upper()

    return csv_row
