"""
Shared types and reference helpers for FHIR x Synthea conversions.
"""

from typing import TypeAlias

from fhir.resources.reference import Reference

# Reference string format: "{ResourceType}/{id}"
RefString: TypeAlias = str


def make_ref(ref_string: RefString | None) -> Reference | None:
    """Convert 'Patient/123' to a FHIR Reference, or None if input is None."""
    if ref_string is None:
        return None
    return Reference(reference=ref_string)


def extract_ref(ref: Reference | None) -> RefString | None:
    """Extract reference string from FHIR Reference, or None."""
    if ref is None:
        return None
    return ref.reference


def extract_id_from_ref(ref: Reference | None) -> str | None:
    """Extract just the ID from a FHIR Reference.

    Reference(reference='Patient/123') → '123'
    """
    ref_str = extract_ref(ref)
    if ref_str is None:
        return None
    return ref_str.split("/")[-1] if "/" in ref_str else ref_str
