"""
Chidian extensions for FHIR x Synthea mappings.

Provides helpers that integrate with chidian's grab() and @mapper:
- coalesce(): Try multiple paths, return first non-None
- grab_attr(): Grab from object attributes without model_dump()
- FHIR extraction helpers: extract_ref_id, extract_code, extract_display, etc.
- Reexports from chidian for convenience
"""

from datetime import datetime
from typing import Any, Callable

from chidian import DROP, KEEP, grab, mapper, mapping_context


def coalesce(
    source: dict | object,
    *paths: str,
    default: Any = None,
    apply: Callable | None = None,
) -> Any:
    """
    Return the first non-None value from multiple paths.

    Args:
        source: Source data (dict or object with attributes)
        *paths: Path strings to try in order
        default: Default if all paths return None
        apply: Optional function to apply to the result

    Returns:
        First non-None value (optionally transformed), or default

    Example:
        # Try recordedDate first, fall back to onsetDateTime
        coalesce(d, "recordedDate", "onsetDateTime")
        coalesce(d, "recordedDate", "onsetDateTime", apply=parse_datetime)
    """
    for path in paths:
        result = grab(source, path)
        if result is not None:
            if apply is not None:
                return apply(result)
            return result
    return default


def grab_attr(
    obj: Any,
    path: str,
    default: Any = None,
    apply: Callable | list[Callable] | None = None,
) -> Any:
    """
    Grab value from object attributes using dot notation.

    Unlike grab(), this accesses object attributes directly without
    requiring model_dump(). Useful for Pydantic models.

    Args:
        obj: Source object
        path: Dot-separated attribute path (e.g., "patient.id")
        default: Default value if path not found
        apply: Function(s) to apply to result

    Returns:
        Value at path or default

    Example:
        grab_attr(synthea_patient, "id")
        grab_attr(synthea_patient, "name.given")
    """
    if obj is None:
        return default

    parts = path.split(".")
    current = obj

    for part in parts:
        if current is None:
            return default

        # Handle list index notation like [0] or [-1]
        if "[" in part:
            attr_name, rest = part.split("[", 1)
            idx_str = rest.rstrip("]")

            # Get the attribute first
            if attr_name:
                current = getattr(current, attr_name, None)
                if current is None:
                    return default

            # Then index into it
            try:
                idx = int(idx_str)
                current = current[idx]
            except (IndexError, TypeError, KeyError):
                return default
        else:
            # Try attribute access, fall back to dict access
            if hasattr(current, part):
                current = getattr(current, part, None)
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return default

    if current is None:
        return default

    # Apply transformation functions
    if apply is not None and current is not None:
        fns = apply if isinstance(apply, list) else [apply]
        for fn in fns:
            current = fn(current)

    return current


def to_dict(obj: Any) -> dict:
    """
    Convert Pydantic model or similar to dict.

    Handles:
    - Objects with model_dump() (Pydantic v2)
    - Objects with dict() method (Pydantic v1)
    - Plain dicts (pass through)

    Uses mode="json" to serialize UUIDs, dates, etc. as strings.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation with JSON-serializable values
    """
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        # Use mode="json" to serialize UUIDs, dates as strings
        return obj.model_dump(mode="json")
    if hasattr(obj, "dict"):
        return obj.dict()
    raise TypeError(f"Cannot convert {type(obj).__name__} to dict")


# =============================================================================
# FHIR Extraction Helpers
# These combine grab() with FHIR-specific extraction logic for use in mappings.
# =============================================================================


def extract_ref_id(source: dict, path: str, default: str = "") -> str:
    """
    Extract resource ID from a FHIR reference at the given path.

    Args:
        source: Source dict
        path: Path to reference object (e.g., "patient", "subject")
        default: Default if not found

    Returns:
        Resource ID string (e.g., "123" from "Patient/123")

    Example:
        extract_ref_id(d, "patient")  # {"patient": {"reference": "Patient/123"}} -> "123"
    """
    ref_obj = grab(source, path)
    if not ref_obj:
        return default
    reference = ref_obj.get("reference", "") if isinstance(ref_obj, dict) else ""
    if not reference:
        return default
    return reference.split("/")[-1] if "/" in reference else reference


def extract_code(
    source: dict,
    path: str,
    system: str | None = None,
    systems: list[str] | None = None,
    default: str = "",
) -> str:
    """
    Extract coding code from a FHIR CodeableConcept at the given path.

    Args:
        source: Source dict
        path: Path to CodeableConcept (e.g., "code", "type[0]")
        system: Preferred coding system URL
        systems: List of preferred systems (tried in order)
        default: Default if not found

    Returns:
        Code string

    Example:
        extract_code(d, "code", system="http://snomed.info/sct")
    """
    concept = grab(source, path)
    if not concept or not isinstance(concept, dict):
        return default

    codings = concept.get("coding", [])
    if not codings:
        return default

    # Try preferred systems first
    preferred = systems or ([system] if system else [])
    for sys in preferred:
        for coding in codings:
            if coding.get("system") == sys:
                code = coding.get("code", "")
                if code:
                    return str(code)

    # Fallback to first coding
    return str(codings[0].get("code", "")) or default


