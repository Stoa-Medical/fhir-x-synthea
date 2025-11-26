"""FHIR R4 MedicationRequest → Synthea Medication"""

import logging
from datetime import date
from decimal import Decimal

from fhir.resources.medicationrequest import MedicationRequest
from synthea_pydantic import Medication as SyntheaMedication

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_extension_decimal,
    extract_reference_id,
    parse_datetime_to_date,
)

logger = logging.getLogger(__name__)


def convert(src: MedicationRequest) -> SyntheaMedication:
    """Convert FHIR R4 MedicationRequest to Synthea Medication.

    Args:
        src: FHIR R4 MedicationRequest resource

    Returns:
        Synthea Medication model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract Start (prefer authoredOn, fallback to occurrencePeriod.start)
    start = None
    authored_on = fhir_resource.get("authoredOn")
    occurrence_period = fhir_resource.get("occurrencePeriod", {})

    if authored_on:
        parsed = parse_datetime_to_date(authored_on)
        if parsed:
            start = date.fromisoformat(parsed)
    elif occurrence_period.get("start"):
        parsed = parse_datetime_to_date(occurrence_period["start"])
        if parsed:
            start = date.fromisoformat(parsed)

    # Extract Stop from occurrencePeriod.end
    stop = None
    if occurrence_period.get("end"):
        parsed = parse_datetime_to_date(occurrence_period["end"])
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

    # Extract Payer from insurance (Coverage or Organization)
    payer = ""
    insurance = fhir_resource.get("insurance", [])
    if insurance:
        first_insurance = insurance[0]
        coverage = (
            first_insurance.get("coverage")
            if isinstance(first_insurance, dict)
            else first_insurance
        )
        if coverage:
            payer = extract_reference_id(coverage)

    # Extract Code and Description from medication (R4B uses CodeableReference)
    code = ""
    description = ""
    medication = fhir_resource.get("medication")
    if medication:
        # R4B: medication is CodeableReference with concept or reference
        if "concept" in medication:
            medication_code = medication["concept"]
            code = extract_coding_code(
                medication_code,
                preferred_system="http://www.nlm.nih.gov/research/umls/rxnorm",
            )
            description = extract_display_or_text(medication_code)
        elif "reference" in medication:
            # Reference to Medication resource
            pass
    else:
        # R4: medicationCodeableConcept
        medication_code = fhir_resource.get("medicationCodeableConcept")
        if medication_code:
            code = extract_coding_code(
                medication_code,
                preferred_system="http://www.nlm.nih.gov/research/umls/rxnorm",
            )
            description = extract_display_or_text(medication_code)

    # Extract Dispenses
    dispenses = None
    dispense_request = fhir_resource.get("dispenseRequest", {})
    repeats_allowed = dispense_request.get("numberOfRepeatsAllowed")
    if repeats_allowed is not None:
        dispenses = int(repeats_allowed)

    # Extract ReasonCode and ReasonDescription
    reason_code = ""
    reason_description = ""

    # R4B uses reason with CodeableReference
    reasons = fhir_resource.get("reason", [])
    if reasons:
        first_reason = reasons[0]
        if "concept" in first_reason:
            concept = first_reason["concept"]
            reason_code = extract_coding_code(
                concept, preferred_system="http://snomed.info/sct"
            )
            reason_description = extract_display_or_text(concept)
    else:
        # R4: reasonCode
        reason_codes = fhir_resource.get("reasonCode", [])
        if reason_codes:
            first_reason = reason_codes[0]
            reason_code = extract_coding_code(
                first_reason, preferred_system="http://snomed.info/sct"
            )
            reason_description = extract_display_or_text(first_reason)

    # Extract financial extensions
    base_cost_str = extract_extension_decimal(
        fhir_resource, "http://synthea.org/fhir/StructureDefinition/medication-baseCost"
    )
    payer_coverage_str = extract_extension_decimal(
        fhir_resource,
        "http://synthea.org/fhir/StructureDefinition/medication-payerCoverage",
    )
    total_cost_str = extract_extension_decimal(
        fhir_resource,
        "http://synthea.org/fhir/StructureDefinition/medication-totalCost",
    )

    base_cost = Decimal(base_cost_str) if base_cost_str else None
    payer_coverage = Decimal(payer_coverage_str) if payer_coverage_str else None
    total_cost = Decimal(total_cost_str) if total_cost_str else None

    return SyntheaMedication(
        start=start,
        stop=stop,
        patient=patient or None,
        payer=payer or None,
        encounter=encounter or None,
        code=code or "unknown",
        description=description or "Unknown medication",
        base_cost=base_cost,
        payer_coverage=payer_coverage,
        dispenses=dispenses,
        totalcost=total_cost,
        reasoncode=reason_code or None,
        reasondescription=reason_description or None,
    )
