"""FHIR R4 SupplyDelivery → Synthea Supply"""

import logging
from datetime import datetime

from fhir.resources.supplydelivery import SupplyDelivery
from synthea_pydantic import Supply as SyntheaSupply

from ..chidian_ext import (
    extract_code,
    extract_display,
    extract_ext_ref,
    extract_ref_id,
    grab,
    mapper,
    parse_dt,
    to_dict,
)

logger = logging.getLogger(__name__)


@mapper(remove_empty=False)
def _to_synthea_supply(d: dict):
    """Core mapping from dict to Synthea Supply structure."""
    # Extract date (prefer occurrenceDateTime, fallback to occurrencePeriod.start)
    supply_date = None
    occurrence_dt = grab(d, "occurrenceDateTime")
    occurrence_period = grab(d, "occurrencePeriod") or {}

    date_str = None
    if occurrence_dt:
        date_str = parse_dt({"dt": occurrence_dt}, "dt")
    elif occurrence_period.get("start"):
        date_str = parse_dt({"dt": occurrence_period["start"]}, "dt")

    if date_str:
        try:
            supply_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass

    # Extract code and description from suppliedItem
    supplied_item = grab(d, "suppliedItem") or {}
    item_concept = supplied_item.get("itemCodeableConcept")
    code = ""
    description = ""
    if item_concept:
        code = extract_code({"i": item_concept}, "i", system="http://snomed.info/sct")
        description = extract_display({"i": item_concept}, "i")

    # Extract quantity
    quantity = None
    quantity_obj = supplied_item.get("quantity", {})
    if quantity_obj.get("value") is not None:
        quantity = int(quantity_obj["value"])

    return {
        "date": supply_date,
        "patient": extract_ref_id(d, "patient") or None,
        "encounter": extract_ext_ref(
            d, "http://hl7.org/fhir/StructureDefinition/resource-encounter"
        )
        or None,
        "code": code or "unknown",
        "description": description or "Unknown supply",
        "quantity": quantity,
    }


def convert(src: SupplyDelivery) -> SyntheaSupply:
    """Convert FHIR R4 SupplyDelivery to Synthea Supply.

    Args:
        src: FHIR R4 SupplyDelivery resource

    Returns:
        Synthea Supply model
    """
    return SyntheaSupply(**_to_synthea_supply(to_dict(src)))
