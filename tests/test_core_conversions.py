"""Tests for core conversion functions (Patient, Encounter, Condition, Allergy)."""

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
from fhir_x_synthea.to_synthea import condition as condition_to_synthea
from fhir_x_synthea.to_synthea import encounter as encounter_to_synthea
from fhir_x_synthea.to_synthea import patient as patient_to_synthea
from fhir_x_synthea.types import extract_id_from_ref, extract_ref, make_ref


# -- Reference helpers --------------------------------------------------------


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


# -- Synthea → FHIR ----------------------------------------------------------


class TestToFhirPatient:
    def test_convert_returns_fhir_patient(self, sample_patient):
        result = patient_to_fhir.convert(sample_patient)
        assert isinstance(result, Patient)

    def test_convert_preserves_id(self, sample_patient):
        result = patient_to_fhir.convert(sample_patient)
        assert result.id == str(sample_patient.id)

    def test_convert_maps_gender(self, sample_patient):
        result = patient_to_fhir.convert(sample_patient)
        assert result.gender == "male"

    def test_convert_creates_name(self, sample_patient):
        result = patient_to_fhir.convert(sample_patient)
        assert result.name is not None
        assert len(result.name) > 0
        assert result.name[0].family == "Smith"
        assert result.name[0].given[0] == "John"

    def test_convert_maps_birthdate(self, sample_patient):
        result = patient_to_fhir.convert(sample_patient)
        assert result.birthDate is not None
        assert str(result.birthDate) == "1965-11-05"


class TestToFhirEncounter:
    def test_convert_returns_fhir_encounter(self, sample_encounter_1):
        result = encounter_to_fhir.convert(sample_encounter_1)
        assert isinstance(result, Encounter)

    def test_convert_preserves_id(self, sample_encounter_1):
        result = encounter_to_fhir.convert(sample_encounter_1)
        assert result.id == str(sample_encounter_1.id)

    def test_convert_with_patient_ref_override(self, sample_encounter_1):
        result = encounter_to_fhir.convert(
            sample_encounter_1, patient_ref="Patient/custom-123"
        )
        assert result.subject is not None
        assert result.subject.reference == "Patient/custom-123"

    def test_convert_uses_source_patient(self, sample_encounter_1):
        result = encounter_to_fhir.convert(sample_encounter_1)
        expected_ref = f"Patient/{sample_encounter_1.patient}"
        assert result.subject.reference == expected_ref

    def test_convert_maps_period(self, sample_encounter_1):
        result = encounter_to_fhir.convert(sample_encounter_1)
        assert result.actualPeriod is not None
        assert result.actualPeriod.start is not None


class TestToFhirCondition:
    def test_convert_returns_fhir_condition(self, sample_condition):
        result = condition_to_fhir.convert(sample_condition)
        assert isinstance(result, Condition)

    def test_convert_has_clinical_status(self, sample_condition):
        result = condition_to_fhir.convert(sample_condition)
        assert result.clinicalStatus is not None

    def test_active_condition_is_active(self, sample_condition):
        result = condition_to_fhir.convert(sample_condition)
        codes = [c.code for c in result.clinicalStatus.coding]
        assert "active" in codes

    def test_resolved_condition_is_resolved(self, sample_condition_resolved):
        result = condition_to_fhir.convert(sample_condition_resolved)
        codes = [c.code for c in result.clinicalStatus.coding]
        assert "resolved" in codes

    def test_convert_with_encounter_ref(self, sample_condition):
        result = condition_to_fhir.convert(
            sample_condition, encounter_ref="Encounter/enc-456"
        )
        assert result.encounter is not None
        assert result.encounter.reference == "Encounter/enc-456"


class TestToFhirAllergy:
    def test_convert_returns_fhir_allergy(self, sample_allergy):
        result = allergy_to_fhir.convert(sample_allergy)
        assert isinstance(result, AllergyIntolerance)

    def test_convert_maps_code(self, sample_allergy):
        result = allergy_to_fhir.convert(sample_allergy)
        assert result.code is not None
        assert result.code.coding is not None
        assert result.code.coding[0].code == "7980"

    def test_convert_maps_patient_ref(self, sample_allergy):
        result = allergy_to_fhir.convert(sample_allergy)
        assert result.patient is not None
        assert str(sample_allergy.patient) in result.patient.reference


# -- FHIR → Synthea (roundtrip) ----------------------------------------------


class TestToSyntheaPatient:
    def test_roundtrip_preserves_name(self, sample_patient):
        fhir = patient_to_fhir.convert(sample_patient)
        roundtripped = patient_to_synthea.convert(fhir)
        assert roundtripped.first == sample_patient.first
        assert roundtripped.last == sample_patient.last

    def test_roundtrip_preserves_gender(self, sample_patient):
        fhir = patient_to_fhir.convert(sample_patient)
        roundtripped = patient_to_synthea.convert(fhir)
        assert roundtripped.gender == sample_patient.gender

    def test_roundtrip_preserves_id(self, sample_patient):
        fhir = patient_to_fhir.convert(sample_patient)
        roundtripped = patient_to_synthea.convert(fhir)
        assert str(roundtripped.id) == str(sample_patient.id)


class TestToSyntheaEncounter:
    def test_roundtrip_preserves_id(self, sample_encounter_1):
        fhir = encounter_to_fhir.convert(sample_encounter_1)
        roundtripped = encounter_to_synthea.convert(fhir)
        assert str(roundtripped.id) == str(sample_encounter_1.id)

    def test_roundtrip_preserves_patient(self, sample_encounter_1):
        fhir = encounter_to_fhir.convert(sample_encounter_1)
        roundtripped = encounter_to_synthea.convert(fhir)
        assert str(roundtripped.patient) == str(sample_encounter_1.patient)

    def test_roundtrip_preserves_code(self, sample_encounter_1):
        fhir = encounter_to_fhir.convert(sample_encounter_1)
        roundtripped = encounter_to_synthea.convert(fhir)
        assert roundtripped.code == sample_encounter_1.code


class TestToSyntheaCondition:
    def test_roundtrip_preserves_code(self, sample_condition):
        fhir = condition_to_fhir.convert(sample_condition)
        roundtripped = condition_to_synthea.convert(fhir)
        assert roundtripped.code == sample_condition.code


class TestToSyntheaAllergy:
    def test_roundtrip_preserves_code(self, sample_allergy):
        fhir = allergy_to_fhir.convert(sample_allergy)
        roundtripped = allergy_to_synthea.convert(fhir)
        assert roundtripped.code == sample_allergy.code

    def test_roundtrip_preserves_description(self, sample_allergy):
        fhir = allergy_to_fhir.convert(sample_allergy)
        roundtripped = allergy_to_synthea.convert(fhir)
        assert roundtripped.description == sample_allergy.description

    def test_roundtrip_preserves_patient(self, sample_allergy):
        fhir = allergy_to_fhir.convert(sample_allergy)
        roundtripped = allergy_to_synthea.convert(fhir)
        assert str(roundtripped.patient) == str(sample_allergy.patient)
