"""
FHIR R4 → Synthea conversion modules.

Each module exposes a `convert` function for transforming FHIR resources to Synthea models.

Usage:
    from fhir_x_synthea.to_synthea import patient
    synthea_patient = patient.convert(fhir_patient)
"""

from fhir_x_synthea.to_synthea import (
    allergy,
    careplan,
    claims,
    claims_transactions,
    condition,
    device,
    encounter,
    imaging_study,
    medication,
    organization,
    patient,
    payer,
    payer_transitions,
    supply,
)

__all__ = [
    "allergy",
    "careplan",
    "claims",
    "claims_transactions",
    "condition",
    "device",
    "encounter",
    "imaging_study",
    "medication",
    "organization",
    "patient",
    "payer",
    "payer_transitions",
    "supply",
]
