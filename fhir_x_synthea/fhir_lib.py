"""
Common helper functions for FHIR mapping operations.
Shared utilities used across fhir_mappers modules.
"""

from datetime import datetime
from typing import Any


def format_datetime(date_str: str | None) -> str | None:
    """
    Format a Synthea datetime string to ISO 8601 format with timezone.

    Args:
        date_str: Datetime string in Synthea format (e.g., "2020-01-15T10:30:00Z" or "2020-01-15")

    Returns:
        ISO 8601 formatted datetime string with timezone, or None if parsing fails
    """
    if not date_str or date_str.strip() == "":
        return None
    try:
        from datetime import timezone

        date_str = date_str.strip()
        # Handle Z suffix
        date_str = date_str.replace("Z", "+00:00")

        # Parse the datetime
        dt = datetime.fromisoformat(date_str)

        # Ensure timezone is present (assume UTC if missing)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.isoformat()
    except (ValueError, AttributeError):
        return None


def format_date(date_str: str | None) -> str | None:
    """
    Format a Synthea date string to YYYY-MM-DD format.

    Args:
        date_str: Date string in Synthea format

    Returns:
        Date string in YYYY-MM-DD format, or None if parsing fails
    """
    if not date_str or date_str.strip() == "":
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except (ValueError, AttributeError):
        return None


def create_reference(
    resource_type: str, resource_id: str | None
) -> dict[str, str] | None:
    """
    Create a FHIR reference object from resource type and ID.

    Args:
        resource_type: FHIR resource type (e.g., "Patient", "Encounter")
        resource_id: Resource identifier

    Returns:
        Dictionary with "reference" key in format "ResourceType/id", or None if invalid
    """
    if not resource_id or resource_id.strip() == "":
        return None
    return {"reference": f"{resource_type}/{resource_id.strip()}"}


def map_gender(gender_str: str | None) -> str | None:
    """
    Map Synthea gender code to FHIR administrative gender.

    Args:
        gender_str: Gender code ("M" or "F")

    Returns:
        FHIR gender code ("male" or "female"), or None if invalid
    """
    if not gender_str:
        return None
    gender_map = {"M": "male", "F": "female"}
    return gender_map.get(gender_str.upper().strip())


def map_marital_status(marital_str: str | None) -> dict[str, Any] | None:
    """
    Map Synthea marital status code to FHIR CodeableConcept.

    Args:
        marital_str: Marital status code ("S", "M", "D", "W")

    Returns:
        FHIR CodeableConcept with v3-MaritalStatus coding, or None if invalid
    """
    if not marital_str:
        return None
    marital_map = {
        "S": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                    "code": "S",
                    "display": "Never Married",
                }
            ]
        },
        "M": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                    "code": "M",
                    "display": "Married",
                }
            ]
        },
        "D": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                    "code": "D",
                    "display": "Divorced",
                }
            ]
        },
        "W": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                    "code": "W",
                    "display": "Widowed",
                }
            ]
        },
    }
    return marital_map.get(marital_str.upper().strip())


def normalize_allergy_category(category: str | None) -> str | None:
    """
    Normalize Synthea allergy category to FHIR allergy category.

    Args:
        category: Category string (e.g., "drug", "medication", "food", "environment")

    Returns:
        Normalized category string, or None if not in mapping
    """
    if not category:
        return None
    category_lower = category.lower().strip()
    mapping = {
        "drug": "medication",
        "medication": "medication",
        "food": "food",
        "environment": "environment",
    }
    return mapping.get(category_lower)


def create_clinical_status_coding(
    is_active: bool,
    status_system: str,
    active_code: str = "active",
    resolved_code: str = "resolved",
) -> dict[str, Any]:
    """
    Create a FHIR clinical status coding.

    Args:
        is_active: Whether the condition/allergy is active
        status_system: CodeSystem URL for the status
        active_code: Code for active status (default: "active")
        resolved_code: Code for resolved status (default: "resolved")

    Returns:
        Dictionary with "coding" array containing status coding
    """
    status_code = active_code if is_active else resolved_code
    return {
        "coding": [
            {
                "system": status_system,
                "code": status_code,
                "display": status_code.capitalize(),
            }
        ]
    }


def map_encounter_class(class_str: str | None) -> dict[str, Any] | None:
    """
    Map Synthea encounter class string to FHIR ActCode coding.

    Args:
        class_str: Encounter class string (e.g., "ambulatory", "emergency", "inpatient")

    Returns:
        Dictionary with system, code, and display, or None if not in mapping
    """
    if not class_str:
        return None
    class_lower = class_str.lower().strip()
    class_map = {
        "ambulatory": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        "emergency": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "EMER",
            "display": "emergency",
        },
        "inpatient": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "IMP",
            "display": "inpatient encounter",
        },
        "wellness": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        "urgentcare": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
    }
    return class_map.get(class_lower)


def split_name(name_str: str | None) -> tuple[str | None, str | None]:
    """
    Split a full name into given (first) and family (last) components.

    Args:
        name_str: Full name string

    Returns:
        Tuple of (given, family) names, with None for missing components
    """
    if not name_str or name_str.strip() == "":
        return None, None
    tokens = name_str.strip().split()
    if not tokens:
        return None, None
    if len(tokens) == 1:
        return tokens[0], None
    return tokens[0], tokens[-1]
