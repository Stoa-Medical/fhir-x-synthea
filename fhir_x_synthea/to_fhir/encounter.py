"""
Mapping function for converting Synthea encounters.csv rows to FHIR Encounter resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime, map_encounter_class


def map_encounter(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea encounters.csv row to a FHIR R4 Encounter resource.

    Args:
        csv_row: Dictionary with keys like Id, Start, Stop, Patient, Organization,
                Provider, EncounterClass, Code, Description, ReasonCode,
                ReasonDescription, Payer, Base_Encounter_Cost, Total_Claim_Cost, Payer_Coverage

    Returns:
        Dictionary representing a FHIR Encounter resource
    """

    # Extract and process fields
    encounter_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    start = csv_row.get("Start", "").strip() if csv_row.get("Start") else ""
    stop = csv_row.get("Stop", "").strip() if csv_row.get("Stop") else ""
    patient_id = csv_row.get("Patient", "").strip() if csv_row.get("Patient") else ""
    organization_id = (
        csv_row.get("Organization", "").strip() if csv_row.get("Organization") else ""
    )
    provider_id = csv_row.get("Provider", "").strip() if csv_row.get("Provider") else ""
    encounter_class = (
        csv_row.get("EncounterClass", "").strip()
        if csv_row.get("EncounterClass")
        else ""
    )
    code = csv_row.get("Code", "").strip() if csv_row.get("Code") else ""
    description = (
        csv_row.get("Description", "").strip() if csv_row.get("Description") else ""
    )
    reason_code = (
        csv_row.get("ReasonCode", "").strip() if csv_row.get("ReasonCode") else ""
    )
    reason_description = (
        csv_row.get("ReasonDescription", "").strip()
        if csv_row.get("ReasonDescription")
        else ""
    )
    payer_id = csv_row.get("Payer", "").strip() if csv_row.get("Payer") else ""
    base_cost_str = (
        csv_row.get("Base_Encounter_Cost", "").strip()
        if csv_row.get("Base_Encounter_Cost")
        else ""
    )
    total_cost_str = (
        csv_row.get("Total_Claim_Cost", "").strip()
        if csv_row.get("Total_Claim_Cost")
        else ""
    )
    payer_coverage_str = (
        csv_row.get("Payer_Coverage", "").strip()
        if csv_row.get("Payer_Coverage")
        else ""
    )

    # Parse numeric costs
    base_cost = None
    if base_cost_str:
        try:
            base_cost = float(base_cost_str)
        except (ValueError, TypeError):
            pass

    total_cost = None
    if total_cost_str:
        try:
            total_cost = float(total_cost_str)
        except (ValueError, TypeError):
            pass

    payer_coverage = None
    if payer_coverage_str:
        try:
            payer_coverage = float(payer_coverage_str)
        except (ValueError, TypeError):
            pass

    # Determine status based on STOP field
    status = "finished" if (stop and stop != "") else "in-progress"

    # Generate resource ID (use Id if present)
    resource_id = (
        encounter_id
        if encounter_id
        else f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")
    )

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Encounter",
        "id": resource_id,
        "status": status,
    }

    # Set period
    period: dict[str, Any] = {}
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            period["start"] = iso_start
    if stop:
        iso_stop = format_datetime(stop)
        if iso_stop:
            period["end"] = iso_stop
    if period:
        resource["period"] = period

    # Set subject (patient) reference (required)
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["subject"] = patient_ref

    # Set serviceProvider (organization) reference (required)
    if organization_id:
        org_ref = create_reference("Organization", organization_id)
        if org_ref:
            resource["serviceProvider"] = org_ref

    # Set participant (provider) reference (required)
    if provider_id:
        provider_ref = create_reference("Practitioner", provider_id)
        if provider_ref:
            resource["participant"] = [{"individual": provider_ref}]

    # Set class
    class_coding = map_encounter_class(encounter_class)
    if class_coding:
        resource["class"] = class_coding

    # Set type (SNOMED CT)
    if code or description:
        type_obj: dict[str, Any] = {}
        if code:
            coding = {"system": "http://snomed.info/sct", "code": code}
            if description:
                coding["display"] = description
            type_obj["coding"] = [coding]
        if description:
            type_obj["text"] = description
        if type_obj:
            resource["type"] = [type_obj]

    # Set reasonCode
    if reason_code or reason_description:
        reason_code_obj: dict[str, Any] = {}
        if reason_code:
            coding = {"system": "http://snomed.info/sct", "code": reason_code}
            if reason_description:
                coding["display"] = reason_description
            reason_code_obj["coding"] = [coding]
        if reason_description and not reason_code:
            reason_code_obj["text"] = reason_description
        if reason_code_obj:
            resource["reasonCode"] = [reason_code_obj]

    # Set extensions for payer and costs
    extensions: list[dict[str, Any]] = []

    # Payer extension
    if payer_id:
        payer_ref = create_reference("Organization", payer_id)
        if payer_ref:
            extensions.append(
                {
                    "url": "http://example.org/fhir/StructureDefinition/encounter-payer",
                    "valueReference": payer_ref,
                }
            )

    # Cost extensions
    if base_cost is not None:
        extensions.append(
            {
                "url": "http://example.org/fhir/StructureDefinition/encounter-baseCost",
                "valueDecimal": base_cost,
            }
        )

    if total_cost is not None:
        extensions.append(
            {
                "url": "http://example.org/fhir/StructureDefinition/encounter-totalClaimCost",
                "valueDecimal": total_cost,
            }
        )

    if payer_coverage is not None:
        extensions.append(
            {
                "url": "http://example.org/fhir/StructureDefinition/encounter-payerCoverage",
                "valueDecimal": payer_coverage,
            }
        )

    if extensions:
        resource["extension"] = extensions

    return resource
