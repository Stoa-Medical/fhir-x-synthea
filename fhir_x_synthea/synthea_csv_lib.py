"""
Common helper functions for reverse FHIR to Synthea CSV mapping operations.
Shared utilities used across synthea_csv_mappers modules.
"""

from datetime import datetime
from typing import Any


def extract_reference_id(reference_obj: dict[str, Any] | None) -> str:
    """
    Extract the resource ID from a FHIR reference object.

    Args:
        reference_obj: FHIR reference object with "reference" key (e.g., {"reference": "Patient/123"})

    Returns:
        Resource ID string, or empty string if invalid/missing
    """
    if not reference_obj:
        return ""
    reference = reference_obj.get("reference", "")
    if not reference:
        return ""
    # Extract id from "ResourceType/id" format
    if "/" in reference:
        return reference.split("/")[-1]
    return reference


def parse_datetime(dt_value: str | datetime | None) -> str:
    """
    Parse a FHIR datetime value to Synthea format (ISO 8601).

    Args:
        dt_value: ISO 8601 datetime string or datetime object from FHIR

    Returns:
        ISO 8601 formatted datetime string, or empty string if parsing fails
    """
    if not dt_value:
        return ""
    try:
        # Handle datetime objects directly
        if isinstance(dt_value, datetime):
            return dt_value.isoformat()
        # Handle string input
        dt = datetime.fromisoformat(str(dt_value).replace("Z", "+00:00"))
        return dt.isoformat()
    except (ValueError, AttributeError, TypeError):
        return ""


def parse_datetime_to_date(dt_str: str | None) -> str:
    """
    Parse a FHIR datetime string to date-only format (YYYY-MM-DD).

    Args:
        dt_str: ISO 8601 datetime string from FHIR

    Returns:
        Date string in YYYY-MM-DD format, or empty string if parsing fails
    """
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except (ValueError, AttributeError):
        return ""


def extract_coding_code(
    codeable_concept: dict[str, Any] | None,
    preferred_system: str | None = None,
    preferred_systems: list[str] | None = None,
) -> str:
    """
    Extract a coding code from a FHIR CodeableConcept.

    Args:
        codeable_concept: FHIR CodeableConcept dictionary
        preferred_system: Single preferred coding system URL (deprecated, use preferred_systems)
        preferred_systems: List of preferred coding system URLs (tried in order)

    Returns:
        Coding code string, or empty string if not found
    """
    if not codeable_concept:
        return ""
    codings = codeable_concept.get("coding", [])
    if not codings:
        return ""

    # Handle preferred_systems list (newer API)
    if preferred_systems:
        for system in preferred_systems:
            for coding in codings:
                if coding.get("system") == system:
                    code = coding.get("code", "")
                    if code:
                        return code

    # Handle single preferred_system (legacy API)
    if preferred_system:
        for coding in codings:
            if coding.get("system") == preferred_system:
                code = coding.get("code", "")
                if code:
                    return code

    # Fallback to first coding
    first_code = codings[0].get("code", "")
    return first_code if first_code else ""


def extract_coding_system(codeable_concept: dict[str, Any] | None) -> str:
    """
    Extract the coding system URL from a FHIR CodeableConcept.

    Args:
        codeable_concept: FHIR CodeableConcept dictionary

    Returns:
        Coding system URL string, or empty string if not found
    """
    if not codeable_concept:
        return ""
    codings = codeable_concept.get("coding", [])
    if not codings:
        return ""
    return codings[0].get("system", "")


def extract_display_or_text(codeable_concept: dict[str, Any] | None) -> str:
    """
    Extract display text or fallback to text from a FHIR CodeableConcept.

    Args:
        codeable_concept: FHIR CodeableConcept dictionary

    Returns:
        Display text or text field, or empty string if not found
    """
    if not codeable_concept:
        return ""
    codings = codeable_concept.get("coding", [])
    if codings:
        display = codings[0].get("display", "")
        if display:
            return display
    return codeable_concept.get("text", "")


