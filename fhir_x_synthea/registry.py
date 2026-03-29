"""
Converter registry for fhir-x-synthea.

Static manifest of all available converters with metadata for agent-driven discovery.
Each entry points to a module; the agent discovers functions via dir() + callable().

Non-uniform semantics handled:
- claims_transactions to_fhir: has convert() AND convert_response()
- imaging_study to_synthea: convert() returns list, not single model
- payer and organization to_fhir: both target FHIR Organization

Usage:
    from fhir_x_synthea.registry import get_converter, list_converters

    # Get a specific converter module
    mod = get_converter("to_fhir", "patient")
    if mod:
        result = mod.convert(synthea_patient)

    # List all converters
    for entry in list_converters(direction="to_fhir"):
        print(entry["resource_name"], entry["module"])
"""

import importlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

# FHIR version contract
FHIR_VERSION = "R4B"

# Static manifest: direction -> resource_name -> metadata
# Each entry has:
#   module_path: importable module path
#   fhir_type: target FHIR resource type(s)
#   notes: any non-uniform semantics
_MANIFEST: dict[str, dict[str, dict[str, Any]]] = {
    "to_fhir": {
        "patient": {
            "module_path": "fhir_x_synthea.to_fhir.patient",
            "fhir_type": "Patient",
        },
        "encounter": {
            "module_path": "fhir_x_synthea.to_fhir.encounter",
            "fhir_type": "Encounter",
        },
        "condition": {
            "module_path": "fhir_x_synthea.to_fhir.condition",
            "fhir_type": "Condition",
        },
        "allergy": {
            "module_path": "fhir_x_synthea.to_fhir.allergy",
            "fhir_type": "AllergyIntolerance",
        },
        "careplan": {
            "module_path": "fhir_x_synthea.to_fhir.careplan",
            "fhir_type": "CarePlan",
        },
        "claims": {
            "module_path": "fhir_x_synthea.to_fhir.claims",
            "fhir_type": "Claim",
        },
        "claims_transactions": {
            "module_path": "fhir_x_synthea.to_fhir.claims_transactions",
            "fhir_type": ["Claim", "ClaimResponse"],
            "notes": "Has convert() -> Claim and convert_response() -> ClaimResponse",
        },
        "device": {
            "module_path": "fhir_x_synthea.to_fhir.device",
            "fhir_type": "Device",
        },
        "imaging_study": {
            "module_path": "fhir_x_synthea.to_fhir.imaging_study",
            "fhir_type": "ImagingStudy",
        },
        "immunization": {
            "module_path": "fhir_x_synthea.to_fhir.immunization",
            "fhir_type": "Immunization",
        },
        "medication": {
            "module_path": "fhir_x_synthea.to_fhir.medication",
            "fhir_type": "MedicationRequest",
        },
        "observation": {
            "module_path": "fhir_x_synthea.to_fhir.observation",
            "fhir_type": "Observation",
        },
        "organization": {
            "module_path": "fhir_x_synthea.to_fhir.organization",
            "fhir_type": "Organization",
            "notes": "Synthea Organization -> FHIR Organization",
        },
        "payer": {
            "module_path": "fhir_x_synthea.to_fhir.payer",
            "fhir_type": "Organization",
            "notes": "Synthea Payer -> FHIR Organization (insurance type)",
        },
        "payer_transitions": {
            "module_path": "fhir_x_synthea.to_fhir.payer_transitions",
            "fhir_type": "Coverage",
        },
        "procedure": {
            "module_path": "fhir_x_synthea.to_fhir.procedure",
            "fhir_type": "Procedure",
        },
        "provider": {
            "module_path": "fhir_x_synthea.to_fhir.provider",
            "fhir_type": "Practitioner",
        },
        "supply": {
            "module_path": "fhir_x_synthea.to_fhir.supply",
            "fhir_type": "SupplyDelivery",
        },
    },
    "to_synthea": {
        "patient": {
            "module_path": "fhir_x_synthea.to_synthea.patient",
            "fhir_type": "Patient",
        },
        "encounter": {
            "module_path": "fhir_x_synthea.to_synthea.encounter",
            "fhir_type": "Encounter",
        },
        "condition": {
            "module_path": "fhir_x_synthea.to_synthea.condition",
            "fhir_type": "Condition",
        },
        "allergy": {
            "module_path": "fhir_x_synthea.to_synthea.allergy",
            "fhir_type": "AllergyIntolerance",
        },
        "careplan": {
            "module_path": "fhir_x_synthea.to_synthea.careplan",
            "fhir_type": "CarePlan",
        },
        "claims": {
            "module_path": "fhir_x_synthea.to_synthea.claims",
            "fhir_type": "Claim",
        },
        "claims_transactions": {
            "module_path": "fhir_x_synthea.to_synthea.claims_transactions",
            "fhir_type": ["Claim", "ClaimResponse"],
            "notes": "Has convert() and convert_response(), requires both Claim + ClaimResponse",
        },
        "device": {
            "module_path": "fhir_x_synthea.to_synthea.device",
            "fhir_type": "Device",
        },
        "imaging_study": {
            "module_path": "fhir_x_synthea.to_synthea.imaging_study",
            "fhir_type": "ImagingStudy",
            "notes": "convert() returns list[SyntheaImagingStudy], one per series-instance pair",
        },
        "medication": {
            "module_path": "fhir_x_synthea.to_synthea.medication",
            "fhir_type": "MedicationRequest",
        },
        "organization": {
            "module_path": "fhir_x_synthea.to_synthea.organization",
            "fhir_type": "Organization",
        },
        "payer": {
            "module_path": "fhir_x_synthea.to_synthea.payer",
            "fhir_type": "Organization",
            "notes": "FHIR Organization (insurance type) -> Synthea Payer",
        },
        "payer_transitions": {
            "module_path": "fhir_x_synthea.to_synthea.payer_transitions",
            "fhir_type": "Coverage",
        },
        "supply": {
            "module_path": "fhir_x_synthea.to_synthea.supply",
            "fhir_type": "SupplyDelivery",
        },
        "immunization": {
            "module_path": "fhir_x_synthea.to_synthea.immunization",
            "fhir_type": "Immunization",
        },
        "observation": {
            "module_path": "fhir_x_synthea.to_synthea.observation",
            "fhir_type": "Observation",
        },
        "procedure": {
            "module_path": "fhir_x_synthea.to_synthea.procedure",
            "fhir_type": "Procedure",
        },
        "provider": {
            "module_path": "fhir_x_synthea.to_synthea.provider",
            "fhir_type": "Practitioner",
        },
    },
}

