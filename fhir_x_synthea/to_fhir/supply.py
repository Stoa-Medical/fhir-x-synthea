"""Synthea Supply → FHIR R4 SupplyDelivery"""

from typing import Any

from fhir.resources.supplydelivery import SupplyDelivery
from synthea_pydantic import Supply as SyntheaSupply

from ..fhir_lib import format_datetime
from ..utils import to_str


def convert(
    src: SyntheaSupply,
    *,
    patient_ref: str | None = None,
) -> SupplyDelivery:
    """Convert Synthea Supply to FHIR R4 SupplyDelivery.

    Args:
        src: Synthea Supply model
        patient_ref: Optional patient reference (e.g., "Patient/123")

    Returns:
        FHIR R4 SupplyDelivery resource
    """
    d = src.model_dump()

    # Extract fields
    date = to_str(d.get("date"))
    patient_id = to_str(d.get("patient"))
    encounter_id = to_str(d.get("encounter"))
    code = to_str(d.get("code"))
    description = to_str(d.get("description"))
    quantity = d.get("quantity")

    # Generate resource ID
    resource_id = f"supply-{patient_id}-{date}-{code}".replace(" ", "-").replace(
        ":", "-"
    )

    # Build resource
    resource: dict[str, Any] = {
        "resourceType": "SupplyDelivery",
        "id": resource_id,
        "status": "completed",
    }

    # Set occurrence
    if date:
        iso_date = format_datetime(date)
        if iso_date:
            resource["occurrenceDateTime"] = iso_date

    # Set patient reference
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )
    if effective_patient_ref:
        resource["patient"] = {"reference": effective_patient_ref}

    # Set encounter via extension
    if encounter_id:
        resource["extension"] = [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/resource-encounter",
                "valueReference": {"reference": f"Encounter/{encounter_id}"},
            }
        ]

    # Set suppliedItem
    supplied_item: dict[str, Any] = {}
    if code or description:
        item_code: dict[str, Any] = {}
        if code:
            item_code["coding"] = [
                {
                    "system": "http://snomed.info/sct",
                    "code": code,
                    "display": description or None,
                }
            ]
        if description:
            item_code["text"] = description
        supplied_item["itemCodeableConcept"] = item_code

    if quantity is not None:
        supplied_item["quantity"] = {"value": float(quantity)}

    if supplied_item:
        resource["suppliedItem"] = supplied_item

    return SupplyDelivery(**resource)