def extract_extension_decimal(fhir_resource: dict[str, Any], extension_url: str) -> str:
    """
    Extract a decimal value from a FHIR extension.

    Args:
        fhir_resource: FHIR resource dictionary
        extension_url: Extension URL to search for

    Returns:
        Decimal value as string, or empty string if not found
    """
    extensions = fhir_resource.get("extension", [])
    for ext in extensions:
        if ext.get("url") == extension_url:
            value = ext.get("valueDecimal")
            if value is not None:
                return str(value)
    return ""


def extract_extension_string(fhir_resource: dict[str, Any], extension_url: str) -> str:
    """
    Extract a string value from a FHIR extension.

    Args:
        fhir_resource: FHIR resource dictionary
        extension_url: Extension URL to search for

    Returns:
        String value, or empty string if not found
    """
    extensions = fhir_resource.get("extension", [])
    for ext in extensions:
        if ext.get("url") == extension_url:
            value = ext.get("valueString")
            if value:
                return value
    return ""


def extract_extension_reference(
    fhir_resource: dict[str, Any], extension_url: str
) -> str:
    """
    Extract a reference ID from a FHIR extension's valueReference.

    Args:
        fhir_resource: FHIR resource dictionary
        extension_url: Extension URL to search for

    Returns:
        Reference ID, or empty string if not found
    """
    extensions = fhir_resource.get("extension", [])
    for ext in extensions:
        if ext.get("url") == extension_url:
            value_ref = ext.get("valueReference")
            if value_ref:
                return extract_reference_id(value_ref)
    return ""


def extract_extension_period(
    fhir_resource: dict[str, Any], extension_url: str
) -> dict[str, Any]:
    """
    Extract a period from a FHIR extension's valuePeriod.

    Args:
        fhir_resource: FHIR resource dictionary
        extension_url: Extension URL to search for

    Returns:
        Period dictionary, or empty dict if not found
    """
    extensions = fhir_resource.get("extension", [])
    for ext in extensions:
        if ext.get("url") == extension_url:
            value_period = ext.get("valuePeriod")
            if value_period:
                return value_period
    return {}


def extract_nested_extension(
    fhir_resource: dict[str, Any], extension_url: str, nested_url: str, value_type: str
) -> str:
    """
    Extract a value from a nested extension structure.

    Args:
        fhir_resource: FHIR resource dictionary
        extension_url: Parent extension URL
        nested_url: Nested extension URL (sub-extension)
        value_type: Type of value to extract ("valueDecimal", "valueInteger", "valueString")

    Returns:
        Value as string, or empty string if not found
    """
    extensions = fhir_resource.get("extension", [])
    for ext in extensions:
        if ext.get("url") == extension_url:
            nested_extensions = ext.get("extension", [])
            for nested_ext in nested_extensions:
                if nested_ext.get("url") == nested_url:
                    if value_type == "valueDecimal":
                        value = nested_ext.get("valueDecimal")
                    elif value_type == "valueInteger":
                        value = nested_ext.get("valueInteger")
                    elif value_type == "valueString":
                        value = nested_ext.get("valueString")
                    else:
                        value = None
                    if value is not None:
                        return str(value)
    return ""


def extract_year(dt_str: str | None) -> str:
    """
    Extract the year component from a date string.

    Args:
        dt_str: Date string in ISO 8601 format

    Returns:
        Year as string (YYYY), or empty string if parsing fails
    """
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return str(dt.year)
    except (ValueError, AttributeError):
        # Try to extract year from YYYY-MM-DD format
        if dt_str and len(dt_str) >= 4:
            try:
                return str(int(dt_str[:4]))
            except (ValueError, TypeError):
                pass
        return ""


def normalize_sop_code(sop_code: str | None) -> str:
    """
    Normalize SOP code by stripping urn:oid: prefix if present.

    Args:
        sop_code: SOP code string, potentially with urn:oid: prefix

    Returns:
        SOP code without prefix, or empty string if input is empty
    """
    if not sop_code or sop_code.strip() == "":
        return ""
    sop_code = sop_code.strip()
    if sop_code.startswith("urn:oid:"):
        return sop_code[8:]  # Remove "urn:oid:" prefix
    return sop_code
