"""Orchestration helper for building FHIR Bundles from Synthea data."""

from fhir.resources.bundle import Bundle, BundleEntry
from synthea_pydantic import (
    Allergy,
    Condition,
    Encounter,
    Patient,
)

from .to_fhir import allergy as allergy_to_fhir
from .to_fhir import condition as condition_to_fhir
from .to_fhir import encounter as encounter_to_fhir
from .to_fhir import patient as patient_to_fhir


def patient_bundle(
    patient: Patient,
    encounters: list[Encounter] | None = None,
    conditions: list[Condition] | None = None,
    allergies: list[Allergy] | None = None,
) -> Bundle:
    """Build a FHIR Bundle for a single patient, auto-wiring references.

    This function converts Synthea resources to FHIR and automatically wires
    the patient reference into all related resources.

    Args:
        patient: Synthea Patient model
        encounters: List of Synthea Encounter models for this patient
        conditions: List of Synthea Condition models for this patient
        allergies: List of Synthea Allergy models for this patient

    Returns:
        FHIR Bundle containing all converted resources

    Example:
        >>> from synthea_pydantic import Patient, Encounter
        >>> patient = Patient(...)
        >>> encounters = [Encounter(...), Encounter(...)]
        >>> bundle = patient_bundle(patient, encounters=encounters)
    """
    encounters = encounters or []
    conditions = conditions or []
    allergies = allergies or []

    entries: list[BundleEntry] = []

    # Convert patient
    fhir_patient = patient_to_fhir.convert(patient)
    patient_ref = f"Patient/{fhir_patient.id}"
    entries.append(
        BundleEntry(
            fullUrl=f"urn:uuid:{fhir_patient.id}",
            resource=fhir_patient,
        )
    )

    # Build encounter reference map for conditions/allergies
    encounter_refs: dict[str, str] = {}

    # Convert encounters
    for enc in encounters:
        fhir_enc = encounter_to_fhir.convert(enc, patient_ref=patient_ref)
        enc_id = str(enc.id)
        encounter_refs[enc_id] = f"Encounter/{fhir_enc.id}"
        entries.append(
            BundleEntry(
                fullUrl=f"urn:uuid:{fhir_enc.id}",
                resource=fhir_enc,
            )
        )

    # Convert conditions with references
    for cond in conditions:
        enc_ref = encounter_refs.get(str(cond.encounter)) if cond.encounter else None
        fhir_cond = condition_to_fhir.convert(
            cond,
            patient_ref=patient_ref,
            encounter_ref=enc_ref,
        )
        entries.append(
            BundleEntry(
                fullUrl=f"urn:uuid:{fhir_cond.id}",
                resource=fhir_cond,
            )
        )

    # Convert allergies (allergy has patient/encounter embedded, no override needed)
    for allrgy in allergies:
        fhir_allergy = allergy_to_fhir.convert(allrgy)
        entries.append(
            BundleEntry(
                fullUrl=f"urn:uuid:{fhir_allergy.id}",
                resource=fhir_allergy,
            )
        )

    return Bundle(
        type="collection",
        entry=entries,
    )
