"""FHIR R4 Immunization -> Synthea Immunization"""

from fhir.resources.immunization import Immunization
from synthea_pydantic import Immunization as SyntheaImmunization

from ..chidian_ext import (
    extract_code,
    extract_display,
    extract_ext,
    extract_ref_id,
    grab,
    mapper,
    parse_date,
    to_dict,
)


@mapper(remove_empty=False)
def _to_synthea_immunization(d: dict):
    """Core mapping from FHIR Immunization dict to Synthea structure."""
    return {
        "date": parse_date(d, "occurrenceDateTime") or None,
        "patient": extract_ref_id(d, "patient") or None,
        "encounter": extract_ref_id(d, "encounter") or None,
        "code": extract_code(d, "vaccineCode", system="http://hl7.org/fhir/sid/cvx") or None,
        "description": extract_display(d, "vaccineCode") or None,
        "base_cost": extract_ext(
            d,
            "http://synthea.mitre.org/fhir/StructureDefinition/immunization-cost",
            "valueDecimal",
            None,
        ),
    }


def convert(src: Immunization) -> SyntheaImmunization:
    """Convert FHIR R4 Immunization to Synthea Immunization.

    Args:
        src: FHIR R4 Immunization resource

    Returns:
        Synthea Immunization model
    """
    return SyntheaImmunization(**_to_synthea_immunization(to_dict(src)))
