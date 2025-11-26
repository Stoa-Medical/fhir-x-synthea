"""
Mapping function for converting Synthea procedures.csv rows to FHIR Procedure resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime


def map_procedure(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea procedures.csv row to a FHIR R4 Procedure resource.

    Args:
        csv_row: Dictionary with keys like START, STOP, PATIENT, ENCOUNTER,
                SYSTEM, CODE, DESCRIPTION, BASE_COST, REASONCODE, REASONDESCRIPTION

    Returns:
        Dictionary representing a FHIR Procedure resource
    """

    # Extract and process fields
    start = csv_row.get("START", "").strip() if csv_row.get("START") else ""
    stop = csv_row.get("STOP", "").strip() if csv_row.get("STOP") else ""
    patient_id = csv_row.get("PATIENT", "").strip() if csv_row.get("PATIENT") else ""
    encounter_id = (
        csv_row.get("ENCOUNTER", "").strip() if csv_row.get("ENCOUNTER") else ""
    )
    system = csv_row.get("SYSTEM", "").strip() if csv_row.get("SYSTEM") else ""
    code = csv_row.get("CODE", "").strip() if csv_row.get("CODE") else ""
    description = (
        csv_row.get("DESCRIPTION", "").strip() if csv_row.get("DESCRIPTION") else ""
    )
    base_cost_str = (
        csv_row.get("BASE_COST", "").strip() if csv_row.get("BASE_COST") else ""
    )
    reason_code = (
        csv_row.get("REASONCODE", "").strip() if csv_row.get("REASONCODE") else ""
    )
    reason_description = (
        csv_row.get("REASONDESCRIPTION", "").strip()
        if csv_row.get("REASONDESCRIPTION")
        else ""
    )

    # Parse base cost
    base_cost = None
    if base_cost_str:
        try:
            base_cost = float(base_cost_str)
        except (ValueError, TypeError):
            pass

    # Generate resource ID from PATIENT+START+CODE
    resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Procedure",
        "id": resource_id,
        "status": "completed",
    }

    # Set performedDateTime or performedPeriod based on presence of STOP
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            if stop:
                # Use performedPeriod if STOP is present
                iso_stop = format_datetime(stop)
                if iso_stop:
                    resource["performedPeriod"] = {"start": iso_start, "end": iso_stop}
                else:
                    resource["performedDateTime"] = iso_start
            else:
                # Use performedDateTime if only START is present
                resource["performedDateTime"] = iso_start

    # Set subject (patient) reference
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["subject"] = patient_ref

    # Set encounter reference
    if encounter_id:
        encounter_ref = create_reference("Encounter", encounter_id)
        if encounter_ref:
            resource["encounter"] = encounter_ref

    # Set code
    if code or system or description:
        code_obj: dict[str, Any] = {}
        if code or system:
            coding = {}
            if system:
                coding["system"] = system
            if code:
                coding["code"] = code
            if description:
                coding["display"] = description
            if coding:
                code_obj["coding"] = [coding]
        if description:
            code_obj["text"] = description
        if code_obj:
            resource["code"] = code_obj

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

    # Set base cost extension
    if base_cost is not None:
        resource.setdefault("extension", []).append(
            {
                "url": "http://example.org/fhir/StructureDefinition/baseCost",
                "valueMoney": {"value": base_cost, "currency": "USD"},
            }
        )

    return resource
