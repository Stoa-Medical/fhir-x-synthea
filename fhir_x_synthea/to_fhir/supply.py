"""
Mapping function for converting Synthea supplies.csv rows to FHIR SupplyDelivery resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime


def map_supply_delivery(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea supplies.csv row to a FHIR R4 SupplyDelivery resource.

    Args:
        csv_row: Dictionary with keys like DATE, PATIENT, ENCOUNTER, CODE, DESCRIPTION, QUANTITY

    Returns:
        Dictionary representing a FHIR SupplyDelivery resource
    """

    # Extract and process fields
    date = csv_row.get("DATE", "").strip() if csv_row.get("DATE") else ""
    patient_id = csv_row.get("PATIENT", "").strip() if csv_row.get("PATIENT") else ""
    encounter_id = (
        csv_row.get("ENCOUNTER", "").strip() if csv_row.get("ENCOUNTER") else ""
    )
    code = csv_row.get("CODE", "").strip() if csv_row.get("CODE") else ""
    description = (
        csv_row.get("DESCRIPTION", "").strip() if csv_row.get("DESCRIPTION") else ""
    )
    quantity_str = (
        csv_row.get("QUANTITY", "").strip() if csv_row.get("QUANTITY") else ""
    )

    # Parse quantity
    quantity = None
    if quantity_str:
        try:
            quantity = float(quantity_str)
        except (ValueError, TypeError):
            pass

    # Generate resource ID
    resource_id = f"supply-{patient_id}-{date}-{code}".replace(" ", "-").replace(
        ":", "-"
    )

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "SupplyDelivery",
        "id": resource_id,
        "status": "completed",
    }

    # Set occurrenceDateTime from DATE
    if date:
        iso_date = format_datetime(date)
        if iso_date:
            resource["occurrenceDateTime"] = iso_date

    # Set patient reference
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["patient"] = patient_ref

    # Set encounter reference via extension
    if encounter_id:
        encounter_ref = create_reference("Encounter", encounter_id)
        if encounter_ref:
            resource.setdefault("extension", []).append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/resource-encounter",
                    "valueReference": encounter_ref,
                }
            )

    # Set suppliedItem
    supplied_item: dict[str, Any] = {}

    # Set itemCodeableConcept
    if code or description:
        item_code: dict[str, Any] = {}
        if code:
            coding = {"system": "http://snomed.info/sct", "code": code}
            if description:
                coding["display"] = description
            item_code["coding"] = [coding]
        if description:
            item_code["text"] = description
        if item_code:
            supplied_item["itemCodeableConcept"] = item_code

    # Set quantity
    if quantity is not None:
        supplied_item["quantity"] = {"value": quantity}

    if supplied_item:
        resource["suppliedItem"] = supplied_item

    return resource
