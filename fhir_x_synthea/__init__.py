"""
FHIR x Synthea: Bidirectional mapping library between FHIR R4 and Synthea formats.

Usage:
    # Individual converters
    from fhir_x_synthea import to_fhir, to_synthea
    fhir_patient = to_fhir.patient.convert(synthea_patient)
    synthea_patient = to_synthea.patient.convert(fhir_patient)

    # Orchestration helpers
    from fhir_x_synthea import patient_bundle, extract_tables
    bundle = patient_bundle(patient, encounters=encounters, conditions=conditions)
    tables = extract_tables(bundle)

    # Reference helpers
    from fhir_x_synthea import make_ref, extract_ref, extract_id_from_ref
"""

__version__ = "0.1.0"

from fhir_x_synthea import to_fhir, to_synthea
from fhir_x_synthea.bundle import patient_bundle
from fhir_x_synthea.extract import (
    extract_allergies,
    extract_conditions,
    extract_encounters,
    extract_patients,
    extract_tables,
)
from fhir_x_synthea.types import extract_id_from_ref, extract_ref, make_ref

__all__ = [
    # Conversion modules
    "to_fhir",
    "to_synthea",
    # Orchestration helpers
    "patient_bundle",
    "extract_tables",
    "extract_patients",
    "extract_encounters",
    "extract_conditions",
    "extract_allergies",
    # Reference helpers
    "make_ref",
    "extract_ref",
    "extract_id_from_ref",
]
