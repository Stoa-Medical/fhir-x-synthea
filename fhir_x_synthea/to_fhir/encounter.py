"""Synthea Encounter → FHIR R4 Encounter"""

from fhir.resources.encounter import Encounter
from synthea_pydantic import Encounter as SyntheaEncounter

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import (
    codeable_concept,
    format_datetime,
    period,
    ref,
)


def _encounter_class(class_str: str | None):
    """Map encounter class to FHIR CodeableConcept."""
    if not class_str:
        return None

    class_map = {
        "ambulatory": {"code": "AMB", "display": "ambulatory"},
        "emergency": {"code": "EMER", "display": "emergency"},
        "inpatient": {"code": "IMP", "display": "inpatient encounter"},
        "wellness": {"code": "AMB", "display": "ambulatory"},
        "urgentcare": {"code": "AMB", "display": "ambulatory"},
    }

    mapping = class_map.get(class_str.lower().strip())
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


def _reason(reason_code: str | None, reason_desc: str | None) -> list | None:
    """Build encounter reason structure (R4B CodeableReference)."""
    if not reason_code and not reason_desc:
        return None

    concept: dict = {}
    if reason_code:
        coding = {"system": "http://snomed.info/sct", "code": reason_code}
        if reason_desc:
            coding["display"] = reason_desc
        concept["coding"] = [coding]
    if reason_desc:
        concept["text"] = reason_desc

    if not concept:
        return None

    return [{"value": [{"concept": concept}]}]


def _cost_extensions(d: dict) -> list | None:
    """Build cost-related extensions."""
    payer_id = grab(d, "payer")
    base_cost = grab(d, "base_encounter_cost")
    total_cost = grab(d, "total_claim_cost")
    payer_coverage = grab(d, "payer_coverage")

    extensions: list = []

    if payer_id:
        payer_ref = ref("Organization", payer_id)
        if payer_ref is not None:
            extensions.append(
                {
                    "url": "http://example.org/fhir/StructureDefinition/encounter-payer",
                    "valueReference": payer_ref,
                }
            )

    if base_cost is not None:
        extensions.append(
            dict(
                url="http://example.org/fhir/StructureDefinition/encounter-baseCost",
                valueDecimal=float(base_cost),
            )
        )

    if total_cost is not None:
        extensions.append(
            dict(
                url="http://example.org/fhir/StructureDefinition/encounter-totalClaimCost",
                valueDecimal=float(total_cost),
            )
        )

    if payer_coverage is not None:
        extensions.append(
            dict(
                url="http://example.org/fhir/StructureDefinition/encounter-payerCoverage",
                valueDecimal=float(payer_coverage),
            )
        )

    return extensions if extensions else None


@mapper
def _to_fhir_encounter(
    d: dict,
    patient_ref: str | None = None,
    provider_ref: str | None = None,
    organization_ref: str | None = None,
):
    """Core mapping from dict to FHIR Encounter structure."""
    encounter_id = grab(d, "id")
    patient_id = grab(d, "patient")
    provider_id = grab(d, "provider")
    organization_id = grab(d, "organization")
    start = grab(d, "start")
    stop = grab(d, "stop")

    # Generate ID if not present
    if not encounter_id:
        code = grab(d, "code") or ""
        resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")
        encounter_id = resource_id if resource_id != "--" else None

    # Determine status
    status = "completed" if stop else "in-progress"

    # Build effective references (overrides or from source)
    eff_patient_ref = patient_ref or (f"Patient/{patient_id}" if patient_id else None)
    eff_provider_ref = provider_ref or (
        f"Practitioner/{provider_id}" if provider_id else None
    )
    eff_org_ref = organization_ref or (
        f"Organization/{organization_id}" if organization_id else None
    )

    # Build period
    actual_period = period(
        format_datetime(start) if start else None,
        format_datetime(stop) if stop else None,
    )

    # Build encounter class
    enc_class = _encounter_class(grab(d, "encounterclass"))

    # Build type
    code_val = grab(d, "code")
    desc = grab(d, "description")
    type_obj = codeable_concept(
        system="http://snomed.info/sct",
        code=code_val,
        display=desc,
        text=desc,
    )

    return {
        "resourceType": "Encounter",
        "id": encounter_id,
        "status": status,
        "class_fhir": [enc_class] if enc_class else None,
        "type": [type_obj] if type_obj else None,
        "subject": ref(
            "Patient", eff_patient_ref.split("/")[-1] if eff_patient_ref else None
        ),
        "participant": [{"actor": {"reference": eff_provider_ref}}]
        if eff_provider_ref
        else None,
        "serviceProvider": ref(
            "Organization", eff_org_ref.split("/")[-1] if eff_org_ref else None
        ),
        "actualPeriod": actual_period,
        "reason": _reason(grab(d, "reasoncode"), grab(d, "reasondescription")),
        "extension": _cost_extensions(d),
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
    return Encounter(
        **_to_fhir_encounter(
            to_dict(src),
            patient_ref,
            provider_ref,
            organization_ref,
        )
    )
