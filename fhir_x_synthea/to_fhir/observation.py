"""
Mapping function for converting Synthea observations.csv rows to FHIR Observation resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime


def map_observation(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea observations.csv row to a FHIR R4 Observation resource.

    Args:
        csv_row: Dictionary with keys like DATE, PATIENT, ENCOUNTER, CODE,
                DESCRIPTION, VALUE, UNITS, TYPE

    Returns:
        Dictionary representing a FHIR Observation resource
    """

    # Helper to normalize category
    def normalize_category(category_type: str | None) -> dict[str, Any] | None:
        if not category_type:
            return None
        category_lower = category_type.lower().strip()
        category_map = {
            "vital-signs": {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs",
            },
            "laboratory": {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory",
                "display": "Laboratory",
            },
            "survey": {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "survey",
                "display": "Survey",
            },
            "social-history": {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "social-history",
                "display": "Social History",
            },
            "imaging": {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "imaging",
                "display": "Imaging",
            },
            "procedure": {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "procedure",
                "display": "Procedure",
            },
        }
        return category_map.get(category_lower)

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
    value_str = csv_row.get("VALUE", "").strip() if csv_row.get("VALUE") else ""
    units = csv_row.get("UNITS", "").strip() if csv_row.get("UNITS") else ""
    category_type = csv_row.get("TYPE", "").strip() if csv_row.get("TYPE") else ""

    # Generate resource ID from DATE+PATIENT+CODE
    resource_id = f"{patient_id}-{date}-{code}".replace(" ", "-").replace(":", "-")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Observation",
        "id": resource_id,
        "status": "final",
    }

    # Set effectiveDateTime from DATE
    if date:
        iso_date = format_datetime(date)
        if iso_date:
            resource["effectiveDateTime"] = iso_date

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

    # Set code (LOINC)
    if code or description:
        code_obj: dict[str, Any] = {}
        if code:
            coding = {"system": "http://loinc.org", "code": code}
            if description:
                coding["display"] = description
            code_obj["coding"] = [coding]
        if description:
            code_obj["text"] = description
        if code_obj:
            resource["code"] = code_obj

    # Set category
    category_coding = normalize_category(category_type)
    if category_coding:
        resource["category"] = [{"coding": [category_coding]}]

    # Set value based on type detection
    if value_str:
        # Try to parse as numeric
        try:
            numeric_value = float(value_str)
            # Use valueQuantity if numeric
            quantity: dict[str, Any] = {"value": numeric_value}
            if units:
                quantity["unit"] = units
                quantity["code"] = units
                quantity["system"] = "http://unitsofmeasure.org"
            else:
                # Default unit "1" if no units provided
                quantity["unit"] = "1"
                quantity["code"] = "1"
                quantity["system"] = "http://unitsofmeasure.org"
            resource["valueQuantity"] = quantity
        except (ValueError, TypeError):
            # Try boolean
            value_lower = value_str.lower()
            if value_lower in ("true", "false"):
                resource["valueBoolean"] = value_lower == "true"
            else:
                # Default to string
                resource["valueString"] = value_str

    return resource
