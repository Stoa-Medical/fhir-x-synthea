"""
FHIR R4 → Synthea conversion modules.

Each module exposes a `convert` function for transforming FHIR resources to Synthea models.

Core resources (wired into bundle/extract orchestration):
    patient, encounter, condition, allergy

Additional converters are staged in _staged/ for future integration.

Usage:
    from fhir_x_synthea.to_synthea import patient
    synthea_patient = patient.convert(fhir_patient)
"""

from fhir_x_synthea.to_synthea import (
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