def extract_system(source: dict, path: str, default: str = "") -> str:
    """
    Extract coding system URL from a FHIR CodeableConcept at the given path.

    Args:
        source: Source dict
        path: Path to CodeableConcept
        default: Default if not found

    Returns:
        System URL string
    """
    concept = grab(source, path)
    if not concept or not isinstance(concept, dict):
        return default

    codings = concept.get("coding", [])
    if not codings:
        return default

    return codings[0].get("system", "") or default


def extract_display(source: dict, path: str, default: str = "") -> str:
    """
    Extract display text from a FHIR CodeableConcept at the given path.

    Tries coding[0].display first, then falls back to text field.

    Args:
        source: Source dict
        path: Path to CodeableConcept
        default: Default if not found

    Returns:
        Display or text string
    """
    concept = grab(source, path)
    if not concept or not isinstance(concept, dict):
        return default

    codings = concept.get("coding", [])
    if codings:
        display = codings[0].get("display", "")
        if display:
            return display

    return concept.get("text", "") or default


def parse_dt(source: dict, path: str, default: str = "") -> str:
    """
    Extract and parse a datetime value to ISO 8601 format.

    Args:
        source: Source dict
        path: Path to datetime value
        default: Default if not found or parse fails

    Returns:
        ISO 8601 datetime string
    """
    dt_value = grab(source, path)
    return to_datetime(dt_value, default)


def to_datetime(dt_value: Any, default: str = "") -> str:
    """
    Parse a datetime value to ISO 8601 format.

    Can be used as an apply function with grab() or coalesce().

    Args:
        dt_value: Datetime value (string or datetime object)
        default: Default if parse fails

    Returns:
        ISO 8601 datetime string
    """
    if not dt_value:
        return default

    try:
        if isinstance(dt_value, datetime):
            return dt_value.isoformat()
        dt_str = str(dt_value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)
        return dt.isoformat()
    except (ValueError, AttributeError, TypeError):
        return default


def parse_date(source: dict, path: str, default: str = "") -> str:
    """
    Extract and parse a datetime value to date-only format (YYYY-MM-DD).

    Args:
        source: Source dict
        path: Path to datetime value
        default: Default if not found or parse fails

    Returns:
        Date string in YYYY-MM-DD format
    """
    dt_value = grab(source, path)
    return to_date_str(dt_value, default)


def to_date_str(dt_value: Any, default: str = "") -> str:
    """
    Parse a datetime value to date-only format (YYYY-MM-DD).

    Can be used as an apply function with grab() or coalesce().

    Args:
        dt_value: Datetime value (string or datetime object)
        default: Default if parse fails

    Returns:
        Date string in YYYY-MM-DD format
    """
    if not dt_value:
        return default

    try:
        if isinstance(dt_value, datetime):
            return dt_value.date().isoformat()
        dt_str = str(dt_value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)
        return dt.date().isoformat()
    except (ValueError, AttributeError, TypeError):
        return default


def extract_ext(
    source: dict,
    ext_url: str,
    value_type: str = "valueString",
    default: Any = "",
) -> Any:
    """
    Extract a value from a FHIR extension by URL.

    Args:
        source: Source dict (resource with extension array)
        ext_url: Extension URL to find
        value_type: Type of value to extract (valueString, valueDecimal, etc.)
        default: Default if not found

    Returns:
        Extension value

    Example:
        extract_ext(d, "http://example.org/ext/cost", "valueDecimal")
    """
    extensions = grab(source, "extension") or []
    for ext in extensions:
        if ext.get("url") == ext_url:
            value = ext.get(value_type)
            if value is not None:
                return value
    return default


def extract_ext_ref(source: dict, ext_url: str, default: str = "") -> str:
    """
    Extract a reference ID from a FHIR extension's valueReference.

    Args:
        source: Source dict
        ext_url: Extension URL to find
        default: Default if not found

    Returns:
        Reference ID string
    """
    extensions = grab(source, "extension") or []
    for ext in extensions:
        if ext.get("url") == ext_url:
            ref_obj = ext.get("valueReference")
            if ref_obj:
                reference = ref_obj.get("reference", "")
                if reference and "/" in reference:
                    return reference.split("/")[-1]
                return reference or default
    return default


def extract_nested_ext(
    source: dict,
    ext_url: str,
    nested_url: str,
    value_type: str = "valueString",
    default: Any = "",
) -> Any:
    """
    Extract a value from a nested FHIR extension.

    Args:
        source: Source dict
        ext_url: Parent extension URL
        nested_url: Nested extension URL
        value_type: Type of value to extract
        default: Default if not found

    Returns:
        Nested extension value
    """
    extensions = grab(source, "extension") or []
    for ext in extensions:
        if ext.get("url") == ext_url:
            nested = ext.get("extension", [])
            for n in nested:
                if n.get("url") == nested_url:
                    value = n.get(value_type)
                    if value is not None:
                        return value
    return default


__all__ = [
    # Chidian reexports
    "grab",
    "mapper",
    "mapping_context",
    "DROP",
    "KEEP",
    # Core extensions
    "coalesce",
    "grab_attr",
    "to_dict",
    # FHIR extraction helpers
    "extract_ref_id",
    "extract_code",
    "extract_system",
    "extract_display",
    "parse_dt",
    "parse_date",
    "to_datetime",
    "to_date_str",
    "extract_ext",
    "extract_ext_ref",
    "extract_nested_ext",
]
