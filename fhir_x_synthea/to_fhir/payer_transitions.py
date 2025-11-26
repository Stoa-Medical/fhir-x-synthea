"""
Mapping function for converting Synthea payer_transitions.csv rows to FHIR Coverage resources.
"""

from typing import Any

from ..fhir_lib import create_reference


def map_coverage(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea payer_transitions.csv row to a FHIR R4 Coverage resource.

    Args:
        csv_row: Dictionary with keys like Patient, Member ID, Start_Year, End_Year,
                Payer, Secondary Payer, Ownership, Owner Name

    Returns:
        Dictionary representing a FHIR Coverage resource
    """

    # Helper to map relationship
    def map_relationship(ownership_str: str | None) -> dict[str, Any] | None:
        if not ownership_str:
            return None
        ownership_lower = ownership_str.lower().strip()
        relationship_map: dict[str, dict[str, Any]] = {
            "self": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
                        "code": "self",
                        "display": "Self",
                    }
                ]
            },
            "spouse": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
                        "code": "spouse",
                        "display": "Spouse",
                    }
                ]
            },
            "guardian": {"text": "Guardian"},
        }
        return relationship_map.get(ownership_lower)

    # Extract and process fields
    patient_id = csv_row.get("Patient", "").strip() if csv_row.get("Patient") else ""
    member_id = csv_row.get("Member ID", "").strip() if csv_row.get("Member ID") else ""
    start_year_str = (
        csv_row.get("Start_Year", "").strip() if csv_row.get("Start_Year") else ""
    )
    end_year_str = (
        csv_row.get("End_Year", "").strip() if csv_row.get("End_Year") else ""
    )
    payer_id = csv_row.get("Payer", "").strip() if csv_row.get("Payer") else ""
    secondary_payer_id = (
        csv_row.get("Secondary Payer", "").strip()
        if csv_row.get("Secondary Payer")
        else ""
    )
    ownership = csv_row.get("Ownership", "").strip() if csv_row.get("Ownership") else ""
    owner_name = (
        csv_row.get("Owner Name", "").strip() if csv_row.get("Owner Name") else ""
    )

    # Parse years and convert to full dates
    # Start_Year -> YYYY-01-01, End_Year -> YYYY-12-31
    start_date = None
    end_date = None

    if start_year_str:
        try:
            year = int(start_year_str)
            start_date = f"{year}-01-01"
        except (ValueError, TypeError):
            pass

    if end_year_str:
        try:
            year = int(end_year_str)
            end_date = f"{year}-12-31"
        except (ValueError, TypeError):
            pass

    # Generate resource ID
    resource_id = (
        f"cov-{patient_id}-{start_year_str}-{payer_id}".replace(" ", "-")
        if patient_id and start_year_str and payer_id
        else ""
    )

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Coverage",
        "id": resource_id,
        "status": "active",
    }

    # Set beneficiary (patient) reference (required)
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["beneficiary"] = patient_ref

    # Set subscriberId (Member ID)
    if member_id:
        resource["subscriberId"] = member_id

    # Set period
    period: dict[str, Any] = {}
    if start_date:
        period["start"] = start_date
    if end_date:
        period["end"] = end_date
    if period:
        resource["period"] = period

    # Set payor (primary and secondary)
    payors = []
    if payer_id:
        payer_ref = create_reference("Organization", payer_id)
        if payer_ref:
            payors.append(payer_ref)

    if secondary_payer_id:
        secondary_payer_ref = create_reference("Organization", secondary_payer_id)
        if secondary_payer_ref:
            payors.append(secondary_payer_ref)

    if payors:
        resource["payor"] = payors

    # Set relationship
    relationship = map_relationship(ownership)
    if relationship:
        resource["relationship"] = relationship

    # Set owner name extension
    if owner_name:
        resource.setdefault("extension", []).append(
            {
                "url": "http://synthea.mitre.org/fhir/StructureDefinition/policy-owner-name",
                "valueString": owner_name,
            }
        )

    return resource
