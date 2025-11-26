"""
Mapping function for converting Synthea careplans.csv rows to FHIR CarePlan resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime


def map_careplan(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea careplans.csv row to a FHIR R4 CarePlan resource.

    Args:
        csv_row: Dictionary with keys like Id, Start, Stop, Patient, Encounter,
                Code, Description, ReasonCode, ReasonDescription

    Returns:
        Dictionary representing a FHIR CarePlan resource
    """

    # Extract and process fields
    careplan_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    start = csv_row.get("Start", "").strip() if csv_row.get("Start") else ""
    stop = csv_row.get("Stop", "").strip() if csv_row.get("Stop") else ""
    patient_id = csv_row.get("Patient", "").strip() if csv_row.get("Patient") else ""
    encounter_id = (
        csv_row.get("Encounter", "").strip() if csv_row.get("Encounter") else ""
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

    # Determine status based on STOP field
    status = "active" if (not stop or stop == "") else "completed"

    # Generate resource ID (use Id if present, otherwise generate from Patient+Start+Code)
    if careplan_id:
        resource_id = careplan_id
    else:
        resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "CarePlan",
        "id": resource_id,
        "status": status,
        "intent": "plan",
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

    # Set encounter reference (optional)
    if encounter_id:
        encounter_ref = create_reference("Encounter", encounter_id)
        if encounter_ref:
            resource["encounter"] = encounter_ref

    # Set category (SNOMED CT)
    if code:
        resource["category"] = [
            {"coding": [{"system": "http://snomed.info/sct", "code": code}]}
        ]

    # Set description and title
    if description:
        resource["description"] = description
        resource["title"] = description

    # Set reasonCode (SNOMED CT)
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

    return resource
