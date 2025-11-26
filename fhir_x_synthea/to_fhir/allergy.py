"""Synthea Allergy → FHIR R4 AllergyIntolerance"""

from fhir.resources.allergyintolerance import AllergyIntolerance
from synthea_pydantic import Allergy

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import (
    clinical_status,
    codeable_concept,
    format_datetime,
    normalize_allergy_category,
    ref,
    verification_status,
)


def _allergy_id(d: dict) -> str:
    """Generate deterministic allergy ID from patient+start+code."""
    patient_id = grab(d, "patient") or ""
    start = grab(d, "start") or ""
    code = grab(d, "code") or ""
    return f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")


def _allergy_type(type_str: str | None):
    """Build allergy type CodeableConcept."""
    if not type_str:
        return None
    type_code = type_str.lower()
    return {
        "coding": [
            {
                "system": "http://hl7.org/fhir/allergy-intolerance-type",
                "code": type_code,
                "display": type_code.capitalize(),
            }
        ]
    }


def _reaction(code: str | None, desc: str | None, severity: str | None) -> dict | None:
    """Build a single reaction entry."""
    if not code and not desc:
        return None

    result: dict = {}
    if code:
        result["manifestation"] = [
            {
                "concept": {
                    "coding": [{"system": "http://snomed.info/sct", "code": code}]
                }
            }
        ]
    if desc:
        result["description"] = desc
    if severity:
        result["severity"] = severity.lower()

    return result if result else None


@mapper
def _to_fhir_allergy(d: dict):
    """Core mapping from dict to FHIR AllergyIntolerance structure."""
    stop = grab(d, "stop")
    category = normalize_allergy_category(grab(d, "category"))

    # Build reactions list
    r1 = _reaction(grab(d, "reaction1"), grab(d, "description1"), grab(d, "severity1"))
    r2 = _reaction(grab(d, "reaction2"), grab(d, "description2"), grab(d, "severity2"))
    reactions = [r for r in [r1, r2] if r is not None]

    return {
        "resourceType": "AllergyIntolerance",
        "id": _allergy_id(d),
        "clinicalStatus": clinical_status(
            is_active=not stop,
            system="http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
        ),
        "verificationStatus": verification_status(
            code="confirmed",
            system="http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
        ),
        "type": _allergy_type(grab(d, "type")),
        "category": [category] if category else None,
        "code": codeable_concept(
            system=grab(d, "system"),
            code=grab(d, "code"),
            display=grab(d, "description"),
            text=grab(d, "description"),
        ),
        "patient": ref("Patient", grab(d, "patient")),
        "encounter": ref("Encounter", grab(d, "encounter")),
        "recordedDate": grab(d, "start", apply=format_datetime),
        "onsetDateTime": grab(d, "start", apply=format_datetime),
        "lastOccurrence": grab(d, "stop", apply=format_datetime),
        "reaction": reactions if reactions else None,
    }


def convert(src: Allergy) -> AllergyIntolerance:
    """Convert Synthea Allergy to FHIR R4 AllergyIntolerance.

    Args:
        src: Synthea Allergy model

    Returns:
        FHIR R4 AllergyIntolerance resource
    """
    return AllergyIntolerance(**_to_fhir_allergy(to_dict(src)))
