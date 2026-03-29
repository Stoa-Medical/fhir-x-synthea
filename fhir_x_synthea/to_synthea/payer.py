"""FHIR R4 Organization (Payer) → Synthea Payer"""

import logging

from fhir.resources.organization import Organization
from synthea_pydantic import Payer as SyntheaPayer

from ..chidian_ext import extract_nested_ext, grab, mapper, to_dict
from ..synthea_lib import to_decimal

logger = logging.getLogger(__name__)


def _extract_phones(d: dict) -> str:
    """Extract phone numbers and join with semicolon."""
    telecoms = grab(d, "telecom") or []
    phones = [
        contact.get("value", "")
        for contact in telecoms
        if contact.get("system") == "phone" and contact.get("value")
    ]
    return "; ".join(phones)


@mapper(remove_empty=False)
def _to_synthea_payer(d: dict):
    """Core mapping from dict to Synthea Payer structure."""
    addresses = grab(d, "address") or []
    first_address = addresses[0] if addresses else {}

    lines = first_address.get("line", [])
    address = lines[0] if lines else ""

    # Extract payer stats from extension
    stats_url = "http://synthea.mitre.org/fhir/StructureDefinition/payer-stats"

    amount_covered = extract_nested_ext(
        d, stats_url, "amountCovered", "valueDecimal", ""
    )
    amount_uncovered = extract_nested_ext(
        d, stats_url, "amountUncovered", "valueDecimal", ""
    )
    revenue = extract_nested_ext(d, stats_url, "revenue", "valueDecimal", "")
    covered_encounters = extract_nested_ext(
        d, stats_url, "coveredEncounters", "valueInteger", ""
    )
    uncovered_encounters = extract_nested_ext(
        d, stats_url, "uncoveredEncounters", "valueInteger", ""
    )
    covered_medications = extract_nested_ext(
        d, stats_url, "coveredMedications", "valueInteger", ""
    )
    uncovered_medications = extract_nested_ext(
        d, stats_url, "uncoveredMedications", "valueInteger", ""
    )
    covered_procedures = extract_nested_ext(
        d, stats_url, "coveredProcedures", "valueInteger", ""
    )
    uncovered_procedures = extract_nested_ext(
        d, stats_url, "uncoveredProcedures", "valueInteger", ""
    )
    covered_immunizations = extract_nested_ext(
        d, stats_url, "coveredImmunizations", "valueInteger", ""
    )
    uncovered_immunizations = extract_nested_ext(
        d, stats_url, "uncoveredImmunizations", "valueInteger", ""
    )
    unique_customers = extract_nested_ext(
        d, stats_url, "uniqueCustomers", "valueInteger", ""
    )
    qols_avg = extract_nested_ext(d, stats_url, "qolsAvg", "valueDecimal", "")
    member_months = extract_nested_ext(d, stats_url, "memberMonths", "valueInteger", "")

    return {
        "id": grab(d, "id") or None,
        "name": grab(d, "name") or "Unknown Payer",
        "address": address or None,
        "city": first_address.get("city") or None,
        "state_headquartered": first_address.get("state") or None,
        "zip": first_address.get("postalCode") or None,
        "phone": _extract_phones(d) or None,
        "amount_covered": to_decimal(amount_covered) if amount_covered else None,
        "amount_uncovered": to_decimal(amount_uncovered) if amount_uncovered else None,
        "revenue": to_decimal(revenue) if revenue else None,
        "covered_encounters": int(covered_encounters) if covered_encounters else None,
        "uncovered_encounters": int(uncovered_encounters)
        if uncovered_encounters
        else None,
        "covered_medications": int(covered_medications)
        if covered_medications
        else None,
        "uncovered_medications": int(uncovered_medications)
        if uncovered_medications
        else None,
        "covered_procedures": int(covered_procedures) if covered_procedures else None,
        "uncovered_procedures": int(uncovered_procedures)
        if uncovered_procedures
        else None,
        "covered_immunizations": int(covered_immunizations)
        if covered_immunizations
        else None,
        "uncovered_immunizations": int(uncovered_immunizations)
        if uncovered_immunizations
        else None,
        "unique_customers": int(unique_customers) if unique_customers else None,
        "qols_avg": to_decimal(qols_avg) if qols_avg else None,
        "member_months": int(member_months) if member_months else None,
    }


def convert(src: Organization) -> SyntheaPayer:
    """Convert FHIR R4 Organization (payer type) to Synthea Payer.

    Args:
        src: FHIR R4 Organization resource

    Returns:
        Synthea Payer model
    """
    return SyntheaPayer(**_to_synthea_payer(to_dict(src)))
