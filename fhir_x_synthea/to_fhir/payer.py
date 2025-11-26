"""
Mapping function for converting Synthea payers.csv rows to FHIR Organization resources.
"""

import re
from typing import Any


def map_payer(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea payers.csv row to a FHIR R4 Organization resource representing a payer.

    Args:
        csv_row: Dictionary with keys like Id, Name, Ownership, Address, City,
                State_Headquartered, Zip, Phone, Amount_Covered, Amount_Uncovered,
                Revenue, Covered_Encounters, Uncovered_Encounters, etc.

    Returns:
        Dictionary representing a FHIR Organization resource
    """

    # Helper to split phone numbers
    def split_phones(phone_str: str | None) -> list[str]:
        if not phone_str or phone_str.strip() == "":
            return []
        phones = re.split(r"[,;/|]", phone_str)
        return [p.strip() for p in phones if p.strip()]

    # Extract and process fields
    payer_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    name = csv_row.get("Name", "").strip() if csv_row.get("Name") else ""
    ownership = csv_row.get("Ownership", "").strip() if csv_row.get("Ownership") else ""
    address = csv_row.get("Address", "").strip() if csv_row.get("Address") else ""
    city = csv_row.get("City", "").strip() if csv_row.get("City") else ""
    state = (
        csv_row.get("State_Headquartered", "").strip()
        if csv_row.get("State_Headquartered")
        else ""
    )
    zip_code = csv_row.get("Zip", "").strip() if csv_row.get("Zip") else ""
    phone_str = csv_row.get("Phone", "").strip() if csv_row.get("Phone") else ""

    # Extract all stats fields
    amount_covered_str = (
        csv_row.get("Amount_Covered", "").strip()
        if csv_row.get("Amount_Covered")
        else ""
    )
    amount_uncovered_str = (
        csv_row.get("Amount_Uncovered", "").strip()
        if csv_row.get("Amount_Uncovered")
        else ""
    )
    revenue_str = csv_row.get("Revenue", "").strip() if csv_row.get("Revenue") else ""
    covered_encounters_str = (
        csv_row.get("Covered_Encounters", "").strip()
        if csv_row.get("Covered_Encounters")
        else ""
    )
    uncovered_encounters_str = (
        csv_row.get("Uncovered_Encounters", "").strip()
        if csv_row.get("Uncovered_Encounters")
        else ""
    )
    covered_medications_str = (
        csv_row.get("Covered_Medications", "").strip()
        if csv_row.get("Covered_Medications")
        else ""
    )
    uncovered_medications_str = (
        csv_row.get("Uncovered_Medications", "").strip()
        if csv_row.get("Uncovered_Medications")
        else ""
    )
    covered_procedures_str = (
        csv_row.get("Covered_Procedures", "").strip()
        if csv_row.get("Covered_Procedures")
        else ""
    )
    uncovered_procedures_str = (
        csv_row.get("Uncovered_Procedures", "").strip()
        if csv_row.get("Uncovered_Procedures")
        else ""
    )
    covered_immunizations_str = (
        csv_row.get("Covered_Immunizations", "").strip()
        if csv_row.get("Covered_Immunizations")
        else ""
    )
    uncovered_immunizations_str = (
        csv_row.get("Uncovered_Immunizations", "").strip()
        if csv_row.get("Uncovered_Immunizations")
        else ""
    )
    unique_customers_str = (
        csv_row.get("Unique_Customers", "").strip()
        if csv_row.get("Unique_Customers")
        else ""
    )
    qols_avg_str = (
        csv_row.get("QOLS_Avg", "").strip() if csv_row.get("QOLS_Avg") else ""
    )
    member_months_str = (
        csv_row.get("Member_Months", "").strip() if csv_row.get("Member_Months") else ""
    )

    # Parse numeric stats fields
    def parse_decimal(value_str: str) -> float | None:
        if not value_str:
            return None
        try:
            return float(value_str)
        except (ValueError, TypeError):
            return None

    def parse_integer(value_str: str) -> int | None:
        if not value_str:
            return None
        try:
            return int(value_str)
        except (ValueError, TypeError):
            return None

    amount_covered = parse_decimal(amount_covered_str)
    amount_uncovered = parse_decimal(amount_uncovered_str)
    revenue = parse_decimal(revenue_str)
    covered_encounters = parse_integer(covered_encounters_str)
    uncovered_encounters = parse_integer(uncovered_encounters_str)
    covered_medications = parse_integer(covered_medications_str)
    uncovered_medications = parse_integer(uncovered_medications_str)
    covered_procedures = parse_integer(covered_procedures_str)
    uncovered_procedures = parse_integer(uncovered_procedures_str)
    covered_immunizations = parse_integer(covered_immunizations_str)
    uncovered_immunizations = parse_integer(uncovered_immunizations_str)
    unique_customers = parse_integer(unique_customers_str)
    qols_avg = parse_decimal(qols_avg_str)
    member_months = parse_integer(member_months_str)

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Organization",
        "id": payer_id if payer_id else "",
    }

    # Set name (required)
    if name:
        resource["name"] = name

    # Set type (Insurance Company)
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

    # Set telecom (phone numbers)
    phones = split_phones(phone_str)
    if phones:
        resource["telecom"] = [{"system": "phone", "value": phone} for phone in phones]

    # Set extensions (ownership and payer stats)
    extensions = []

    # Ownership extension
    if ownership:
        extensions.append(
            {
                "url": "http://synthea.mitre.org/fhir/StructureDefinition/payer-ownership",
                "valueCode": ownership.lower().strip(),
            }
        )

    # Payer stats extension with nested sub-extensions
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

    stats_extension: dict[str, Any] = {
        "url": "http://synthea.mitre.org/fhir/StructureDefinition/payer-stats",
        "extension": [],
    }

    for field_name, value, value_type in stats_fields:
        if value is not None:
            sub_ext: dict[str, Any] = {"url": field_name}
            if value_type == "valueDecimal":
                sub_ext["valueDecimal"] = value
            elif value_type == "valueInteger":
                sub_ext["valueInteger"] = value
            stats_extension["extension"].append(sub_ext)

    if stats_extension["extension"]:
        extensions.append(stats_extension)

    if extensions:
        resource["extension"] = extensions

    return resource
