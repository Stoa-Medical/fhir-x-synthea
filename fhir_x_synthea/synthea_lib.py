"""
Synthea-specific builder helpers for FHIR to Synthea mappings.

Provides helpers for building Synthea model data, including:
- Default value handling for required fields
- Datetime formatting for Synthea format
- Field normalization utilities
"""

from datetime import datetime
from decimal import Decimal
from typing import Any


def default(value: Any, fallback: Any) -> Any:
    """
    Return fallback if value is empty/None, otherwise return value.

    Useful for Synthea required fields that need defaults.

    Args:
        value: The value to check
        fallback: Default to return if value is empty

    Returns:
        value if not empty, otherwise fallback

    Example:
        default(grab(d, "name"), "Unknown")
    """
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return value


def to_synthea_datetime(dt_value: str | datetime | None) -> str | None:
    """
    Format datetime to Synthea ISO 8601 format.

    Args:
        dt_value: Datetime value (string or datetime object)

    Returns:
        ISO 8601 formatted string, or None if input is empty
    """
    if not dt_value:
        return None
    try:
        if isinstance(dt_value, datetime):
            return dt_value.isoformat()
        dt_str = str(dt_value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)
        return dt.isoformat()
    except (ValueError, AttributeError, TypeError):
        return None


def to_synthea_date(dt_value: str | datetime | None) -> str | None:
    """
    Format datetime to Synthea date-only format (YYYY-MM-DD).

    Args:
        dt_value: Datetime value (string or datetime object)

    Returns:
        Date string in YYYY-MM-DD format, or None if input is empty
    """
    if not dt_value:
        return None
    try:
        if isinstance(dt_value, datetime):
            return dt_value.date().isoformat()
        dt_str = str(dt_value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)
        return dt.date().isoformat()
    except (ValueError, AttributeError, TypeError):
        return None


def to_decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    """
    Convert value to Decimal for Synthea numeric fields.

    Args:
        value: Value to convert
        default: Default if conversion fails

    Returns:
        Decimal value, or default
    """
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, ArithmeticError):
        return default


def normalize_str(value: Any) -> str | None:
    """
    Normalize string value, returning None for empty strings.

    Args:
        value: Value to normalize

    Returns:
        Stripped string or None if empty
    """
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def map_fhir_gender(gender: str | None) -> str:
    """
    Map FHIR administrative gender to Synthea gender code.

    Args:
        gender: FHIR gender string ("male", "female", "other", "unknown")

    Returns:
        Synthea gender code ("M" or "F"), defaults to "M"
    """
    if not gender:
        return "M"
    mapping = {"male": "M", "female": "F"}
    return mapping.get(gender.lower(), "M")


def map_fhir_marital(marital_status: dict[str, Any] | None) -> str | None:
    """
    Map FHIR marital status CodeableConcept to Synthea code.

    Args:
        marital_status: FHIR CodeableConcept for marital status

    Returns:
        Synthea marital code (M, S, D, W) or None
    """
    if not marital_status:
        return None
    codings = marital_status.get("coding", [])
    for coding in codings:
        code = coding.get("code", "")
        if code in ("M", "S", "D", "W"):
            return code
    return None


def map_encounter_class(
    encounter_class: list[dict[str, Any]] | dict[str, Any] | None,
) -> str:
    """
    Map FHIR encounter class to Synthea encounter class string.

    Args:
        encounter_class: FHIR Coding or list of CodeableConcepts

    Returns:
        Synthea encounter class string, defaults to "ambulatory"
    """
    if not encounter_class:
        return "ambulatory"

    # Handle list of CodeableConcepts (R4B format)
    if isinstance(encounter_class, list):
        if not encounter_class:
            return "ambulatory"
        first_class = encounter_class[0]
        codings = first_class.get("coding", [])
        if not codings:
            return "ambulatory"
        coding = codings[0]
        code = coding.get("code", "")
        display = coding.get("display", "")
    else:
        # Handle single Coding
        code = encounter_class.get("code", "")
        display = encounter_class.get("display", "")

    # Map ActCode codes to Synthea values
    code_map = {
        "AMB": "ambulatory",
        "EMER": "emergency",
        "IMP": "inpatient",
        "ACUTE": "inpatient",
    }
    result = code_map.get(code, "")
    if result:
        return result

    # Fallback to display
    if display:
        return display.lower()

    return "ambulatory"


# Valid Synthea encounter classes
VALID_ENCOUNTER_CLASSES = frozenset(
    {
        "ambulatory",
        "emergency",
        "inpatient",
        "wellness",
        "urgentcare",
        "outpatient",
    }
)


def validate_encounter_class(encounter_class: str) -> str:
    """
    Validate and normalize encounter class to valid Synthea value.

    Args:
        encounter_class: Encounter class string

    Returns:
        Valid Synthea encounter class, defaults to "ambulatory"
    """
    if encounter_class in VALID_ENCOUNTER_CLASSES:
        return encounter_class
    return "ambulatory"


__all__ = [
    "default",
    "to_synthea_datetime",
    "to_synthea_date",
    "to_decimal",
    "normalize_str",
    "map_fhir_gender",
    "map_fhir_marital",
    "map_encounter_class",
    "validate_encounter_class",
    "VALID_ENCOUNTER_CLASSES",
]
