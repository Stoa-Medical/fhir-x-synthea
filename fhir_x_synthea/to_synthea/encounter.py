"""FHIR R4 Encounter → Synthea Encounter"""

import logging
from typing import Any

from fhir.resources.encounter import Encounter
from synthea_pydantic import Encounter as SyntheaEncounter

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_extension_decimal,
    extract_extension_reference,
    extract_reference_id,
    parse_datetime,
)

logger = logging.getLogger(__name__)


def _map_encounter_class(
    encounter_class: list[dict[str, Any]] | dict[str, Any] | None,
) -> str:
    """Map FHIR encounter class to Synthea string."""
    if not encounter_class:
        return ""

    # Handle list of CodeableConcepts (R4B format)
    if isinstance(encounter_class, list):
        if not encounter_class:
            return ""
        # Get first CodeableConcept
        first_class = encounter_class[0]
        codings = first_class.get("coding", [])
        if not codings:
            return ""
        # Get first Coding
        coding = codings[0] if codings else {}
        code = coding.get("code", "")
        system = coding.get("system", "")
        display = coding.get("display", "")
    else:
        # Handle dict (single Coding) for backwards compat
        code = encounter_class.get("code", "")
        system = encounter_class.get("system", "")
        display = encounter_class.get("display", "")

    # Check ActCode system
    if "v3-ActCode" in system or "terminology.hl7.org/CodeSystem/v3-ActCode" in system:
        code_map = {
            "AMB": "ambulatory",
            "EMER": "emergency",
            "IMP": "inpatient",
            "ACUTE": "inpatient",
        }
        return code_map.get(code, "")

    # Fallback to display
    if display:
        return display.lower()

    return ""


def convert(src: Encounter) -> SyntheaEncounter:
    """Convert FHIR R4 Encounter to Synthea Encounter.

    Args:
        src: FHIR R4 Encounter resource

    Returns:
        Synthea Encounter model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    # Convert to dict for extraction helpers
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract Id
    resource_id = fhir_resource.get("id", "")

    # Extract Start and Stop from actualPeriod (R4B) or period (R4)
    start = ""
    stop = ""
    period = fhir_resource.get("actualPeriod") or fhir_resource.get("period") or {}
    if period.get("start"):
        start = parse_datetime(period["start"])
    if period.get("end"):
        stop = parse_datetime(period["end"])

    # Extract Patient reference
    patient = ""
    subject = fhir_resource.get("subject")
    if subject:
        patient = extract_reference_id(subject)

    # Extract Organization reference
    organization = ""
    service_provider = fhir_resource.get("serviceProvider")
    if service_provider:
        organization = extract_reference_id(service_provider)

    # Extract Provider from participant (R4B uses 'actor' instead of 'individual')
    provider = ""
    participants = fhir_resource.get("participant", [])
    if participants:
        first_participant = participants[0]
        # R4B uses 'actor', R4 uses 'individual'
        actor = first_participant.get("actor") or first_participant.get("individual")
        if actor:
            provider = extract_reference_id(actor)

    # Log if multiple participants
    if len(participants) > 1:
        logger.warning(
            "Encounter %s has %d participants; only first preserved",
            src.id,
            len(participants),
        )

    # Extract EncounterClass (model_dump returns 'class', not 'class_fhir')
    encounter_class = ""
    class_obj = fhir_resource.get("class") or fhir_resource.get("class_fhir")
    if class_obj:
        encounter_class = _map_encounter_class(class_obj)

    # Extract Code and Description from type
    code = ""
    description = ""
    encounter_types = fhir_resource.get("type", [])
    if encounter_types:
        first_type = encounter_types[0]
        code = extract_coding_code(
            first_type, preferred_system="http://snomed.info/sct"
        )
        description = extract_display_or_text(first_type)

    # Extract ReasonCode and ReasonDescription
    reason_code = ""
    reason_description = ""
    reason_codes = fhir_resource.get("reasonCode", [])
    if reason_codes:
        first_reason = reason_codes[0]
        reason_code = extract_coding_code(
            first_reason, preferred_system="http://snomed.info/sct"
        )
        reason_description = extract_display_or_text(first_reason)

    # Extract cost extensions
    base_encounter_cost = extract_extension_decimal(
        fhir_resource, "http://example.org/fhir/StructureDefinition/encounter-baseCost"
    )
    total_claim_cost = extract_extension_decimal(
        fhir_resource,
        "http://example.org/fhir/StructureDefinition/encounter-totalClaimCost",
    )
    payer_coverage = extract_extension_decimal(
        fhir_resource,
        "http://example.org/fhir/StructureDefinition/encounter-payerCoverage",
    )

    # Extract Payer from extension
    payer = extract_extension_reference(
        fhir_resource, "http://example.org/fhir/StructureDefinition/encounter-payer"
    )

    # Use lowercase field names (synthea_pydantic accepts both but normalizes to lowercase)
    # encounterclass is required and must be a valid literal value
    valid_classes = {
        "ambulatory",
        "emergency",
        "inpatient",
        "wellness",
        "urgentcare",
        "outpatient",
    }
    if encounter_class not in valid_classes:
        encounter_class = "ambulatory"  # Default

    return SyntheaEncounter(
        id=resource_id or None,
        start=start or None,
        stop=stop or None,
        patient=patient or None,
        organization=organization or None,
        provider=provider or None,
        payer=payer or None,
        encounterclass=encounter_class,
        code=code or "unknown",
        description=description or "Unknown",
        base_encounter_cost=base_encounter_cost or "0",
        total_claim_cost=total_claim_cost or "0",
        payer_coverage=payer_coverage or "0",
        reasoncode=reason_code or None,
        reasondescription=reason_description or None,
    )
