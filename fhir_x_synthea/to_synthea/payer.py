"""FHIR R4 Organization (Payer) → Synthea Payer"""

import logging
from decimal import Decimal
from typing import Any

from fhir.resources.organization import Organization
from synthea_pydantic import Payer as SyntheaPayer

from ..synthea_csv_lib import extract_nested_extension

logger = logging.getLogger(__name__)


def _extract_extension_code(fhir_resource: dict[str, Any], extension_url: str) -> str:
    """Extract code value from extension."""
    extensions = fhir_resource.get("extension", [])
    for ext in extensions:
        if ext.get("url") == extension_url:
            value = ext.get("valueCode")
            if value:
                return value
    return ""


def convert(src: Organization) -> SyntheaPayer:
    """Convert FHIR R4 Organization (payer type) to Synthea Payer.

    Args:
        src: FHIR R4 Organization resource

    Returns:
        Synthea Payer model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract Id
    resource_id = fhir_resource.get("id", "")

    # Extract Name
    name = fhir_resource.get("name", "")

    # Extract Address components
    address = ""
    city = ""
    state_headquartered = ""
    zip_code = ""

    addresses = fhir_resource.get("address", [])
    if addresses:
        first_address = addresses[0]

        lines = first_address.get("line", [])
        if lines:
            address = lines[0]

        city = first_address.get("city", "")
        state_headquartered = first_address.get("state", "")
        zip_code = first_address.get("postalCode", "")

    # Extract Phone numbers (join with ; )
    telecom = fhir_resource.get("telecom", [])
    phones = []
    for contact in telecom:
        if contact.get("system") == "phone":
            value = contact.get("value", "")
            if value:
                phones.append(value)

    phone = "; ".join(phones) if phones else ""

    # Extract payer-stats extension nested values
    stats_extension_url = (
        "http://synthea.mitre.org/fhir/StructureDefinition/payer-stats"
    )

    amount_covered_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "amountCovered", "valueDecimal"
    )
    amount_uncovered_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "amountUncovered", "valueDecimal"
    )
    revenue_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "revenue", "valueDecimal"
    )
    covered_encounters_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "coveredEncounters", "valueInteger"
    )
    uncovered_encounters_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "uncoveredEncounters", "valueInteger"
    )
    covered_medications_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "coveredMedications", "valueInteger"
    )
    uncovered_medications_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "uncoveredMedications", "valueInteger"
    )
    covered_procedures_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "coveredProcedures", "valueInteger"
    )
    uncovered_procedures_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "uncoveredProcedures", "valueInteger"
    )
    covered_immunizations_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "coveredImmunizations", "valueInteger"
    )
    uncovered_immunizations_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "uncoveredImmunizations", "valueInteger"
    )
    unique_customers_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "uniqueCustomers", "valueInteger"
    )
    qols_avg_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "qolsAvg", "valueDecimal"
    )
    member_months_str = extract_nested_extension(
        fhir_resource, stats_extension_url, "memberMonths", "valueInteger"
    )

    return SyntheaPayer(
        id=resource_id or None,
        name=name or "Unknown Payer",
        address=address or None,
        city=city or None,
        state_headquartered=state_headquartered or None,
        zip=zip_code or None,
        phone=phone or None,
        amount_covered=Decimal(amount_covered_str) if amount_covered_str else None,
        amount_uncovered=Decimal(amount_uncovered_str)
        if amount_uncovered_str
        else None,
        revenue=Decimal(revenue_str) if revenue_str else None,
        covered_encounters=int(covered_encounters_str)
        if covered_encounters_str
        else None,
        uncovered_encounters=int(uncovered_encounters_str)
        if uncovered_encounters_str
        else None,
        covered_medications=int(covered_medications_str)
        if covered_medications_str
        else None,
        uncovered_medications=int(uncovered_medications_str)
        if uncovered_medications_str
        else None,
        covered_procedures=int(covered_procedures_str)
        if covered_procedures_str
        else None,
        uncovered_procedures=int(uncovered_procedures_str)
        if uncovered_procedures_str
        else None,
        covered_immunizations=int(covered_immunizations_str)
        if covered_immunizations_str
        else None,
        uncovered_immunizations=int(uncovered_immunizations_str)
        if uncovered_immunizations_str
        else None,
        unique_customers=int(unique_customers_str) if unique_customers_str else None,
        qols_avg=Decimal(qols_avg_str) if qols_avg_str else None,
        member_months=int(member_months_str) if member_months_str else None,
    )
