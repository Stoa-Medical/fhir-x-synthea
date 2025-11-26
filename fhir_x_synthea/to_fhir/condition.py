"""
Mapping function for converting Synthea conditions.csv rows to FHIR Condition resources.
"""

from typing import Any

from ..fhir_lib import (
    create_clinical_status_coding,
    create_reference,
    format_datetime,
)


def map_condition(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea conditions.csv row to a FHIR R4 Condition resource.

    Args:
        csv_row: Dictionary with keys like START, STOP, PATIENT, ENCOUNTER, CODE, DESCRIPTION

    Returns:
        Dictionary representing a FHIR Condition resource
    """

    # Extract and process fields
    start = csv_row.get("START", "").strip() if csv_row.get("START") else ""
    stop = csv_row.get("STOP", "").strip() if csv_row.get("STOP") else ""
    patient_id = csv_row.get("PATIENT", "").strip() if csv_row.get("PATIENT") else ""
    encounter_id = (
        csv_row.get("ENCOUNTER", "").strip() if csv_row.get("ENCOUNTER") else ""
    )
    code = csv_row.get("CODE", "").strip() if csv_row.get("CODE") else ""
    description = (
        csv_row.get("DESCRIPTION", "").strip() if csv_row.get("DESCRIPTION") else ""
    )

    # Determine clinical status based on STOP field
    is_active = not stop or stop == ""
    clinical_status = create_clinical_status_coding(
        is_active, "http://terminology.hl7.org/CodeSystem/condition-clinical"
    )

    # Generate resource ID from PATIENT+START+CODE
    resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Condition",
        "id": resource_id,
        "clinicalStatus": clinical_status,
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                    "display": "Confirmed",
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "encounter-diagnosis",
                        "display": "Encounter Diagnosis",
                    }
                ]
            }
        ],
    }

    # Set onsetDateTime from START
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            resource["onsetDateTime"] = iso_start

    # Set abatementDateTime from STOP if present
    if stop:
        iso_stop = format_datetime(stop)
        if iso_stop:
            resource["abatementDateTime"] = iso_stop

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

    # Set code (SNOMED CT)
    if code or description:
        code_obj: dict[str, Any] = {}
        if code:
            coding = {"system": "http://snomed.info/sct", "code": code}
            if description:
                coding["display"] = description
            code_obj["coding"] = [coding]
        if description:
            code_obj["text"] = description
        if code_obj:
            resource["code"] = code_obj

    return resource
