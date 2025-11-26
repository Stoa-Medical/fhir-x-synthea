"""
Mapping function for converting FHIR Encounter resources to Synthea encounters.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_extension_decimal,
    extract_extension_reference,
    extract_reference_id,
    parse_datetime,
)


def map_fhir_encounter_to_csv(fhir_resource: dict[str, Any]) -> dict[str, Any]:
    """
    Map a FHIR R4 Encounter resource to a Synthea encounters.csv row.

    Args:
        fhir_resource: Dictionary representing a FHIR Encounter resource

    Returns:
        Dictionary with CSV column names as keys (Id, Start, Stop, etc.)
    """

    # Helper to map encounter class to Synthea string
    def map_encounter_class(encounter_class: dict[str, Any] | None) -> str:
        if not encounter_class:
            return ""
        codings = encounter_class.get("coding", [])
        if not codings:
            return ""

        # Check ActCode system
        for coding in codings:
            code = coding.get("code", "")
            system = coding.get("system", "")
            if (
                "v3-ActCode" in system
                or "terminology.hl7.org/CodeSystem/v3-ActCode" in system
            ):
                code_map = {
                    "AMB": "ambulatory",
                    "EMER": "emergency",
                    "IMP": "inpatient",
                    "ACUTE": "inpatient",
                }
                return code_map.get(code, "")

        # Fallback to display
        display = codings[0].get("display", "")
        if display:
            return display.lower()

        return ""

    # Initialize CSV row
    csv_row: dict[str, str] = {
        "Id": "",
        "Start": "",
        "Stop": "",
        "Patient": "",
        "Organization": "",
        "Provider": "",
        "EncounterClass": "",
        "Code": "",
        "Description": "",
        "ReasonCode": "",
        "ReasonDescription": "",
        "Base_Encounter_Cost": "",
        "Total_Claim_Cost": "",
        "Payer_Coverage": "",
        "Payer": "",
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

    # Extract Organization reference
    service_provider = fhir_resource.get("serviceProvider")
    if service_provider:
        csv_row["Organization"] = extract_reference_id(service_provider)

    # Extract Provider from participant
    participants = fhir_resource.get("participant", [])
    if participants:
        first_participant = participants[0]
        individual = first_participant.get("individual")
        if individual:
            csv_row["Provider"] = extract_reference_id(individual)

    # Extract EncounterClass
    encounter_class = fhir_resource.get("class")
    if encounter_class:
        csv_row["EncounterClass"] = map_encounter_class(encounter_class)

    # Extract Code and Description from type
    encounter_types = fhir_resource.get("type", [])
    if encounter_types:
        first_type = encounter_types[0]
        csv_row["Code"] = extract_coding_code(first_type, "http://snomed.info/sct")
        csv_row["Description"] = extract_display_or_text(first_type)

    # Extract ReasonCode and ReasonDescription
    reason_codes = fhir_resource.get("reasonCode", [])
    if reason_codes:
        first_reason = reason_codes[0]
        csv_row["ReasonCode"] = extract_coding_code(
            first_reason, "http://snomed.info/sct"
        )
        csv_row["ReasonDescription"] = extract_display_or_text(first_reason)

    # Extract cost extensions
    csv_row["Base_Encounter_Cost"] = extract_extension_decimal(
        fhir_resource, "http://example.org/fhir/StructureDefinition/encounter-baseCost"
    )
    csv_row["Total_Claim_Cost"] = extract_extension_decimal(
        fhir_resource,
        "http://example.org/fhir/StructureDefinition/encounter-totalClaimCost",
    )
    csv_row["Payer_Coverage"] = extract_extension_decimal(
        fhir_resource,
        "http://example.org/fhir/StructureDefinition/encounter-payerCoverage",
    )

    # Extract Payer from extension
    csv_row["Payer"] = extract_extension_reference(
        fhir_resource, "http://example.org/fhir/StructureDefinition/encounter-payer"
    )

    return csv_row
