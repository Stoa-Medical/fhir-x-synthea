"""FHIR R4 Observation -> Synthea Observation"""

from fhir.resources.observation import Observation
from synthea_pydantic import Observation as SyntheaObservation

from ..chidian_ext import (
    extract_code,
    extract_display,
    extract_ref_id,
    grab,
    mapper,
    parse_date,
    to_dict,
)


def _extract_category(d: dict) -> str:
    """Extract observation category from FHIR category array."""
    categories = grab(d, "category") or []
    for cat in categories:
        codings = cat.get("coding", [])
        for coding in codings:
            system = coding.get("system", "")
            if "observation-category" in system:
                return coding.get("code", "")
    return ""


def _extract_value(d: dict) -> tuple[str, str]:
    """Extract value and units from FHIR Observation.

    Returns:
        (value_str, units_str) tuple
    """
    # Quantity value
    quantity = grab(d, "valueQuantity")
    if quantity and isinstance(quantity, dict):
        val = quantity.get("value")
        units = quantity.get("unit", "") or quantity.get("code", "")
        if val is not None:
            return (str(val), units)

    # Boolean value
    bool_val = grab(d, "valueBoolean")
    if bool_val is not None:
        return (str(bool_val).lower(), "")

    # String value
    str_val = grab(d, "valueString")
    if str_val is not None:
        return (str(str_val), "")

    # CodeableConcept value
    cc = grab(d, "valueCodeableConcept")
    if cc and isinstance(cc, dict):
        codings = cc.get("coding", [])
        if codings:
            return (codings[0].get("code", ""), "")
        text = cc.get("text", "")
        if text:
            return (text, "")

    return ("", "")


@mapper(remove_empty=False)
def _to_synthea_observation(d: dict):
    """Core mapping from FHIR Observation dict to Synthea structure."""
    value, units = _extract_value(d)

    return {
        "date": parse_date(d, "effectiveDateTime") or None,
        "patient": extract_ref_id(d, "subject") or None,
        "encounter": extract_ref_id(d, "encounter") or None,
        "category": _extract_category(d) or None,
        "code": extract_code(d, "code", system="http://loinc.org") or None,
        "description": extract_display(d, "code") or None,
        "value": value or None,
        "units": units or None,
        "type": _extract_category(d) or None,
    }


def convert(src: Observation) -> SyntheaObservation:
    """Convert FHIR R4 Observation to Synthea Observation.

    Args:
        src: FHIR R4 Observation resource

    Returns:
        Synthea Observation model
    """
    return SyntheaObservation(**_to_synthea_observation(to_dict(src)))
