"""
Mapping function for converting FHIR Coverage resources to Synthea payer_transitions.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import (
    extract_extension_string,
    extract_reference_id,
    extract_year,
)


def map_fhir_coverage_to_csv(fhir_resource: dict[str, Any]) -> dict[str, Any]:
    """
    Map a FHIR R4 Coverage resource to a Synthea payer_transitions.csv row.

    Args:
        fhir_resource: Dictionary representing a FHIR Coverage resource

    Returns:
        Dictionary with CSV column names as keys
    """

    # Helper to map relationship
    def map_relationship(relationship_obj: dict[str, Any] | None) -> str:
        if not relationship_obj:
            return ""

        # Check codings first
        codings = relationship_obj.get("coding", [])
        for coding in codings:
            code = coding.get("code", "")
            if code == "self":
                return "Self"
            elif code == "spouse":
                return "Spouse"

        # Check text (for Guardian)
        text = relationship_obj.get("text", "")
        if text == "Guardian":
            return "Guardian"

        return ""

    # Initialize CSV row
    csv_row: dict[str, str] = {
        "Patient": "",
        "Member ID": "",
        "Start_Year": "",
        "End_Year": "",
        "Payer": "",
        "Secondary Payer": "",
        "Ownership": "",
        "Owner Name": "",
    }

    # Extract Patient reference
    beneficiary = fhir_resource.get("beneficiary")
    if beneficiary:
        csv_row["Patient"] = extract_reference_id(beneficiary)

    # Extract Member ID (prefer subscriberId, fallback to identifier)
    subscriber_id = fhir_resource.get("subscriberId", "")
    if subscriber_id:
        csv_row["Member ID"] = subscriber_id
    else:
        identifiers = fhir_resource.get("identifier", [])
        if identifiers:
            csv_row["Member ID"] = identifiers[0].get("value", "")

    # Extract Start_Year and End_Year from period
    period = fhir_resource.get("period", {})
    start = period.get("start")
    if start:
        csv_row["Start_Year"] = extract_year(start)

    end = period.get("end")
    if end:
        csv_row["End_Year"] = extract_year(end)

    # Extract Payer references (primary and secondary)
    payors = fhir_resource.get("payor", [])
    if len(payors) > 0:
        csv_row["Payer"] = extract_reference_id(payors[0])

    if len(payors) > 1:
        csv_row["Secondary Payer"] = extract_reference_id(payors[1])

    # Extract Ownership (relationship)
    relationship = fhir_resource.get("relationship")
    if relationship:
        csv_row["Ownership"] = map_relationship(relationship)

    # Extract Owner Name from extension
    owner_name = extract_extension_string(
        fhir_resource,
        "http://synthea.mitre.org/fhir/StructureDefinition/policy-owner-name",
    )
    csv_row["Owner Name"] = owner_name

    return csv_row
