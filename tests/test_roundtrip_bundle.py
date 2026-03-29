"""Roundtrip validation tests for bundle orchestration.

Tests the core throughline: Synthea CSV → FHIR Bundle → Synthea CSV.
"""

import pytest
from synthea_pydantic import Allergy, Condition, Encounter, Patient

from fhir_x_synthea import extract_tables, patient_bundle


class TestPatientBundle:
    """Test patient_bundle() creates valid FHIR bundles."""

    def test_creates_bundle_with_patient(self, sample_patient):
        bundle = patient_bundle(sample_patient)

        assert bundle.type == "collection"
        assert bundle.entry is not None
        assert len(bundle.entry) >= 1
        assert bundle.entry[0].resource.__class__.__name__ == "Patient"

    def test_creates_bundle_with_encounters(
        self, sample_patient, sample_encounters
    ):
        bundle = patient_bundle(sample_patient, encounters=sample_encounters)
        assert len(bundle.entry) == 1 + len(sample_encounters)

    def test_bundle_wires_patient_references(
        self, sample_patient, sample_encounter_1
    ):
        bundle = patient_bundle(sample_patient, encounters=[sample_encounter_1])

        encounter_entry = bundle.entry[1]
        enc_resource = encounter_entry.resource
        assert enc_resource.subject is not None
        assert f"Patient/{sample_patient.id}" in enc_resource.subject.reference

    def test_bundle_with_conditions(self, sample_patient, sample_condition):
        bundle = patient_bundle(sample_patient, conditions=[sample_condition])
        assert len(bundle.entry) == 2  # patient + condition

    def test_bundle_with_allergies(self, sample_patient, sample_allergy):
        bundle = patient_bundle(sample_patient, allergies=[sample_allergy])
        assert len(bundle.entry) == 2  # patient + allergy

    def test_full_bundle(
        self,
        sample_patient,
        sample_encounters,
        sample_condition,
        sample_allergy,
    ):
        bundle = patient_bundle(
            sample_patient,
            encounters=sample_encounters,
            conditions=[sample_condition],
            allergies=[sample_allergy],
        )
        expected = 1 + len(sample_encounters) + 1 + 1
        assert len(bundle.entry) == expected


class TestExtractTables:
    """Test extract_tables() extracts from bundles we generate."""

    def test_extracts_patient(self, sample_patient):
        bundle = patient_bundle(sample_patient)
        tables = extract_tables(bundle)

        assert "patients" in tables
        assert len(tables["patients"]) == 1
        extracted = tables["patients"][0]
        assert extracted.first == sample_patient.first
        assert extracted.last == sample_patient.last

    def test_extracts_encounters(self, sample_patient, sample_encounters):
        bundle = patient_bundle(sample_patient, encounters=sample_encounters)
        tables = extract_tables(bundle)
        assert len(tables["encounters"]) == len(sample_encounters)

    def test_extracts_conditions(self, sample_patient, sample_condition):
        bundle = patient_bundle(sample_patient, conditions=[sample_condition])
        tables = extract_tables(bundle)
        assert len(tables["conditions"]) == 1

    def test_extracts_allergies(self, sample_patient, sample_allergy):
        bundle = patient_bundle(sample_patient, allergies=[sample_allergy])
        tables = extract_tables(bundle)
        assert len(tables["allergies"]) == 1


class TestRoundtrip:
    """Test full roundtrip: Synthea CSV → FHIR Bundle → Synthea tables."""

    def test_patient_survives_roundtrip(self, sample_patient):
        bundle = patient_bundle(sample_patient)
        tables = extract_tables(bundle)
        roundtrip = tables["patients"][0]

        assert roundtrip.first == sample_patient.first
        assert roundtrip.last == sample_patient.last
        assert roundtrip.gender == sample_patient.gender
        assert str(roundtrip.id) == str(sample_patient.id)

    def test_encounter_survives_roundtrip(
        self, sample_patient, sample_encounter_1
    ):
        bundle = patient_bundle(sample_patient, encounters=[sample_encounter_1])
        tables = extract_tables(bundle)
        roundtrip = tables["encounters"][0]

        assert roundtrip.code == sample_encounter_1.code
        assert str(roundtrip.id) == str(sample_encounter_1.id)

    def test_condition_survives_roundtrip(
        self, sample_patient, sample_condition
    ):
        bundle = patient_bundle(sample_patient, conditions=[sample_condition])
        tables = extract_tables(bundle)
        roundtrip = tables["conditions"][0]

        assert roundtrip.code == sample_condition.code

    def test_allergy_survives_roundtrip(self, sample_patient, sample_allergy):
        bundle = patient_bundle(sample_patient, allergies=[sample_allergy])
        tables = extract_tables(bundle)
        roundtrip = tables["allergies"][0]

        assert roundtrip.code == sample_allergy.code

    def test_full_roundtrip_preserves_counts(
        self,
        sample_patient,
        sample_encounters,
        sample_condition,
        sample_allergy,
    ):
        bundle = patient_bundle(
            sample_patient,
            encounters=sample_encounters,
            conditions=[sample_condition],
            allergies=[sample_allergy],
        )
        tables = extract_tables(bundle)

        assert len(tables["patients"]) == 1
        assert len(tables["encounters"]) == len(sample_encounters)
        assert len(tables["conditions"]) == 1
        assert len(tables["allergies"]) == 1
