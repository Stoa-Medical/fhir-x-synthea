"""Tests for core conversion functions."""

import csv
from pathlib import Path

import pytest
from fhir.resources.allergyintolerance import AllergyIntolerance
from fhir.resources.condition import Condition
from fhir.resources.encounter import Encounter
from fhir.resources.patient import Patient
from synthea_pydantic import Allergy
from synthea_pydantic import Condition as SyntheaCondition
from synthea_pydantic import Encounter as SyntheaEncounter
from synthea_pydantic import Patient as SyntheaPatient

from fhir_x_synthea.to_fhir import allergy as allergy_to_fhir
from fhir_x_synthea.to_fhir import condition as condition_to_fhir
from fhir_x_synthea.to_fhir import encounter as encounter_to_fhir
from fhir_x_synthea.to_fhir import patient as patient_to_fhir
from fhir_x_synthea.to_synthea import allergy as allergy_to_synthea
from fhir_x_synthea.to_synthea import encounter as encounter_to_synthea
from fhir_x_synthea.types import extract_id_from_ref, extract_ref, make_ref


# Fixtures for loading test data
@pytest.fixture(scope="module")
def data_dir() -> Path:
    return Path(__file__).parent / "data" / "synthea_csv"


@pytest.fixture(scope="module")
def sample_patient_row(data_dir: Path) -> dict[str, str]:
    with open(data_dir / "patients.csv", newline="") as f:
        reader = csv.DictReader(f)
        return next(reader)


@pytest.fixture(scope="module")
def sample_encounter_row(data_dir: Path) -> dict[str, str]:
    with open(data_dir / "encounters.csv", newline="") as f:
        reader = csv.DictReader(f)
        return next(reader)


@pytest.fixture(scope="module")
def sample_condition_row(data_dir: Path) -> dict[str, str]:
    with open(data_dir / "conditions.csv", newline="") as f:
        reader = csv.DictReader(f)
        return next(reader)


@pytest.fixture(scope="module")
def sample_allergy_row(data_dir: Path) -> dict[str, str]:
    with open(data_dir / "allergies.csv", newline="") as f:
        reader = csv.DictReader(f)
        return next(reader)


# Test types module
class TestTypes:
    def test_make_ref_none(self):
        assert make_ref(None) is None

    def test_make_ref_creates_reference(self):
        ref = make_ref("Patient/123")
        assert ref is not None
        assert ref.reference == "Patient/123"

    def test_extract_ref_none(self):
        assert extract_ref(None) is None

    def test_extract_ref_returns_string(self):
        ref = make_ref("Encounter/456")
        assert extract_ref(ref) == "Encounter/456"

    def test_extract_id_from_ref(self):
        ref = make_ref("Patient/abc-123")
        assert extract_id_from_ref(ref) == "abc-123"

    def test_extract_id_from_ref_none(self):
        assert extract_id_from_ref(None) is None


# Test to_fhir conversions
class TestToFhirPatient:
    def test_convert_returns_fhir_patient(self, sample_patient_row):
        synthea_patient = SyntheaPatient(**sample_patient_row)
        result = patient_to_fhir.convert(synthea_patient)

        assert isinstance(result, Patient)

    def test_convert_preserves_id(self, sample_patient_row):
        synthea_patient = SyntheaPatient(**sample_patient_row)
        result = patient_to_fhir.convert(synthea_patient)

        assert result.id == sample_patient_row["Id"]

    def test_convert_maps_gender(self, sample_patient_row):
        synthea_patient = SyntheaPatient(**sample_patient_row)
        result = patient_to_fhir.convert(synthea_patient)

        expected_gender = "male" if sample_patient_row["GENDER"] == "M" else "female"
        assert result.gender == expected_gender

    def test_convert_creates_name(self, sample_patient_row):
        synthea_patient = SyntheaPatient(**sample_patient_row)
        result = patient_to_fhir.convert(synthea_patient)

        assert result.name is not None
        assert len(result.name) > 0
        assert result.name[0].family == sample_patient_row["LAST"]


class TestToFhirEncounter:
    def test_convert_returns_fhir_encounter(self, sample_encounter_row):
        synthea_encounter = SyntheaEncounter(**sample_encounter_row)
        result = encounter_to_fhir.convert(synthea_encounter)

        assert isinstance(result, Encounter)

    def test_convert_preserves_id(self, sample_encounter_row):
        synthea_encounter = SyntheaEncounter(**sample_encounter_row)
        result = encounter_to_fhir.convert(synthea_encounter)

        assert result.id == sample_encounter_row["Id"]

    def test_convert_with_patient_ref_override(self, sample_encounter_row):
        synthea_encounter = SyntheaEncounter(**sample_encounter_row)
        result = encounter_to_fhir.convert(
            synthea_encounter, patient_ref="Patient/custom-123"
        )

        assert result.subject is not None
        assert result.subject.reference == "Patient/custom-123"

    def test_convert_uses_source_patient_when_no_override(self, sample_encounter_row):
        synthea_encounter = SyntheaEncounter(**sample_encounter_row)
        result = encounter_to_fhir.convert(synthea_encounter)

        expected_ref = f"Patient/{sample_encounter_row['PATIENT']}"
        assert result.subject.reference == expected_ref


