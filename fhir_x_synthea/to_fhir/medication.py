"""
Mapping function for converting Synthea medications.csv rows to FHIR MedicationRequest resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime


def map_medication(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea medications.csv row to a FHIR R4 MedicationRequest resource.

    Args:
        csv_row: Dictionary with keys like Start, Stop, Patient, Encounter, Payer,
                Code, Description, Dispenses, ReasonCode, ReasonDescription,
                Base_Cost, Payer_Coverage, TotalCost

    Returns:
        Dictionary representing a FHIR MedicationRequest resource
    """

    # Extract and process fields
    start = csv_row.get("Start", "").strip() if csv_row.get("Start") else ""
    stop = csv_row.get("Stop", "").strip() if csv_row.get("Stop") else ""
    patient_id = csv_row.get("Patient", "").strip() if csv_row.get("Patient") else ""
    encounter_id = (
        csv_row.get("Encounter", "").strip() if csv_row.get("Encounter") else ""
    )
    payer_id = csv_row.get("Payer", "").strip() if csv_row.get("Payer") else ""
    code = csv_row.get("Code", "").strip() if csv_row.get("Code") else ""
    description = (
        csv_row.get("Description", "").strip() if csv_row.get("Description") else ""
    )
    dispenses_str = (
        csv_row.get("Dispenses", "").strip() if csv_row.get("Dispenses") else ""
    )
    reason_code = (
        csv_row.get("ReasonCode", "").strip() if csv_row.get("ReasonCode") else ""
    )
    reason_description = (
        csv_row.get("ReasonDescription", "").strip()
        if csv_row.get("ReasonDescription")
        else ""
    )
    base_cost_str = (
        csv_row.get("Base_Cost", "").strip() if csv_row.get("Base_Cost") else ""
    )
    payer_coverage_str = (
        csv_row.get("Payer_Coverage", "").strip()
        if csv_row.get("Payer_Coverage")
        else ""
    )
    total_cost_str = (
        csv_row.get("TotalCost", "").strip() if csv_row.get("TotalCost") else ""
    )

    # Parse numeric fields
    dispenses = None
    if dispenses_str:
        try:
            dispenses = int(dispenses_str)
        except (ValueError, TypeError):
            pass

    base_cost = None
    if base_cost_str:
        try:
            base_cost = float(base_cost_str)
        except (ValueError, TypeError):
            pass

    payer_coverage = None
    if payer_coverage_str:
        try:
            payer_coverage = float(payer_coverage_str)
        except (ValueError, TypeError):
            pass

    total_cost = None
    if total_cost_str:
        try:
            total_cost = float(total_cost_str)
        except (ValueError, TypeError):
            pass

    # Determine status based on STOP field
    status = "active" if (not stop or stop == "") else "completed"

    # Generate resource ID from Patient+Start+Code
    resource_id = f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "MedicationRequest",
        "id": resource_id,
        "status": status,
        "intent": "order",
    }

    # Set authoredOn from Start
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            resource["authoredOn"] = iso_start

    # Set occurrencePeriod
    occurrence_period: dict[str, Any] = {}
    if start:
        iso_start = format_datetime(start)
        if iso_start:
            occurrence_period["start"] = iso_start
    if stop:
        iso_stop = format_datetime(stop)
        if iso_stop:
            occurrence_period["end"] = iso_stop

    if occurrence_period:
        resource["occurrencePeriod"] = occurrence_period

    # Set subject (patient) reference (required)
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["subject"] = patient_ref

    # Set encounter reference (required)
    if encounter_id:
        encounter_ref = create_reference("Encounter", encounter_id)
        if encounter_ref:
            resource["encounter"] = encounter_ref

    # Set insurance (payer) reference
    if payer_id:
        payer_ref = create_reference("Coverage", payer_id)
        if payer_ref:
            resource["insurance"] = [payer_ref]

    # Set medicationCodeableConcept (RxNorm)
    if code or description:
        medication_code: dict[str, Any] = {}
        if code:
            coding = {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": code,
            }
            if description:
                coding["display"] = description
            medication_code["coding"] = [coding]
        if description:
            medication_code["text"] = description
        if medication_code:
            resource["medicationCodeableConcept"] = medication_code

    # Set dispenseRequest.numberOfRepeatsAllowed
    if dispenses is not None:
        resource["dispenseRequest"] = {"numberOfRepeatsAllowed": dispenses}

    # Set reasonCode
    if reason_code or reason_description:
        reason_code_obj: dict[str, Any] = {}
        if reason_code:
            coding = {"system": "http://snomed.info/sct", "code": reason_code}
            if reason_description:
                coding["display"] = reason_description
            reason_code_obj["coding"] = [coding]
        if reason_description and not reason_code:
            reason_code_obj["text"] = reason_description
        if reason_code_obj:
            resource["reasonCode"] = [reason_code_obj]

    # Set financial extensions
    extensions = []
    if base_cost is not None:
        extensions.append(
            {
                "url": "http://synthea.org/fhir/StructureDefinition/medication-baseCost",
                "valueDecimal": base_cost,
            }
        )
    if payer_coverage is not None:
        extensions.append(
            {
                "url": "http://synthea.org/fhir/StructureDefinition/medication-payerCoverage",
                "valueDecimal": payer_coverage,
            }
        )
    if total_cost is not None:
        extensions.append(
            {
                "url": "http://synthea.org/fhir/StructureDefinition/medication-totalCost",
                "valueDecimal": total_cost,
            }
        )

    if extensions:
        resource["extension"] = extensions

    return resource
