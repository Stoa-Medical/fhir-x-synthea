"""
Mapping function for converting Synthea immunizations.csv rows to FHIR Immunization resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime


def map_immunization(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea immunizations.csv row to a FHIR R4 Immunization resource.

    Args:
        csv_row: Dictionary with keys like DATE, PATIENT, ENCOUNTER, CODE, DESCRIPTION, COST

    Returns:
        Dictionary representing a FHIR Immunization resource
    """

    # Extract and process fields
    date = csv_row.get("DATE", "").strip() if csv_row.get("DATE") else ""
    patient_id = csv_row.get("PATIENT", "").strip() if csv_row.get("PATIENT") else ""
    encounter_id = (
        csv_row.get("ENCOUNTER", "").strip() if csv_row.get("ENCOUNTER") else ""
    )
    code = csv_row.get("CODE", "").strip() if csv_row.get("CODE") else ""
    description = (
        csv_row.get("DESCRIPTION", "").strip() if csv_row.get("DESCRIPTION") else ""
    )
    cost_str = csv_row.get("COST", "").strip() if csv_row.get("COST") else ""

    # Parse cost
    cost = None
    if cost_str:
        try:
            cost = float(cost_str)
        except (ValueError, TypeError):
            pass

    # Generate resource ID from DATE+PATIENT+CODE
    resource_id = f"{patient_id}-{date}-{code}".replace(" ", "-").replace(":", "-")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Immunization",
        "id": resource_id,
        "status": "completed",
    }

    # Set occurrenceDateTime from DATE
    if date:
        iso_date = format_datetime(date)
        if iso_date:
            resource["occurrenceDateTime"] = iso_date

    # Set patient reference (required)
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["patient"] = patient_ref

    # Set encounter reference (optional)
    if encounter_id:
        encounter_ref = create_reference("Encounter", encounter_id)
        if encounter_ref:
            resource["encounter"] = encounter_ref

    # Set vaccineCode (CVX)
    if code or description:
        vaccine_code: dict[str, Any] = {}
        if code:
            coding = {"system": "http://hl7.org/fhir/sid/cvx", "code": code}
            if description:
                coding["display"] = description
            vaccine_code["coding"] = [coding]
        if description:
            vaccine_code["text"] = description
        if vaccine_code:
            resource["vaccineCode"] = vaccine_code

    # Set cost extension if present
    if cost is not None:
        resource.setdefault("extension", []).append(
            {
                "url": "http://synthea.mitre.org/fhir/StructureDefinition/immunization-cost",
                "valueDecimal": cost,
            }
        )

    return resource
