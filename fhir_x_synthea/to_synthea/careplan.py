"""
Mapping function for converting FHIR CarePlan resources to Synthea careplans.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_reference_id,
    parse_datetime,
)


def map_fhir_careplan_to_csv(fhir_resource: dict[str, Any]) -> dict[str, Any]:
    """
    Map a FHIR R4 CarePlan resource to a Synthea careplans.csv row.

    Args:
        fhir_resource: Dictionary representing a FHIR CarePlan resource

    Returns:
        Dictionary with CSV column names as keys (Id, Start, Stop, etc.)
    """

    # Initialize CSV row
    csv_row: dict[str, str] = {
        "Id": "",
        "Start": "",
        "Stop": "",
        "Patient": "",
        "Encounter": "",
        "Code": "",
        "Description": "",
        "ReasonCode": "",
        "ReasonDescription": "",
    }

    # Extract Id
    resource_id = fhir_resource.get("id", "")
    if resource_id:
        csv_row["Id"] = resource_id

    # Extract Start and Stop from period
    period = fhir_resource.get("period", {})
    start = period.get("start")
    if start:
        csv_row["Start"] = parse_datetime(start)

    stop = period.get("end")
    if stop:
        csv_row["Stop"] = parse_datetime(stop)

    # Extract Patient reference
    subject = fhir_resource.get("subject")
    if subject:
        csv_row["Patient"] = extract_reference_id(subject)

    # Extract Encounter reference
    encounter = fhir_resource.get("encounter")
    if encounter:
        csv_row["Encounter"] = extract_reference_id(encounter)

    # Extract Code from category (SNOMED)
    categories = fhir_resource.get("category", [])
    if categories:
        first_category = categories[0]
        csv_row["Code"] = extract_coding_code(first_category, "http://snomed.info/sct")

    # Extract Description (prefer description, fallback to title)
    description = fhir_resource.get("description", "")
    title = fhir_resource.get("title", "")
    if description:
        csv_row["Description"] = description
    elif title:
        csv_row["Description"] = title

    # Extract ReasonCode and ReasonDescription
    reason_codes = fhir_resource.get("reasonCode", [])
    if reason_codes:
        first_reason = reason_codes[0]
        csv_row["ReasonCode"] = extract_coding_code(
            first_reason, "http://snomed.info/sct"
        )
        csv_row["ReasonDescription"] = extract_display_or_text(first_reason)

    return csv_row
