"""Synthea Allergy → FHIR R4 AllergyIntolerance"""

from typing import Any

from fhir.resources.allergyintolerance import AllergyIntolerance
from synthea_pydantic import Allergy

from ..fhir_lib import (
    create_clinical_status_coding,
    create_reference,
    format_datetime,
    normalize_allergy_category,
)
from ..utils import to_str


def convert(src: Allergy) -> AllergyIntolerance:
    """Convert Synthea Allergy to FHIR R4 AllergyIntolerance.

    Args:
        src: Synthea Allergy model

    Returns:
        FHIR R4 AllergyIntolerance resource
    """
    d = src.model_dump()

    # Extract and process fields (synthea_pydantic uses lowercase keys)
    start = to_str(d.get("start"))
    stop = to_str(d.get("stop"))
    patient_id = to_str(d.get("patient"))
    encounter_id = to_str(d.get("encounter"))
    code = to_str(d.get("code"))
    system = to_str(d.get("system"))
    description = to_str(d.get("description"))
    allergy_type = to_str(d.get("type"))
    category = to_str(d.get("category"))

    # Reactions
    reaction1_code = to_str(d.get("reaction1"))
    reaction1_desc = to_str(d.get("description1"))
    reaction1_severity = to_str(d.get("severity1"))
    reaction2_code = to_str(d.get("reaction2"))
    reaction2_desc = to_str(d.get("description2"))
    reaction2_severity = to_str(d.get("severity2"))

    # Determine clinical status based on stop field
    is_active = not stop
    clinical_status = create_clinical_status_coding(
        is_active, "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
    )

    # Generate resource ID from patient+start+code
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

    # Set recordedDate and onsetDateTime from start
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            resource["recordedDate"] = iso_start
            resource["onsetDateTime"] = iso_start

    # Set lastOccurrence from stop if present
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
            coding: dict[str, str] = {}
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

    # Set type (allergy vs intolerance) - R4B uses CodeableConcept
    if allergy_type:
        type_code = allergy_type.lower()
        resource["type"] = {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/allergy-intolerance-type",
                    "code": type_code,
                    "display": type_code.capitalize(),
                }
            ]
        }

    # Set category (normalized)
    normalized_category = normalize_allergy_category(category)
    if normalized_category:
        resource["category"] = [normalized_category]

    # Build reactions array (R4B uses CodeableReference for manifestation)
    reactions = []

    # First reaction
    if reaction1_code or reaction1_desc:
        reaction1: dict[str, Any] = {}
        if reaction1_code:
            # R4B: manifestation is List[CodeableReference], not List[CodeableConcept]
            reaction1["manifestation"] = [
                {
                    "concept": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": reaction1_code}
                        ]
                    }
                }
            ]
        if reaction1_desc:
            reaction1["description"] = reaction1_desc
        if reaction1_severity:
            reaction1["severity"] = reaction1_severity.lower()
        if reaction1:
            reactions.append(reaction1)

    # Second reaction (optional)
    if reaction2_code or reaction2_desc:
        reaction2: dict[str, Any] = {}
        if reaction2_code:
            reaction2["manifestation"] = [
                {
                    "concept": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": reaction2_code}
                        ]
                    }
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
