"""
Synthea → FHIR R4 conversion modules.

Each module exposes a `convert` function for transforming Synthea models to FHIR resources.

Core resources (wired into bundle/extract orchestration):
    patient, encounter, condition, allergy

Additional converters are staged in _staged/ for future integration.

Usage:
    from fhir_x_synthea.to_fhir import patient
    fhir_patient = patient.convert(synthea_patient)
"""

from fhir_x_synthea.to_fhir import (
    allergy,
    condition,
    encounter,
    patient,
)

__all__ = [
    "allergy",
    "condition",
    "encounter",
    "patient",
]
