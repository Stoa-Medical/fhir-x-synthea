"""FHIR R4 SupplyDelivery → Synthea Supply"""

import logging
from datetime import datetime

from fhir.resources.supplydelivery import SupplyDelivery
from synthea_pydantic import Supply as SyntheaSupply

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_extension_reference,
    extract_reference_id,
    parse_datetime,
)

logger = logging.getLogger(__name__)


def convert(src: SupplyDelivery) -> SyntheaSupply:
    """Convert FHIR R4 SupplyDelivery to Synthea Supply.

    Args:
        src: FHIR R4 SupplyDelivery resource

    Returns:
        Synthea Supply model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract DATE (prefer occurrenceDateTime, fallback to occurrencePeriod.start)
    supply_date = None
    occurrence_date_time = fhir_resource.get("occurrenceDateTime")
    occurrence_period = fhir_resource.get("occurrencePeriod", {})

    if occurrence_date_time:
        date_str = parse_datetime(occurrence_date_time)
        if date_str:
            try:
                supply_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                pass
    elif occurrence_period.get("start"):
        date_str = parse_datetime(occurrence_period["start"])
        if date_str:
            try:
                supply_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

    # Extract PATIENT reference
    patient = ""
    patient_ref = fhir_resource.get("patient")
    if patient_ref:
        patient = extract_reference_id(patient_ref)

    # Extract ENCOUNTER from extension
    encounter = extract_extension_reference(
        fhir_resource, "http://hl7.org/fhir/StructureDefinition/resource-encounter"
    )

    # Extract CODE and DESCRIPTION from suppliedItem
    code = ""
    description = ""
    supplied_item = fhir_resource.get("suppliedItem", {})
    item_codeable_concept = supplied_item.get("itemCodeableConcept")
    if item_codeable_concept:
        code = extract_coding_code(
            item_codeable_concept, preferred_system="http://snomed.info/sct"
        )
        description = extract_display_or_text(item_codeable_concept)

    # Extract QUANTITY
    quantity = None
    quantity_obj = supplied_item.get("quantity", {})
    quantity_value = quantity_obj.get("value")
    if quantity_value is not None:
        quantity = int(quantity_value)

    return SyntheaSupply(
        date=supply_date,
        patient=patient or None,
        encounter=encounter or None,
        code=code or "unknown",
        description=description or "Unknown supply",
        quantity=quantity,
    )
