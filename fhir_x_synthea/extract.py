"""Orchestration helper for extracting Synthea tables from FHIR Bundles."""

import logging
from typing import Any

from fhir.resources.bundle import Bundle
from synthea_pydantic import Allergy
from synthea_pydantic import Condition as SyntheaCondition
from synthea_pydantic import Encounter as SyntheaEncounter
from synthea_pydantic import Patient as SyntheaPatient

from .registry import get_converter, list_converters

logger = logging.getLogger(__name__)

# Map FHIR resource type -> (registry resource_name, table_name)
_FHIR_TYPE_TO_TABLE: dict[str, tuple[str, str]] = {
    "Patient": ("patient", "patients"),
    "Encounter": ("encounter", "encounters"),
    "Condition": ("condition", "conditions"),
    "AllergyIntolerance": ("allergy", "allergies"),
}


def extract_tables(bundle: Bundle) -> dict[str, list[Any]]:
    """Extract Synthea table rows from a FHIR Bundle.

    This function processes all resources in a FHIR Bundle and converts them
    to Synthea model instances, organized by table name.

    Args:
        bundle: FHIR Bundle containing resources to extract

    Returns:
        Dictionary mapping table names to lists of Synthea models:
        {
            "patients": [SyntheaPatient, ...],
            "encounters": [SyntheaEncounter, ...],
            "conditions": [SyntheaCondition, ...],
            "allergies": [Allergy, ...],
        }

    Example:
        >>> from fhir.resources.bundle import Bundle
        >>> bundle = Bundle.model_validate(json_data)
        >>> tables = extract_tables(bundle)
        >>> for patient in tables["patients"]:
        ...     print(patient.first, patient.last)
    """
    # Initialize all known tables
    tables: dict[str, list[Any]] = {
        table_name: [] for _, table_name in _FHIR_TYPE_TO_TABLE.values()
    }

    if not bundle.entry:
        return tables

    for entry in bundle.entry:
        resource = entry.resource
        if resource is None:
            continue

        resource_type = resource.__class__.__name__
        mapping = _FHIR_TYPE_TO_TABLE.get(resource_type)
        if mapping is None:
            logger.debug("Skipping unknown resource type: %s", resource_type)
            continue

        resource_name, table_name = mapping
        converter = get_converter("to_synthea", resource_name)
        if converter is None:
            logger.warning("No to_synthea converter for: %s", resource_name)
            continue

        result = converter.convert(resource)
        # Handle list-return converters (e.g., imaging_study)
        if isinstance(result, list):
            tables[table_name].extend(result)
        else:
            tables[table_name].append(result)

    return tables


def extract_patients(bundle: Bundle) -> list[SyntheaPatient]:
    """Extract only Patient resources from a FHIR Bundle.

    Args:
        bundle: FHIR Bundle containing resources

    Returns:
        List of Synthea Patient models
    """
    return extract_tables(bundle)["patients"]


def extract_encounters(bundle: Bundle) -> list[SyntheaEncounter]:
    """Extract only Encounter resources from a FHIR Bundle.

    Args:
        bundle: FHIR Bundle containing resources

    Returns:
        List of Synthea Encounter models
    """
    return extract_tables(bundle)["encounters"]


def extract_conditions(bundle: Bundle) -> list[SyntheaCondition]:
    """Extract only Condition resources from a FHIR Bundle.

    Args:
        bundle: FHIR Bundle containing resources

    Returns:
        List of Synthea Condition models
    """
    return extract_tables(bundle)["conditions"]


def extract_allergies(bundle: Bundle) -> list[Allergy]:
    """Extract only AllergyIntolerance resources from a FHIR Bundle.

    Args:
        bundle: FHIR Bundle containing resources

    Returns:
        List of Synthea Allergy models
    """
    return extract_tables(bundle)["allergies"]
