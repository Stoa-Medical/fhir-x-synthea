"""FHIR R4 AllergyIntolerance → Synthea Allergy"""

import logging

from fhir.resources.allergyintolerance import AllergyIntolerance
from synthea_pydantic import Allergy

from ..chidian_ext import (
    coalesce,
    extract_code,
    extract_display,
    extract_ref_id,
    extract_system,
    grab,
    mapper,
    parse_dt,
    to_datetime,
    to_dict,
)

logger = logging.getLogger(__name__)


def _extract_allergy_type(d: dict) -> str | None:
    """Extract allergy type from CodeableConcept or string."""
    type_obj = grab(d, "type")
    if not type_obj:
        return None

    if isinstance(type_obj, dict):
        return (
            extract_code(
                {"type": type_obj},
                "type",
                system="http://hl7.org/fhir/allergy-intolerance-type",
            )
            or None
        )
    elif isinstance(type_obj, str):
        return type_obj.lower() or None

    return None


def _extract_category(d: dict) -> str | None:
    """Extract first category."""
    categories = grab(d, "category") or []
    if categories and isinstance(categories[0], str):
        return categories[0]
    return None


def _extract_reaction(d: dict, idx: int) -> tuple[str, str, str]:
    """Extract reaction code, description, and severity for reaction at index."""
    reactions = grab(d, "reaction") or []
    if idx >= len(reactions):
        return "", "", ""

    r = reactions[idx]
    manifestations = r.get("manifestation", [])

    code = ""
    if manifestations:
        # R4B uses concept inside manifestation
        first_manif = manifestations[0]
        if "concept" in first_manif:
            code = extract_code(
                {"m": first_manif["concept"]}, "m", system="http://snomed.info/sct"
            )
        else:
            code = extract_code(
                {"m": first_manif}, "m", system="http://snomed.info/sct"
            )

    description = r.get("description", "")
    severity = (r.get("severity") or "").upper()

    return code, description, severity


@mapper(remove_empty=False)
def _to_synthea_allergy(d: dict):
    """Core mapping from dict to Synthea Allergy structure."""
    r1_code, r1_desc, r1_sev = _extract_reaction(d, 0)
    r2_code, r2_desc, r2_sev = _extract_reaction(d, 1)

    # Log lossy conversions
    reactions = grab(d, "reaction") or []
    if len(reactions) > 2:
        logger.warning(
            "AllergyIntolerance has %d reactions; only first 2 preserved",
            len(reactions),
        )

    return {
        "start": coalesce(d, "recordedDate", "onsetDateTime", apply=to_datetime)
        or None,
        "stop": parse_dt(d, "lastOccurrence") or None,
        "patient": extract_ref_id(d, "patient") or None,
        "encounter": extract_ref_id(d, "encounter") or None,
        "code": extract_code(
            d,
            "code",
            systems=[
                "http://snomed.info/sct",
                "http://www.nlm.nih.gov/research/umls/rxnorm",
            ],
        )
        or None,
        "system": extract_system(d, "code") or None,
        "description": extract_display(d, "code") or None,
        "type": _extract_allergy_type(d),
        "category": _extract_category(d),
        "reaction1": r1_code or None,
        "description1": r1_desc or None,
        "severity1": r1_sev or None,
        "reaction2": r2_code or None,
        "description2": r2_desc or None,
        "severity2": r2_sev or None,
    }


def convert(src: AllergyIntolerance) -> Allergy:
    """Convert FHIR R4 AllergyIntolerance to Synthea Allergy.

    Args:
        src: FHIR R4 AllergyIntolerance resource

    Returns:
        Synthea Allergy model
    """
    return Allergy(**_to_synthea_allergy(to_dict(src)))
