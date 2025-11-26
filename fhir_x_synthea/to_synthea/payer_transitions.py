"""FHIR R4 Coverage → Synthea PayerTransition"""

import logging

from fhir.resources.coverage import Coverage
from synthea_pydantic import PayerTransition

from ..chidian_ext import (
    extract_ext,
    extract_ext_ref,
    extract_ref_id,
    grab,
    mapper,
    to_dict,
)

logger = logging.getLogger(__name__)


def _map_relationship(relationship_obj: dict | None) -> str:
    """Map FHIR relationship to Synthea ownership."""
    if not relationship_obj:
        return ""

    codings = relationship_obj.get("coding", [])
    for coding in codings:
        code = coding.get("code", "")
        if code == "self":
            return "Self"
        elif code == "spouse":
            return "Spouse"
        elif code == "child":
            return "Child"
        elif code == "parent":
            return "Guardian"

    text = relationship_obj.get("text", "")
    if text == "Guardian":
        return "Guardian"

    return ""


def _extract_year(date_str: str | None) -> int | None:
    """Extract year from date string."""
    if not date_str:
        return None
    try:
        # Handle YYYY-MM-DD format
        if len(date_str) >= 4:
            return int(date_str[:4])
    except (ValueError, TypeError):
        pass
    return None


def _extract_secondary_payer(d: dict) -> str:
    """Extract secondary payer from payor list or extension."""
    # Check payor list (R4)
    payors = grab(d, "payor") or []
    if len(payors) > 1:
        ref = payors[1].get("reference", "") if isinstance(payors[1], dict) else ""
        if "/" in ref:
            return ref.split("/")[-1]
        return ref

    # Check extension
    return extract_ext_ref(
        d, "http://synthea.mitre.org/fhir/StructureDefinition/secondary-payer"
    )


@mapper(remove_empty=False)
def _to_synthea_payer_transition(d: dict):
    """Core mapping from dict to Synthea PayerTransition structure."""
    # Extract patient
    patient = extract_ref_id(d, "beneficiary")

    # Extract member ID (prefer subscriberId, fallback to identifier)
    member_id = grab(d, "subscriberId") or ""
    if not member_id:
        identifiers = grab(d, "identifier") or []
        if identifiers:
            member_id = identifiers[0].get("value", "")

    # Extract period years
    period = grab(d, "period") or {}
    start_year = _extract_year(period.get("start"))
    end_year = _extract_year(period.get("end"))

    # Extract payer (R4B uses insurer, R4 uses payor)
    payer = extract_ref_id(d, "insurer")
    if not payer:
        payors = grab(d, "payor") or []
        if payors:
            ref = payors[0].get("reference", "") if isinstance(payors[0], dict) else ""
            if "/" in ref:
                payer = ref.split("/")[-1]
            else:
                payer = ref

    # Extract secondary payer
    secondary_payer = _extract_secondary_payer(d)

    # Extract ownership
    ownership = _map_relationship(grab(d, "relationship"))

    # Extract owner name
    owner_name = extract_ext(
        d,
        "http://synthea.mitre.org/fhir/StructureDefinition/owner-name",
        "valueString",
        "",
    )

    return {
        "patient": patient or None,
        "memberid": member_id or None,
        "start_year": start_year,
        "end_year": end_year,
        "payer": payer or None,
        "secondary_payer": secondary_payer or None,
        "ownership": ownership or None,
        "owner_name": owner_name or None,
    }


def convert(src: Coverage) -> PayerTransition:
    """Convert FHIR R4 Coverage to Synthea PayerTransition.

    Args:
        src: FHIR R4 Coverage resource

    Returns:
        Synthea PayerTransition model
    """
    return PayerTransition(**_to_synthea_payer_transition(to_dict(src)))
