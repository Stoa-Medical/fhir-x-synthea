"""FHIR R4 Encounter → Synthea Encounter"""

import logging

from fhir.resources.encounter import Encounter
from synthea_pydantic import Encounter as SyntheaEncounter

from ..chidian_ext import (
    extract_code,
    extract_display,
    extract_ext,
    extract_ext_ref,
    extract_ref_id,
    grab,
    mapper,
    parse_dt,
    to_dict,
)
from ..synthea_lib import map_encounter_class, validate_encounter_class

logger = logging.getLogger(__name__)


@mapper(remove_empty=False)
def _to_synthea_encounter(d: dict):
    """Core mapping from dict to Synthea Encounter structure."""
    # Extract period
    period = grab(d, "actualPeriod") or grab(d, "period") or {}
    start = parse_dt({"p": period.get("start")}, "p") if period.get("start") else None
    stop = parse_dt({"p": period.get("end")}, "p") if period.get("end") else None

    # Extract patient
    patient = extract_ref_id(d, "subject")

    # Extract organization
    organization = extract_ref_id(d, "serviceProvider")

    # Extract provider from participant
    provider = ""
    participants = grab(d, "participant") or []
    if participants:
        first_participant = participants[0]
        actor = first_participant.get("actor") or first_participant.get("individual")
        if actor:
            provider = (
                actor.get("reference", "").split("/")[-1]
                if "/" in actor.get("reference", "")
                else actor.get("reference", "")
            )

    # Log if multiple participants
    if len(participants) > 1:
        logger.warning(
            "Encounter has %d participants; only first preserved", len(participants)
        )

    # Extract encounter class
    class_obj = grab(d, "class") or grab(d, "class_fhir")
    encounter_class = validate_encounter_class(map_encounter_class(class_obj))

    # Extract code and description from type
    code = extract_code(d, "type[0]", system="http://snomed.info/sct") or "unknown"
    description = extract_display(d, "type[0]") or "Unknown"

    # Extract reason
    reason_code = extract_code(d, "reasonCode[0]", system="http://snomed.info/sct")
    reason_description = extract_display(d, "reasonCode[0]")

    # Extract cost extensions
    base_cost = extract_ext(
        d,
        "http://example.org/fhir/StructureDefinition/encounter-baseCost",
        "valueDecimal",
        "0",
    )
    total_cost = extract_ext(
        d,
        "http://example.org/fhir/StructureDefinition/encounter-totalClaimCost",
        "valueDecimal",
        "0",
    )
    payer_coverage = extract_ext(
        d,
        "http://example.org/fhir/StructureDefinition/encounter-payerCoverage",
        "valueDecimal",
        "0",
    )

    # Extract payer
    payer = extract_ext_ref(
        d, "http://example.org/fhir/StructureDefinition/encounter-payer"
    )

    return {
        "id": grab(d, "id") or None,
        "start": start or None,
        "stop": stop or None,
        "patient": patient or None,
        "organization": organization or None,
        "provider": provider or None,
        "payer": payer or None,
        "encounterclass": encounter_class,
        "code": code,
        "description": description,
        "base_encounter_cost": str(base_cost),
        "total_claim_cost": str(total_cost),
        "payer_coverage": str(payer_coverage),
        "reasoncode": reason_code or None,
        "reasondescription": reason_description or None,
    }


def convert(src: Encounter) -> SyntheaEncounter:
    """Convert FHIR R4 Encounter to Synthea Encounter.

    Args:
        src: FHIR R4 Encounter resource

    Returns:
        Synthea Encounter model
    """
    return SyntheaEncounter(**_to_synthea_encounter(to_dict(src)))
