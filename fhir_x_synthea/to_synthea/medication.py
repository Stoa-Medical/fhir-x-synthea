"""
Mapping function for converting FHIR MedicationRequest resources to Synthea medications.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_extension_decimal,
    extract_reference_id,
    parse_datetime,
)


def map_fhir_medication_request_to_csv(fhir_resource: dict[str, Any]) -> dict[str, Any]:
    """
    Map a FHIR R4 MedicationRequest resource to a Synthea medications.csv row.

    Args:
        fhir_resource: Dictionary representing a FHIR MedicationRequest resource

    Returns:
        Dictionary with CSV column names as keys (Start, Stop, Patient, etc.)
    """

    # Initialize CSV row
    csv_row: dict[str, str] = {
        "Start": "",
        "Stop": "",
        "Patient": "",
        "Encounter": "",
        "Payer": "",
        "Code": "",
        "Description": "",
        "Dispenses": "",
        "ReasonCode": "",
        "ReasonDescription": "",
        "Base_Cost": "",
        "Payer_Coverage": "",
        "TotalCost": "",
    }

    # Extract Start (prefer authoredOn, fallback to occurrencePeriod.start)
    authored_on = fhir_resource.get("authoredOn")
    occurrence_period = fhir_resource.get("occurrencePeriod", {})

    if authored_on:
        csv_row["Start"] = parse_datetime(authored_on)
    elif occurrence_period.get("start"):
        csv_row["Start"] = parse_datetime(occurrence_period["start"])

    # Extract Stop from occurrencePeriod.end
    if occurrence_period.get("end"):
        csv_row["Stop"] = parse_datetime(occurrence_period["end"])

    # Extract Patient reference
    subject = fhir_resource.get("subject")
    if subject:
        csv_row["Patient"] = extract_reference_id(subject)

    # Extract Encounter reference
    encounter = fhir_resource.get("encounter")
    if encounter:
        csv_row["Encounter"] = extract_reference_id(encounter)

    # Extract Payer from insurance (Coverage or Organization)
    insurance = fhir_resource.get("insurance", [])
    if insurance:
        first_insurance = insurance[0]
        coverage = first_insurance.get("coverage")
        if coverage:
            csv_row["Payer"] = extract_reference_id(coverage)

    # Extract Code and Description from medicationCodeableConcept (RxNorm)
    medication_code = fhir_resource.get("medicationCodeableConcept")
    if medication_code:
        csv_row["Code"] = extract_coding_code(
            medication_code, "http://www.nlm.nih.gov/research/umls/rxnorm"
        )
        csv_row["Description"] = extract_display_or_text(medication_code)

    # Extract Dispenses
    dispense_request = fhir_resource.get("dispenseRequest", {})
    repeats_allowed = dispense_request.get("numberOfRepeatsAllowed")
    if repeats_allowed is not None:
        csv_row["Dispenses"] = str(repeats_allowed)

    # Extract ReasonCode and ReasonDescription
    reason_codes = fhir_resource.get("reasonCode", [])
    if reason_codes:
        first_reason = reason_codes[0]
        csv_row["ReasonCode"] = extract_coding_code(
            first_reason, "http://snomed.info/sct"
        )
        csv_row["ReasonDescription"] = extract_display_or_text(first_reason)

    # Extract financial extensions
    csv_row["Base_Cost"] = extract_extension_decimal(
        fhir_resource, "http://synthea.org/fhir/StructureDefinition/medication-baseCost"
    )
    csv_row["Payer_Coverage"] = extract_extension_decimal(
        fhir_resource,
        "http://synthea.org/fhir/StructureDefinition/medication-payerCoverage",
    )
    csv_row["TotalCost"] = extract_extension_decimal(
        fhir_resource,
        "http://synthea.org/fhir/StructureDefinition/medication-totalCost",
    )

    return csv_row
