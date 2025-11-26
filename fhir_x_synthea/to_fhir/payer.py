"""Synthea Payer → FHIR R4 Organization (Insurance)"""

from typing import Any

from fhir.resources.organization import Organization
from synthea_pydantic import Payer as SyntheaPayer

from ..utils import split_phones, to_str


def convert(src: SyntheaPayer) -> Organization:
    """Convert Synthea Payer to FHIR R4 Organization (insurance type).

    Args:
        src: Synthea Payer model

    Returns:
        FHIR R4 Organization resource with insurance type
    """
    d = src.model_dump()

    # Extract fields
    payer_id = to_str(d.get("id"))
    name = to_str(d.get("name"))
    address = to_str(d.get("address"))
    city = to_str(d.get("city"))
    state = to_str(d.get("state_headquartered"))
    zip_code = to_str(d.get("zip"))
    phone_str = to_str(d.get("phone"))

    # Handle numeric stats fields
    amount_covered = d.get("amount_covered")
    amount_uncovered = d.get("amount_uncovered")
    revenue = d.get("revenue")
    covered_encounters = d.get("covered_encounters")
    uncovered_encounters = d.get("uncovered_encounters")
    covered_medications = d.get("covered_medications")
    uncovered_medications = d.get("uncovered_medications")
    covered_procedures = d.get("covered_procedures")
    uncovered_procedures = d.get("uncovered_procedures")
    covered_immunizations = d.get("covered_immunizations")
    uncovered_immunizations = d.get("uncovered_immunizations")
    unique_customers = d.get("unique_customers")
    qols_avg = d.get("qols_avg")
    member_months = d.get("member_months")

    # Build resource
    resource: dict[str, Any] = {"resourceType": "Organization"}

    if payer_id:
        resource["id"] = payer_id

    if name:
        resource["name"] = name

    # Set type as insurance company
    resource["type"] = [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                    "code": "ins",
                    "display": "Insurance Company",
                }
            ]
        }
    ]

    # Set address
    if address or city or state or zip_code:
        address_obj: dict[str, Any] = {}
        if address:
            address_obj["line"] = [address]
        if city:
            address_obj["city"] = city
        if state:
            address_obj["state"] = state
        if zip_code:
            address_obj["postalCode"] = zip_code
        resource["address"] = [address_obj]

    # Set telecom
    phones = split_phones(phone_str)
    if phones:
        resource["telecom"] = [{"system": "phone", "value": phone} for phone in phones]

    # Build stats extension
    extensions = []
    stats_fields = [
        ("amountCovered", amount_covered, "valueDecimal"),
        ("amountUncovered", amount_uncovered, "valueDecimal"),
        ("revenue", revenue, "valueDecimal"),
        ("coveredEncounters", covered_encounters, "valueInteger"),
        ("uncoveredEncounters", uncovered_encounters, "valueInteger"),
        ("coveredMedications", covered_medications, "valueInteger"),
        ("uncoveredMedications", uncovered_medications, "valueInteger"),
        ("coveredProcedures", covered_procedures, "valueInteger"),
        ("uncoveredProcedures", uncovered_procedures, "valueInteger"),
        ("coveredImmunizations", covered_immunizations, "valueInteger"),
        ("uncoveredImmunizations", uncovered_immunizations, "valueInteger"),
        ("uniqueCustomers", unique_customers, "valueInteger"),
        ("qolsAvg", qols_avg, "valueDecimal"),
        ("memberMonths", member_months, "valueInteger"),
    ]

    stats_ext: dict[str, Any] = {
        "url": "http://synthea.mitre.org/fhir/StructureDefinition/payer-stats",
        "extension": [],
    }

    for field_name, value, value_type in stats_fields:
        if value is not None:
            sub_ext: dict[str, Any] = {"url": field_name}
            if value_type == "valueDecimal":
                sub_ext["valueDecimal"] = float(value)
            elif value_type == "valueInteger":
                sub_ext["valueInteger"] = int(value)
            stats_ext["extension"].append(sub_ext)

    if stats_ext["extension"]:
        extensions.append(stats_ext)

    if extensions:
        resource["extension"] = extensions

    return Organization(**resource)
