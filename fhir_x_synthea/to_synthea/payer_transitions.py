"""FHIR R4 Coverage → Synthea PayerTransition"""

import logging
from typing import Any

from fhir.resources.coverage import Coverage
from synthea_pydantic import PayerTransition

from ..synthea_csv_lib import (
    extract_extension_string,
    extract_reference_id,
    extract_year,
)

logger = logging.getLogger(__name__)


def _map_relationship(relationship_obj: dict[str, Any] | None) -> str:
    """Map FHIR relationship to Synthea ownership."""
    if not relationship_obj:
        return ""

    # Check codings first
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

    # Check text (for Guardian)
    text = relationship_obj.get("text", "")
    if text == "Guardian":
        return "Guardian"

    return ""


def convert(src: Coverage) -> PayerTransition:
    """Convert FHIR R4 Coverage to Synthea PayerTransition.

    Args:
        src: FHIR R4 Coverage resource

    Returns:
        Synthea PayerTransition model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract Patient reference
    patient = ""
    beneficiary = fhir_resource.get("beneficiary")
    if beneficiary:
        patient = extract_reference_id(beneficiary)

    # Extract Member ID (prefer subscriberId, fallback to identifier)
    member_id = fhir_resource.get("subscriberId", "")
    if not member_id:
        identifiers = fhir_resource.get("identifier", [])
        if identifiers:
            member_id = identifiers[0].get("value", "")

    # Extract Start_Year and End_Year from period
    start_year = None
    end_year = None
    period = fhir_resource.get("period", {})
    start = period.get("start")
    if start:
        year_str = extract_year(start)
        if year_str:
            start_year = int(year_str)

    end = period.get("end")
    if end:
        year_str = extract_year(end)
        if year_str:
            end_year = int(year_str)

    # Extract Payer references (R4B uses insurer, R4 uses payor)
    payer = ""
    secondary_payer = ""

    # Try insurer first (R4B)
    insurer = fhir_resource.get("insurer")
    if insurer:
        payer = extract_reference_id(insurer)
    else:
        # Fallback to payor (R4)
        payors = fhir_resource.get("payor", [])
        if len(payors) > 0:
            payer = extract_reference_id(payors[0])

        if len(payors) > 1:
            secondary_payer = extract_reference_id(payors[1])

    # Check for secondary payer in extension
    if not secondary_payer:
        secondary_payer = extract_extension_string(
            fhir_resource,
            "http://synthea.mitre.org/fhir/StructureDefinition/secondary-payer",
        )
        if not secondary_payer:
            # Try valueReference
            extensions = fhir_resource.get("extension", [])
            for ext in extensions:
                if (
                    ext.get("url")
                    == "http://synthea.mitre.org/fhir/StructureDefinition/secondary-payer"
                ):
                    value_ref = ext.get("valueReference")
                    if value_ref:
                        secondary_payer = extract_reference_id(value_ref)
                        break

    # Extract Ownership (relationship)
    ownership = ""
    relationship = fhir_resource.get("relationship")
    if relationship:
        ownership = _map_relationship(relationship)

    # Extract Owner Name from extension
    owner_name = extract_extension_string(
        fhir_resource,
        "http://synthea.mitre.org/fhir/StructureDefinition/owner-name",
    )

    return PayerTransition(
        patient=patient or None,
        memberid=member_id or None,
        start_year=start_year,
        end_year=end_year,
        payer=payer or None,
        secondary_payer=secondary_payer or None,
        ownership=ownership or None,
        owner_name=owner_name or None,
    )
