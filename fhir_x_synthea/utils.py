"""
Common utility functions shared across fhir_x_synthea modules.
"""

import re
from typing import Any


def to_str(value: Any) -> str:
    """Convert value to string, handling None and UUID types.

    Args:
        value: Any value to convert to string

    Returns:
        Stripped string representation, or empty string if None
    """
    if value is None:
        return ""
    return str(value).strip()


def split_phones(phone_str: str | None) -> list[str]:
    """Split phone string on common delimiters.

    Args:
        phone_str: Phone string potentially containing multiple numbers

    Returns:
        List of individual phone numbers
    """
    if not phone_str or phone_str.strip() == "":
        return []
    phones = re.split(r"[,;/|]", phone_str)
    return [p.strip() for p in phones if p.strip()]


def normalize_sop_code_with_prefix(sop_code: str | None) -> str | None:
    """Add urn:oid: prefix to SOP code if not present.

    Args:
        sop_code: SOP code string

    Returns:
        SOP code with urn:oid: prefix, or None if empty
    """
    if not sop_code or sop_code.strip() == "":
        return None
    sop_code = sop_code.strip()
    if sop_code.startswith("urn:oid:"):
        return sop_code
    return f"urn:oid:{sop_code}"
