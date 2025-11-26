"""
Mapping function for converting Synthea allergies.csv rows to FHIR AllergyIntolerance resources.
"""

from typing import Any

from fhir.resources.allergyintolerance import AllergyIntolerance
from synthea_pydantic import Allergy

from ..fhir_lib import (
    create_clinical_status_coding,
    create_reference,
    format_datetime,
    normalize_allergy_category,
)


def map_allergy(allergy: Allergy) -> AllergyIntolerance:
    """
    Map a Synthea allergies.csv row to a FHIR R4 AllergyIntolerance resource.

    Args:
        csv_row: Dictionary with keys like START, STOP, PATIENT, ENCOUNTER, CODE,
                SYSTEM, DESCRIPTION, TYPE, CATEGORY, REACTION1, DESCRIPTION1,
                SEVERITY1, REACTION2, DESCRIPTION2, SEVERITY2

    Returns:
        AllergyIntolerance resource
    """
    csv_row = allergy.model_dump()
    # Extract and process fields
    start = csv_row.get("START", "").strip() if csv_row.get("START") else ""
    stop = csv_row.get("STOP", "").strip() if csv_row.get("STOP") else ""
    patient_id = csv_row.get("PATIENT", "").strip() if csv_row.get("PATIENT") else ""
    encounter_id = (
        csv_row.get("ENCOUNTER", "").strip() if csv_row.get("ENCOUNTER") else ""
    )
    code = csv_row.get("CODE", "").strip() if csv_row.get("CODE") else ""
    system = csv_row.get("SYSTEM", "").strip() if csv_row.get("SYSTEM") else ""
    description = (
        csv_row.get("DESCRIPTION", "").strip() if csv_row.get("DESCRIPTION") else ""
    )
    allergy_type = csv_row.get("TYPE", "").strip() if csv_row.get("TYPE") else ""
    category = csv_row.get("CATEGORY", "").strip() if csv_row.get("CATEGORY") else ""

    # Determine clinical status based on STOP field
    is_active = not stop or stop == ""
    clinical_status = create_clinical_status_coding(
        is_active, "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
    )

    # Generate resource ID from PATIENT+START+CODE
    resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "AllergyIntolerance",
        "id": resource_id,
        "clinicalStatus": clinical_status,
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                    "code": "confirmed",
                    "display": "Confirmed",
                }
            ]
        },
    }

    # Set recordedDate and onsetDateTime from START
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            resource["recordedDate"] = iso_start
            resource["onsetDateTime"] = iso_start

    # Set lastOccurrence from STOP if present
    if stop:
        iso_stop = format_datetime(stop)
        if iso_stop:
            resource["lastOccurrence"] = iso_stop

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

    # Set code (substance/product)
    if code or system or description:
        code_obj: dict[str, Any] = {}
        if code or system:
            coding = {}
            if code:
                coding["code"] = code
            if system:
                coding["system"] = system
            if description:
                coding["display"] = description
            if coding:
                code_obj["coding"] = [coding]
        if description:
            code_obj["text"] = description
        if code_obj:
            resource["code"] = code_obj

    # Set type (allergy vs intolerance)
    if allergy_type:
        resource["type"] = allergy_type.lower()

    # Set category (normalized)
    normalized_category = normalize_allergy_category(category)
    if normalized_category:
        resource["category"] = [normalized_category]

    # Build reactions array
    reactions = []

    # First reaction
    reaction1_code = (
        csv_row.get("REACTION1", "").strip() if csv_row.get("REACTION1") else ""
    )
    reaction1_desc = (
        csv_row.get("DESCRIPTION1", "").strip() if csv_row.get("DESCRIPTION1") else ""
    )
    reaction1_severity = (
        csv_row.get("SEVERITY1", "").strip() if csv_row.get("SEVERITY1") else ""
    )

    if reaction1_code or reaction1_desc:
        reaction1: dict[str, Any] = {}
        if reaction1_code:
            reaction1["manifestation"] = [
                {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": reaction1_code}
                    ]
                }
            ]
        if reaction1_desc:
            reaction1["description"] = reaction1_desc
        if reaction1_severity:
            reaction1["severity"] = reaction1_severity.lower()
        if reaction1:
            reactions.append(reaction1)

    # Second reaction (optional)
    reaction2_code = (
        csv_row.get("REACTION2", "").strip() if csv_row.get("REACTION2") else ""
    )
    reaction2_desc = (
        csv_row.get("DESCRIPTION2", "").strip() if csv_row.get("DESCRIPTION2") else ""
    )
    reaction2_severity = (
        csv_row.get("SEVERITY2", "").strip() if csv_row.get("SEVERITY2") else ""
    )

    if reaction2_code or reaction2_desc:
        reaction2: dict[str, Any] = {}
        if reaction2_code:
            reaction2["manifestation"] = [
                {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": reaction2_code}
                    ]
                }
            ]
        if reaction2_desc:
            reaction2["description"] = reaction2_desc
        if reaction2_severity:
            reaction2["severity"] = reaction2_severity.lower()
        if reaction2:
            reactions.append(reaction2)

    if reactions:
        resource["reaction"] = reactions

    return AllergyIntolerance(**resource)
