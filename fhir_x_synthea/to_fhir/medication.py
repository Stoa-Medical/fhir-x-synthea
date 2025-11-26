"""Synthea Medication → FHIR R4 MedicationRequest"""

from typing import Any

from fhir.resources.medicationrequest import MedicationRequest
from synthea_pydantic import Medication as SyntheaMedication

from ..fhir_lib import format_datetime
from ..utils import to_str


def convert(
    src: SyntheaMedication,
    *,
    patient_ref: str | None = None,
    encounter_ref: str | None = None,
) -> MedicationRequest:
    """Convert Synthea Medication to FHIR R4 MedicationRequest.

    Args:
        src: Synthea Medication model
        patient_ref: Optional patient reference (e.g., "Patient/123")
        encounter_ref: Optional encounter reference (e.g., "Encounter/456")

    Returns:
        FHIR R4 MedicationRequest resource
    """
    d = src.model_dump()

    # Extract fields
    start = to_str(d.get("start"))
    stop = to_str(d.get("stop"))
    patient_id = to_str(d.get("patient"))
    encounter_id = to_str(d.get("encounter"))
    payer_id = to_str(d.get("payer"))
    code = to_str(d.get("code"))
    description = to_str(d.get("description"))
    dispenses = d.get("dispenses")
    reason_code = to_str(d.get("reasoncode"))
    reason_description = to_str(d.get("reasondescription"))
    base_cost = d.get("base_cost")
    payer_coverage = d.get("payer_coverage")
    total_cost = d.get("totalcost")

    # Determine status
    status = "active" if not stop else "completed"

    # Generate resource ID
    resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")

    # Build resource
    resource: dict[str, Any] = {
        "resourceType": "MedicationRequest",
        "id": resource_id,
        "status": status,
        "intent": "order",
    }

    # Set authoredOn
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            resource["authoredOn"] = iso_start

    # Set subject reference
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )
    if effective_patient_ref:
        resource["subject"] = {"reference": effective_patient_ref}

    # Set encounter reference
    effective_encounter_ref = encounter_ref or (
        f"Encounter/{encounter_id}" if encounter_id else None
    )
    if effective_encounter_ref:
        resource["encounter"] = {"reference": effective_encounter_ref}

    # Set insurance reference
    if payer_id:
        resource["insurance"] = [{"reference": f"Coverage/{payer_id}"}]

    # Set medication (RxNorm)
    if code or description:
        medication_code: dict[str, Any] = {}
        if code:
            medication_code["coding"] = [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": code,
                    "display": description or None,
                }
            ]
        if description:
            medication_code["text"] = description
        resource["medication"] = {"concept": medication_code}

    # Set dispense request
    if dispenses is not None:
        resource["dispenseRequest"] = {"numberOfRepeatsAllowed": int(dispenses)}

    # Set reason (R4B uses reason with CodeableReference)
    if reason_code or reason_description:
        concept: dict[str, Any] = {}
        if reason_code:
            concept["coding"] = [
                {
                    "system": "http://snomed.info/sct",
                    "code": reason_code,
                    "display": reason_description or None,
                }
            ]
        if reason_description:
            concept["text"] = reason_description
        resource["reason"] = [{"concept": concept}]

    # Set financial extensions
    extensions = []
    if base_cost is not None:
        extensions.append(
            {
                "url": "http://synthea.org/fhir/StructureDefinition/medication-baseCost",
                "valueDecimal": float(base_cost),
            }
        )
    if payer_coverage is not None:
        extensions.append(
            {
                "url": "http://synthea.org/fhir/StructureDefinition/medication-payerCoverage",
                "valueDecimal": float(payer_coverage),
            }
        )
    if total_cost is not None:
        extensions.append(
            {
                "url": "http://synthea.org/fhir/StructureDefinition/medication-totalCost",
                "valueDecimal": float(total_cost),
            }
        )
    if extensions:
        resource["extension"] = extensions

    return MedicationRequest(**resource)
