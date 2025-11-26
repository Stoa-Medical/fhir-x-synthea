"""
Synthea → FHIR R4 conversion modules.

Each module exposes a `convert` function for transforming Synthea models to FHIR resources.

Usage:
    from fhir_x_synthea.to_fhir import patient
    fhir_patient = patient.convert(synthea_patient)
"""

from fhir_x_synthea.to_fhir import (
    allergy,
    careplan,
    claims,
    claims_transactions,
    condition,
    device,
    encounter,
    imaging_study,
    immunization,
    medication,
    observation,
    organization,
    patient,
    payer,
    payer_transitions,
    procedure,
    provider,
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
    "immunization",
    "medication",
    "observation",
    "organization",
    "patient",
    "payer",
    "payer_transitions",
    "procedure",
    "provider",
    "supply",
]
