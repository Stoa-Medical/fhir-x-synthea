"""Synthea Encounter → FHIR R4 Encounter"""

from typing import Any

from fhir.resources.encounter import Encounter
from synthea_pydantic import Encounter as SyntheaEncounter

from ..fhir_lib import create_reference, format_datetime
from ..utils import to_str


def _map_encounter_class(class_str: str) -> dict[str, Any] | None:
    """Map Synthea encounter class string to FHIR CodeableConcept structure."""
    if not class_str:
        return None
    class_lower = class_str.lower().strip()
    class_map = {
        "ambulatory": {"code": "AMB", "display": "ambulatory"},
        "emergency": {"code": "EMER", "display": "emergency"},
        "inpatient": {"code": "IMP", "display": "inpatient encounter"},
        "wellness": {"code": "AMB", "display": "ambulatory"},
        "urgentcare": {"code": "AMB", "display": "ambulatory"},
    }
    mapping = class_map.get(class_lower)
    if not mapping:
        return None
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                **mapping,
            }
        ]
    }


def convert(
    src: SyntheaEncounter,
    *,
    patient_ref: str | None = None,
    provider_ref: str | None = None,
    organization_ref: str | None = None,
) -> Encounter:
    """Convert Synthea Encounter to FHIR R4 Encounter.

    Args:
        src: Synthea Encounter model
        patient_ref: Optional patient reference (e.g., "Patient/123")
        provider_ref: Optional provider reference (e.g., "Practitioner/456")
        organization_ref: Optional organization reference (e.g., "Organization/789")

    Returns:
        FHIR R4 Encounter resource
    """
    d = src.model_dump()

    # Extract and process fields (synthea_pydantic uses lowercase keys)
    encounter_id = to_str(d.get("id"))
    start = to_str(d.get("start"))
    stop = to_str(d.get("stop"))
    patient_id = to_str(d.get("patient"))
    organization_id = to_str(d.get("organization"))
    provider_id = to_str(d.get("provider"))
    encounter_class = to_str(d.get("encounterclass"))
    code = to_str(d.get("code"))
    description = to_str(d.get("description"))
    reason_code = to_str(d.get("reasoncode"))
    reason_description = to_str(d.get("reasondescription"))
    payer_id = to_str(d.get("payer"))

    # Handle numeric fields
    base_cost = d.get("base_encounter_cost")
    total_cost = d.get("total_claim_cost")
    payer_coverage = d.get("payer_coverage")

    # Determine status based on stop field
    status = "completed" if stop else "in-progress"

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Encounter",
        "status": status,
    }

    # Set id if present (generate if not)
    if encounter_id:
        resource["id"] = encounter_id
    else:
        resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")
        if resource_id and resource_id != "--":
            resource["id"] = resource_id

    # Set actualPeriod (fhir.resources 8.x uses actualPeriod instead of period)
    actual_period: dict[str, Any] = {}
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            actual_period["start"] = iso_start
    if stop:
        iso_stop = format_datetime(stop)
        if iso_stop:
            actual_period["end"] = iso_stop
    if actual_period:
        resource["actualPeriod"] = actual_period

    # Set subject (patient) reference - use override or from source
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )
    if effective_patient_ref:
        resource["subject"] = {"reference": effective_patient_ref}

    # Set serviceProvider (organization) reference - use override or from source
    effective_org_ref = organization_ref or (
        f"Organization/{organization_id}" if organization_id else None
    )
    if effective_org_ref:
        resource["serviceProvider"] = {"reference": effective_org_ref}

    # Set participant (provider) - fhir.resources 8.x uses actor instead of individual
    effective_provider_ref = provider_ref or (
        f"Practitioner/{provider_id}" if provider_id else None
    )
    if effective_provider_ref:
        resource["participant"] = [{"actor": {"reference": effective_provider_ref}}]

    # Set class_fhir (fhir.resources uses class_fhir, expects list of CodeableConcept)
    class_coding = _map_encounter_class(encounter_class)
    if class_coding:
        resource["class_fhir"] = [class_coding]

    # Set type (SNOMED CT)
    if code or description:
        type_obj: dict[str, Any] = {}
        if code:
            coding = {"system": "http://snomed.info/sct", "code": code}
            if description:
                coding["display"] = description
            type_obj["coding"] = [coding]
        if description:
            type_obj["text"] = description
        if type_obj:
            resource["type"] = [type_obj]

    # Set reason (R4B uses reason with CodeableReference structure)
    if reason_code or reason_description:
        concept: dict[str, Any] = {}
        if reason_code:
            coding = {"system": "http://snomed.info/sct", "code": reason_code}
            if reason_description:
                coding["display"] = reason_description
            concept["coding"] = [coding]
        if reason_description:
            concept["text"] = reason_description
        if concept:
            resource["reason"] = [{"value": [{"concept": concept}]}]

    # Set extensions for payer and costs
    extensions: list[dict[str, Any]] = []

    # Payer extension
    if payer_id:
        payer_ref_obj = create_reference("Organization", payer_id)
        if payer_ref_obj:
            extensions.append(
                {
                    "url": "http://example.org/fhir/StructureDefinition/encounter-payer",
                    "valueReference": payer_ref_obj,
                }
            )

    # Cost extensions
    if base_cost is not None:
        extensions.append(
            {
                "url": "http://example.org/fhir/StructureDefinition/encounter-baseCost",
                "valueDecimal": float(base_cost),
            }
        )

    if total_cost is not None:
        extensions.append(
            {
                "url": "http://example.org/fhir/StructureDefinition/encounter-totalClaimCost",
                "valueDecimal": float(total_cost),
            }
        )

    if payer_coverage is not None:
        extensions.append(
            {
                "url": "http://example.org/fhir/StructureDefinition/encounter-payerCoverage",
                "valueDecimal": float(payer_coverage),
            }
        )

    if extensions:
        resource["extension"] = extensions

    return Encounter(**resource)
