"""Tests for the converter registry."""

from fhir_x_synthea.registry import (
    FHIR_VERSION,
    get_converter,
    get_converter_meta,
    list_converters,
    list_resource_names,
)


class TestGetConverter:
    def test_returns_module_for_known_converter(self):
        mod = get_converter("to_fhir", "patient")
        assert mod is not None
        assert hasattr(mod, "convert")
        assert callable(mod.convert)

    def test_returns_none_for_unknown_resource(self):
        assert get_converter("to_fhir", "nonexistent") is None

    def test_returns_none_for_unknown_direction(self):
        assert get_converter("to_omop", "patient") is None

    def test_to_synthea_patient_works(self):
        mod = get_converter("to_synthea", "patient")
        assert mod is not None
        assert hasattr(mod, "convert")


class TestGetConverterMeta:
    def test_returns_meta_for_known_converter(self):
        meta = get_converter_meta("to_fhir", "patient")
        assert meta is not None
        assert "module_path" in meta
        assert "fhir_type" in meta
        assert meta["fhir_type"] == "Patient"

    def test_returns_none_for_unknown(self):
        assert get_converter_meta("to_fhir", "nonexistent") is None


class TestListConverters:
    def test_lists_all_converters(self):
        all_converters = list_converters()
        assert len(all_converters) >= 8  # 4 to_fhir + 4 to_synthea minimum

    def test_filters_by_direction(self):
        to_fhir = list_converters(direction="to_fhir")
        to_synthea = list_converters(direction="to_synthea")
        assert all(c["direction"] == "to_fhir" for c in to_fhir)
        assert all(c["direction"] == "to_synthea" for c in to_synthea)

    def test_includes_fhir_version(self):
        converters = list_converters()
        for c in converters:
            assert c["fhir_version"] == FHIR_VERSION


class TestListResourceNames:
    def test_lists_names(self):
        names = list_resource_names()
        assert "patient" in names
        assert "encounter" in names
        assert "condition" in names
        assert "allergy" in names

    def test_filters_by_direction(self):
        to_fhir_names = list_resource_names(direction="to_fhir")
        assert "patient" in to_fhir_names


class TestFhirVersion:
    def test_version_is_r4b(self):
        assert FHIR_VERSION == "R4B"