# Cache of loaded modules
_loaded: dict[str, Any] = {}


def _load_module(module_path: str) -> Any | None:
    """Import a converter module, caching the result."""
    if module_path in _loaded:
        return _loaded[module_path]
    try:
        mod = importlib.import_module(module_path)
        _loaded[module_path] = mod
        logger.debug("Loaded converter: %s", module_path)
        return mod
    except Exception:
        logger.warning("Failed to load converter: %s", module_path, exc_info=True)
        _loaded[module_path] = None
        return None


def get_converter(direction: str, resource_name: str) -> Any | None:
    """Get a converter module by direction and resource name.

    Args:
        direction: "to_fhir" or "to_synthea"
        resource_name: e.g. "patient", "encounter", "claims"

    Returns:
        The converter module (with convert() function), or None if not found.
    """
    entry = _MANIFEST.get(direction, {}).get(resource_name)
    if entry is None:
        return None
    return _load_module(entry["module_path"])


def get_converter_meta(direction: str, resource_name: str) -> dict[str, Any] | None:
    """Get metadata for a converter without loading the module.

    Returns:
        Metadata dict with module_path, fhir_type, notes, etc. or None.
    """
    return _MANIFEST.get(direction, {}).get(resource_name)


def list_converters(direction: str | None = None) -> list[dict[str, Any]]:
    """List all registered converters with metadata.

    Args:
        direction: Optional filter. "to_fhir", "to_synthea", or None for all.

    Returns:
        List of dicts with direction, resource_name, and metadata.
    """
    results = []
    directions = [direction] if direction else list(_MANIFEST.keys())
    for d in directions:
        for resource_name, meta in _MANIFEST.get(d, {}).items():
            results.append({
                "direction": d,
                "resource_name": resource_name,
                "fhir_version": FHIR_VERSION,
                **meta,
            })
    return results


def list_resource_names(direction: str | None = None) -> list[str]:
    """List all registered resource names.

    Args:
        direction: Optional filter.

    Returns:
        Sorted list of unique resource names.
    """
    names = set()
    directions = [direction] if direction else list(_MANIFEST.keys())
    for d in directions:
        names.update(_MANIFEST.get(d, {}).keys())
    return sorted(names)
