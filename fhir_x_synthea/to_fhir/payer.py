"""Synthea Payer → FHIR R4 Organization (Insurance)"""

from fhir.resources.organization import Organization
from synthea_pydantic import Payer as SyntheaPayer

from ..chidian_ext import grab, mapper, to_dict
from ..utils import split_phones


def _address(d: dict):
    """Build FHIR Address from source dict."""
    address = grab(d, "address")
    city = grab(d, "city")
    state = grab(d, "state_headquartered")
    zip_code = grab(d, "zip")

    if not any([address, city, state, zip_code]):
        return None

    return {
        "line": [address] if address else None,
        "city": city,
        "state": state,
        "postalCode": zip_code,
    }


def _telecom(phone_str: str | None):
    """Build telecom array from phone string."""
    phones = split_phones(phone_str)
    if not phones:
        return None
    return [{"system": "phone", "value": phone} for phone in phones]


def _stats_extension(d: dict):
    """Build payer stats extension from source dict."""
    stats_fields = [
        ("amountCovered", "amount_covered", "valueDecimal"),
        ("amountUncovered", "amount_uncovered", "valueDecimal"),
        ("revenue", "revenue", "valueDecimal"),
        ("coveredEncounters", "covered_encounters", "valueInteger"),
        ("uncoveredEncounters", "uncovered_encounters", "valueInteger"),
        ("coveredMedications", "covered_medications", "valueInteger"),
        ("uncoveredMedications", "uncovered_medications", "valueInteger"),
        ("coveredProcedures", "covered_procedures", "valueInteger"),
        ("uncoveredProcedures", "uncovered_procedures", "valueInteger"),
        ("coveredImmunizations", "covered_immunizations", "valueInteger"),
        ("uncoveredImmunizations", "uncovered_immunizations", "valueInteger"),
        ("uniqueCustomers", "unique_customers", "valueInteger"),
        ("qolsAvg", "qols_avg", "valueDecimal"),
        ("memberMonths", "member_months", "valueInteger"),
    ]

    nested = []
    for field_name, src_key, value_type in stats_fields:
        value = grab(d, src_key)
        if value is not None:
            sub_ext: dict = {"url": field_name}
            if value_type == "valueDecimal":
                sub_ext["valueDecimal"] = float(value)
            else:
                sub_ext["valueInteger"] = int(value)
            nested.append(sub_ext)

    if not nested:
        return None

    return {
        "url": "http://synthea.mitre.org/fhir/StructureDefinition/payer-stats",
        "extension": nested,
    }


@mapper
def _to_fhir_payer(d: dict):
    """Core mapping from dict to FHIR Organization (insurance) structure."""
    addr = _address(d)
    stats = _stats_extension(d)

    return {
        "resourceType": "Organization",
        "id": grab(d, "id"),
        "name": grab(d, "name"),
        "type": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                        "code": "ins",
                        "display": "Insurance Company",
                    }
                ]
            }
        ],
        "address": [addr] if addr else None,
        "telecom": _telecom(grab(d, "phone")),
        "extension": [stats] if stats else None,
    }


def convert(src: SyntheaPayer) -> Organization:
    """Convert Synthea Payer to FHIR R4 Organization (insurance type).

    Args:
        src: Synthea Payer model

    Returns:
        FHIR R4 Organization resource with insurance type
    """
    return Organization(**_to_fhir_payer(to_dict(src)))