class TestToFhirCondition:
    def test_convert_returns_fhir_condition(self, sample_condition_row):
        synthea_condition = SyntheaCondition(**sample_condition_row)
        result = condition_to_fhir.convert(synthea_condition)

        assert isinstance(result, Condition)

    def test_convert_has_clinical_status(self, sample_condition_row):
        synthea_condition = SyntheaCondition(**sample_condition_row)
        result = condition_to_fhir.convert(synthea_condition)

        assert result.clinicalStatus is not None

    def test_convert_with_encounter_ref(self, sample_condition_row):
        synthea_condition = SyntheaCondition(**sample_condition_row)
        result = condition_to_fhir.convert(
            synthea_condition, encounter_ref="Encounter/enc-456"
        )

        assert result.encounter is not None
        assert result.encounter.reference == "Encounter/enc-456"


class TestToFhirAllergy:
    def test_convert_returns_fhir_allergy(self, sample_allergy_row):
        synthea_allergy = Allergy(**sample_allergy_row)
        result = allergy_to_fhir.convert(synthea_allergy)

        assert isinstance(result, AllergyIntolerance)

    def test_convert_maps_code(self, sample_allergy_row):
        synthea_allergy = Allergy(**sample_allergy_row)
        result = allergy_to_fhir.convert(synthea_allergy)

        assert result.code is not None
        assert result.code.coding is not None
        assert result.code.coding[0].code == sample_allergy_row["CODE"]


# Test to_synthea conversions
class TestToSyntheaAllergy:
    def test_convert_returns_synthea_allergy(self, sample_allergy_row):
        # First convert to FHIR
        synthea_allergy = Allergy(**sample_allergy_row)
        fhir_allergy = allergy_to_fhir.convert(synthea_allergy)

        # Then convert back
        result = allergy_to_synthea.convert(fhir_allergy)

        assert isinstance(result, Allergy)

    def test_roundtrip_preserves_code(self, sample_allergy_row):
        original = Allergy(**sample_allergy_row)
        fhir = allergy_to_fhir.convert(original)
        roundtripped = allergy_to_synthea.convert(fhir)

        assert roundtripped.code == original.code

    def test_roundtrip_preserves_description(self, sample_allergy_row):
        original = Allergy(**sample_allergy_row)
        fhir = allergy_to_fhir.convert(original)
        roundtripped = allergy_to_synthea.convert(fhir)

        assert roundtripped.description == original.description

    def test_roundtrip_preserves_patient(self, sample_allergy_row):
        original = Allergy(**sample_allergy_row)
        fhir = allergy_to_fhir.convert(original)
        roundtripped = allergy_to_synthea.convert(fhir)

        assert roundtripped.patient == original.patient


class TestToSyntheaEncounter:
    def test_convert_returns_synthea_encounter(self, sample_encounter_row):
        # First convert to FHIR
        synthea_encounter = SyntheaEncounter(**sample_encounter_row)
        fhir_encounter = encounter_to_fhir.convert(synthea_encounter)

        # Then convert back
        result = encounter_to_synthea.convert(fhir_encounter)

        assert isinstance(result, SyntheaEncounter)

    def test_roundtrip_preserves_id(self, sample_encounter_row):
        original = SyntheaEncounter(**sample_encounter_row)
        fhir = encounter_to_fhir.convert(original)
        roundtripped = encounter_to_synthea.convert(fhir)

        assert str(roundtripped.id) == str(original.id)

    def test_roundtrip_preserves_patient(self, sample_encounter_row):
        original = SyntheaEncounter(**sample_encounter_row)
        fhir = encounter_to_fhir.convert(original)
        roundtripped = encounter_to_synthea.convert(fhir)

        assert str(roundtripped.patient) == str(original.patient)

    def test_roundtrip_preserves_code(self, sample_encounter_row):
        original = SyntheaEncounter(**sample_encounter_row)
        fhir = encounter_to_fhir.convert(original)
        roundtripped = encounter_to_synthea.convert(fhir)

        assert roundtripped.code == original.code


# Integration test: Process multiple rows
class TestBatchConversion:
    def test_convert_multiple_patients(self, data_dir: Path):
        with open(data_dir / "patients.csv", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)[:10]  # First 10 patients

        for row in rows:
            synthea = SyntheaPatient(**row)
            fhir = patient_to_fhir.convert(synthea)
            assert isinstance(fhir, Patient)
            assert fhir.id == row["Id"]

    def test_convert_multiple_encounters(self, data_dir: Path):
        with open(data_dir / "encounters.csv", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)[:10]  # First 10 encounters

        for row in rows:
            synthea = SyntheaEncounter(**row)
            fhir = encounter_to_fhir.convert(synthea)
            assert isinstance(fhir, Encounter)

    def test_convert_multiple_allergies_roundtrip(self, data_dir: Path):
        with open(data_dir / "allergies.csv", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)[:10]  # First 10 allergies

        for row in rows:
            original = Allergy(**row)
            fhir = allergy_to_fhir.convert(original)
            roundtripped = allergy_to_synthea.convert(fhir)

            assert roundtripped.code == original.code
            assert roundtripped.patient == original.patient
