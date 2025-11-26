"""Orchestration helper for extracting Synthea tables from FHIR Bundles."""

from typing import Any

from fhir.resources.allergyintolerance import AllergyIntolerance
from fhir.resources.bundle import Bundle
from fhir.resources.condition import Condition
from fhir.resources.encounter import Encounter
from fhir.resources.patient import Patient
from synthea_pydantic import Allergy
from synthea_pydantic import Condition as SyntheaCondition
from synthea_pydantic import Encounter as SyntheaEncounter
from synthea_pydantic import Patient as SyntheaPatient

from .to_synthea import allergy as allergy_to_synthea
from .to_synthea import condition as condition_to_synthea
from .to_synthea import encounter as encounter_to_synthea
from .to_synthea import patient as patient_to_synthea


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
    tables: dict[str, list[Any]] = {
        "patients": [],
        "encounters": [],
        "conditions": [],
        "allergies": [],
    }

    if not bundle.entry:
        return tables

    for entry in bundle.entry:
        resource = entry.resource
        if resource is None:
            continue

        resource_type = resource.__class__.__name__

        if resource_type == "Patient" and isinstance(resource, Patient):
            synthea = patient_to_synthea.convert(resource)
            tables["patients"].append(synthea)

        elif resource_type == "Encounter" and isinstance(resource, Encounter):
            synthea = encounter_to_synthea.convert(resource)
            tables["encounters"].append(synthea)

        elif resource_type == "Condition" and isinstance(resource, Condition):
            synthea = condition_to_synthea.convert(resource)
            tables["conditions"].append(synthea)

        elif resource_type == "AllergyIntolerance" and isinstance(
            resource, AllergyIntolerance
        ):
            synthea = allergy_to_synthea.convert(resource)
            tables["allergies"].append(synthea)

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
