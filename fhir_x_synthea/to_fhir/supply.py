"""Synthea Supply → FHIR R4 SupplyDelivery"""

from fhir.resources.supplydelivery import SupplyDelivery
from synthea_pydantic import Supply as SyntheaSupply

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import format_datetime


def _resource_id(d: dict) -> str:
    """Generate deterministic resource ID."""
    patient_id = grab(d, "patient") or ""
    date = grab(d, "date") or ""
    code = grab(d, "code") or ""
    return f"supply-{patient_id}-{date}-{code}".replace(" ", "-").replace(":", "-")


def _encounter_extension(encounter_id: str | None):
    """Build encounter reference extension."""
    if not encounter_id:
        return None
    return [
        {
            "url": "http://hl7.org/fhir/StructureDefinition/resource-encounter",
            "valueReference": {"reference": f"Encounter/{encounter_id}"},
        }
    ]


def _supplied_item(d: dict) -> dict | None:
    """Build suppliedItem structure."""
    code = grab(d, "code")
    description = grab(d, "description")
    quantity = grab(d, "quantity")

    result: dict = {}

    if code or description:
        item_code = {}
        if code:
            coding = {"system": "http://snomed.info/sct", "code": code}
            if description:
                coding["display"] = description
            item_code["coding"] = [coding]
        if description:
            item_code["text"] = description
        if item_code:
            result["itemCodeableConcept"] = item_code

    if quantity is not None:
        result["quantity"] = {"value": float(quantity)}

    return result if result else None


@mapper
def _to_fhir_supply(d: dict, patient_ref: str | None = None):
    """Core mapping from dict to FHIR SupplyDelivery structure."""
    patient_id = grab(d, "patient")
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )

    return {
        "resourceType": "SupplyDelivery",
        "id": _resource_id(d),
        "status": "completed",
        "occurrenceDateTime": grab(d, "date", apply=format_datetime),
        "patient": {"reference": effective_patient_ref}
        if effective_patient_ref
        else None,
        "extension": _encounter_extension(grab(d, "encounter")),
        "suppliedItem": _supplied_item(d),
    }


def convert(src: SyntheaSupply, *, patient_ref: str | None = None) -> SupplyDelivery:
    """Convert Synthea Supply to FHIR R4 SupplyDelivery.

    Args:
        src: Synthea Supply model
        patient_ref: Optional patient reference (e.g., "Patient/123")

    Returns:
        FHIR R4 SupplyDelivery resource
    """
    return SupplyDelivery(**_to_fhir_supply(to_dict(src), patient_ref))
