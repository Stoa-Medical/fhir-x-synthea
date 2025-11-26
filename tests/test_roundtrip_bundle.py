"""Roundtrip validation tests for bundle orchestration."""

import csv
from pathlib import Path

import pytest
from synthea_pydantic import (
    Allergy,
    Condition,
    Encounter,
    Patient,
)

from fhir_x_synthea import extract_tables, patient_bundle


@pytest.fixture(scope="module")
def data_dir() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def synthea_csv_dir(data_dir: Path) -> Path:
    return data_dir / "synthea_csv"


@pytest.fixture(scope="module")
def sample_patient(synthea_csv_dir: Path) -> Patient:
    """Load first patient from CSV."""
    with open(synthea_csv_dir / "patients.csv", newline="") as f:
        row = next(csv.DictReader(f))
    return Patient(**row)


@pytest.fixture(scope="module")
def sample_patient_encounters(
    synthea_csv_dir: Path, sample_patient: Patient
) -> list[Encounter]:
    """Load encounters for sample patient."""
    patient_id = str(sample_patient.id)
    encounters = []
    with open(synthea_csv_dir / "encounters.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["PATIENT"] == patient_id:
                encounters.append(Encounter(**row))
    return encounters


@pytest.fixture(scope="module")
def sample_patient_conditions(
    synthea_csv_dir: Path, sample_patient: Patient
) -> list[Condition]:
    """Load conditions for sample patient."""
    patient_id = str(sample_patient.id)
    conditions = []
    with open(synthea_csv_dir / "conditions.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["PATIENT"] == patient_id:
                conditions.append(Condition(**row))
    return conditions


@pytest.fixture(scope="module")
def sample_patient_allergies(
    synthea_csv_dir: Path, sample_patient: Patient
) -> list[Allergy]:
    """Load allergies for sample patient."""
    patient_id = str(sample_patient.id)
    allergies = []
    with open(synthea_csv_dir / "allergies.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["PATIENT"] == patient_id:
                allergies.append(Allergy(**row))
    return allergies


class TestPatientBundle:
    """Test patient_bundle() creates valid FHIR bundles."""

    def test_creates_bundle_with_patient(self, sample_patient: Patient):
        bundle = patient_bundle(sample_patient)

        assert bundle.type == "collection"
        assert bundle.entry is not None
        assert len(bundle.entry) >= 1
        # First entry should be patient
        assert bundle.entry[0].resource.__class__.__name__ == "Patient"

    def test_creates_bundle_with_encounters(
        self, sample_patient: Patient, sample_patient_encounters: list[Encounter]
    ):
        encounters = sample_patient_encounters[:5]  # Limit for speed
        bundle = patient_bundle(sample_patient, encounters=encounters)

        assert len(bundle.entry) == 1 + len(encounters)

    def test_bundle_wires_patient_references(
        self, sample_patient: Patient, sample_patient_encounters: list[Encounter]
    ):
        if not sample_patient_encounters:
            pytest.skip("No encounters for patient")

        bundle = patient_bundle(
            sample_patient, encounters=[sample_patient_encounters[0]]
        )

        # Check encounter has patient reference
        encounter_entry = bundle.entry[1]
        enc_resource = encounter_entry.resource
        assert enc_resource.subject is not None
        assert f"Patient/{sample_patient.id}" in enc_resource.subject.reference

    def test_bundle_with_conditions(
        self, sample_patient: Patient, sample_patient_conditions: list[Condition]
    ):
        conditions = sample_patient_conditions[:5]
        bundle = patient_bundle(sample_patient, conditions=conditions)

        expected_count = 1 + len(conditions)
        assert len(bundle.entry) == expected_count

    def test_bundle_with_allergies(
        self, sample_patient: Patient, sample_patient_allergies: list[Allergy]
    ):
        allergies = sample_patient_allergies[:5]
        bundle = patient_bundle(sample_patient, allergies=allergies)

        expected_count = 1 + len(allergies)
        assert len(bundle.entry) == expected_count

    def test_full_bundle(
        self,
        sample_patient: Patient,
        sample_patient_encounters: list[Encounter],
        sample_patient_conditions: list[Condition],
        sample_patient_allergies: list[Allergy],
    ):
        bundle = patient_bundle(
            sample_patient,
            encounters=sample_patient_encounters[:3],
            conditions=sample_patient_conditions[:3],
            allergies=sample_patient_allergies[:3],
        )

        # Count should match
        enc_count = min(3, len(sample_patient_encounters))
        cond_count = min(3, len(sample_patient_conditions))
        allergy_count = min(3, len(sample_patient_allergies))
        expected = 1 + enc_count + cond_count + allergy_count
        assert len(bundle.entry) == expected


class TestExtractTables:
    """Test extract_tables() extracts from bundles we generate."""

    def test_extracts_patient(self, sample_patient: Patient):
        bundle = patient_bundle(sample_patient)
        tables = extract_tables(bundle)

        assert "patients" in tables
        assert len(tables["patients"]) == 1
        extracted = tables["patients"][0]
        assert extracted.first == sample_patient.first
        assert extracted.last == sample_patient.last

    def test_extracts_encounters(
        self, sample_patient: Patient, sample_patient_encounters: list[Encounter]
    ):
        encounters = sample_patient_encounters[:5]
        bundle = patient_bundle(sample_patient, encounters=encounters)
        tables = extract_tables(bundle)

        assert len(tables["encounters"]) == len(encounters)

    def test_extracts_conditions(
        self, sample_patient: Patient, sample_patient_conditions: list[Condition]
    ):
        conditions = sample_patient_conditions[:5]
        bundle = patient_bundle(sample_patient, conditions=conditions)
        tables = extract_tables(bundle)

        assert len(tables["conditions"]) == len(conditions)

    def test_extracts_allergies(
        self, sample_patient: Patient, sample_patient_allergies: list[Allergy]
    ):
        allergies = sample_patient_allergies[:5]
        bundle = patient_bundle(sample_patient, allergies=allergies)
        tables = extract_tables(bundle)

        assert len(tables["allergies"]) == len(allergies)


class TestRoundtrip:
    """Test full roundtrip: Synthea CSV -> FHIR Bundle -> Synthea tables."""

    def test_patient_survives_roundtrip(self, sample_patient: Patient):
        """Key patient fields survive Synthea -> FHIR -> Synthea roundtrip."""
        bundle = patient_bundle(sample_patient)
        tables = extract_tables(bundle)
        roundtrip = tables["patients"][0]

        assert roundtrip.first == sample_patient.first
        assert roundtrip.last == sample_patient.last
        assert roundtrip.gender == sample_patient.gender
        assert str(roundtrip.id) == str(sample_patient.id)

    def test_encounter_survives_roundtrip(
        self, sample_patient: Patient, sample_patient_encounters: list[Encounter]
    ):
        """Encounter fields survive roundtrip."""
        if not sample_patient_encounters:
            pytest.skip("No encounters for patient")

        original = sample_patient_encounters[0]
        bundle = patient_bundle(sample_patient, encounters=[original])
        tables = extract_tables(bundle)
        roundtrip = tables["encounters"][0]

        assert roundtrip.code == original.code
        assert str(roundtrip.id) == str(original.id)

    def test_condition_survives_roundtrip(
        self, sample_patient: Patient, sample_patient_conditions: list[Condition]
    ):
        """Condition fields survive roundtrip."""
        if not sample_patient_conditions:
            pytest.skip("No conditions for patient")

        original = sample_patient_conditions[0]
        bundle = patient_bundle(sample_patient, conditions=[original])
        tables = extract_tables(bundle)
        roundtrip = tables["conditions"][0]

        assert roundtrip.code == original.code

    def test_allergy_survives_roundtrip(
        self, sample_patient: Patient, sample_patient_allergies: list[Allergy]
    ):
        """Allergy fields survive roundtrip."""
        if not sample_patient_allergies:
            pytest.skip("No allergies for patient")

        original = sample_patient_allergies[0]
        bundle = patient_bundle(sample_patient, allergies=[original])
        tables = extract_tables(bundle)
        roundtrip = tables["allergies"][0]

        assert roundtrip.code == original.code

    def test_full_roundtrip_preserves_counts(
        self,
        sample_patient: Patient,
        sample_patient_encounters: list[Encounter],
        sample_patient_conditions: list[Condition],
        sample_patient_allergies: list[Allergy],
    ):
        """Full roundtrip preserves resource counts."""
        enc = sample_patient_encounters[:5]
        cond = sample_patient_conditions[:5]
        allrg = sample_patient_allergies[:5]

        bundle = patient_bundle(
            sample_patient,
            encounters=enc,
            conditions=cond,
            allergies=allrg,
        )
        tables = extract_tables(bundle)

        assert len(tables["patients"]) == 1
        assert len(tables["encounters"]) == len(enc)
        assert len(tables["conditions"]) == len(cond)
        assert len(tables["allergies"]) == len(allrg)
