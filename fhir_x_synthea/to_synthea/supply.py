"""
Mapping function for converting FHIR SupplyDelivery resources to Synthea supplies.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_extension_reference,
    extract_reference_id,
    parse_datetime_to_date,
)


def map_fhir_supply_delivery_to_csv(fhir_resource: dict[str, Any]) -> dict[str, Any]:
    """
    Map a FHIR R4 SupplyDelivery resource to a Synthea supplies.csv row.

    Args:
        fhir_resource: Dictionary representing a FHIR SupplyDelivery resource

    Returns:
        Dictionary with CSV column names as keys (DATE, PATIENT, ENCOUNTER, etc.)
    """

    # Initialize CSV row
    csv_row: dict[str, str] = {
        "DATE": "",
        "PATIENT": "",
        "ENCOUNTER": "",
        "CODE": "",
        "DESCRIPTION": "",
        "QUANTITY": "",
    }

    # Extract DATE (prefer occurrenceDateTime, fallback to occurrencePeriod.start)
    occurrence_date_time = fhir_resource.get("occurrenceDateTime")
    occurrence_period = fhir_resource.get("occurrencePeriod", {})

    if occurrence_date_time:
        csv_row["DATE"] = parse_datetime_to_date(occurrence_date_time)
    elif occurrence_period.get("start"):
        csv_row["DATE"] = parse_datetime_to_date(occurrence_period["start"])

    # Extract PATIENT reference
    patient = fhir_resource.get("patient")
    if patient:
        csv_row["PATIENT"] = extract_reference_id(patient)

    # Extract ENCOUNTER from extension
    csv_row["ENCOUNTER"] = extract_extension_reference(
        fhir_resource, "http://hl7.org/fhir/StructureDefinition/resource-encounter"
    )

    # Extract CODE and DESCRIPTION from suppliedItem
    supplied_item = fhir_resource.get("suppliedItem", {})
    item_codeable_concept = supplied_item.get("itemCodeableConcept")
    if item_codeable_concept:
        csv_row["CODE"] = extract_coding_code(
            item_codeable_concept, "http://snomed.info/sct"
        )
        csv_row["DESCRIPTION"] = extract_display_or_text(item_codeable_concept)

    # Extract QUANTITY
    quantity = supplied_item.get("quantity", {})
    quantity_value = quantity.get("value")
    if quantity_value is not None:
        csv_row["QUANTITY"] = str(quantity_value)

    return csv_row
