"""
Mapping functions for converting Synthea claims_transactions.csv rows to FHIR Claim and ClaimResponse resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime


def map_claim_from_transaction(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea claims_transactions.csv row to a FHIR R4 Claim resource (skeleton).

    Args:
        csv_row: Dictionary with keys from claims_transactions.csv

    Returns:
        Dictionary representing a FHIR Claim resource
    """

    # Extract and process fields
    claim_id = csv_row.get("Claim ID", "").strip() if csv_row.get("Claim ID") else ""
    transaction_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    patient_id = (
        csv_row.get("Patient ID", "").strip() if csv_row.get("Patient ID") else ""
    )
    place_of_service_id = (
        csv_row.get("Place of Service", "").strip()
        if csv_row.get("Place of Service")
        else ""
    )
    provider_id = (
        csv_row.get("Provider ID", "").strip() if csv_row.get("Provider ID") else ""
    )
    from_date = csv_row.get("From Date", "").strip() if csv_row.get("From Date") else ""
    to_date = csv_row.get("To Date", "").strip() if csv_row.get("To Date") else ""
    appointment_id = (
        csv_row.get("Appointment ID", "").strip()
        if csv_row.get("Appointment ID")
        else ""
    )
    procedure_code = (
        csv_row.get("Procedure Code", "").strip()
        if csv_row.get("Procedure Code")
        else ""
    )
    notes = csv_row.get("Notes", "").strip() if csv_row.get("Notes") else ""
    line_note = csv_row.get("Line Note", "").strip() if csv_row.get("Line Note") else ""
    supervising_provider_id = (
        csv_row.get("Supervising Provider ID", "").strip()
        if csv_row.get("Supervising Provider ID")
        else ""
    )
    patient_insurance_id = (
        csv_row.get("Patient Insurance ID", "").strip()
        if csv_row.get("Patient Insurance ID")
        else ""
    )
    department_id = (
        csv_row.get("Department ID", "").strip() if csv_row.get("Department ID") else ""
    )
    fee_schedule_id = (
        csv_row.get("Fee Schedule ID", "").strip()
        if csv_row.get("Fee Schedule ID")
        else ""
    )

    # Parse numeric fields
    charge_id_str = (
        csv_row.get("Charge ID", "").strip() if csv_row.get("Charge ID") else ""
    )
    units_str = csv_row.get("Units", "").strip() if csv_row.get("Units") else ""
    unit_amount_str = (
        csv_row.get("Unit Amount", "").strip() if csv_row.get("Unit Amount") else ""
    )
    amount_str = csv_row.get("Amount", "").strip() if csv_row.get("Amount") else ""

    charge_id = None
    if charge_id_str:
        try:
            charge_id = int(charge_id_str)
        except (ValueError, TypeError):
            pass

    units = None
    if units_str:
        try:
            units = float(units_str)
        except (ValueError, TypeError):
            pass

    unit_amount = None
    if unit_amount_str:
        try:
            unit_amount = float(unit_amount_str)
        except (ValueError, TypeError):
            pass

    amount = None
    if amount_str:
        try:
            amount = float(amount_str)
        except (ValueError, TypeError):
            pass

    # Extract diagnosis references (DiagnosisRef1-4)
    diagnosis_sequences = []
    for i in range(1, 5):
        diag_ref_key = f"DiagnosisRef{i}"
        diag_ref = (
            csv_row.get(diag_ref_key, "").strip() if csv_row.get(diag_ref_key) else ""
        )
        if diag_ref:
            try:
                diagnosis_sequences.append(int(diag_ref))
            except (ValueError, TypeError):
                pass

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Claim",
        "id": claim_id if claim_id else "",
    }

    # Set patient reference
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["patient"] = patient_ref

    # Set provider reference
    if provider_id:
        provider_ref = create_reference("Practitioner", provider_id)
        if provider_ref:
            resource["provider"] = provider_ref

    # Set facility
    if place_of_service_id:
        facility_ref = create_reference("Organization", place_of_service_id)
        if facility_ref:
            resource["facility"] = facility_ref

    # Set billablePeriod
    billable_period: dict[str, Any] = {}
    if from_date:
        iso_from = format_datetime(from_date)
        if iso_from:
            billable_period["start"] = iso_from
    if to_date:
        iso_to = format_datetime(to_date)
        if iso_to:
            billable_period["end"] = iso_to
    if billable_period:
        resource["billablePeriod"] = billable_period

    # Set insurance
    if patient_insurance_id:
        insurance_ref = create_reference("Coverage", patient_insurance_id)
        if insurance_ref:
            resource["insurance"] = [{"coverage": insurance_ref}]

    # Set careTeam (supervising provider)
    if supervising_provider_id:
        provider_ref = create_reference("Practitioner", supervising_provider_id)
        if provider_ref:
            resource["careTeam"] = [
                {"provider": provider_ref, "role": {"text": "supervising"}}
            ]

    # Set item
    item: dict[str, Any] = {}

    if charge_id is not None:
        item["sequence"] = charge_id

    # Encounter reference
    if appointment_id:
        encounter_ref = create_reference("Encounter", appointment_id)
        if encounter_ref:
            item["encounter"] = [encounter_ref]

    # Product or service
    if procedure_code:
        item["productOrService"] = {
            "coding": [{"system": "http://snomed.info/sct", "code": procedure_code}]
        }
        if line_note:
            item["productOrService"]["coding"][0]["display"] = line_note

    # Quantity
    if units is not None:
        item["quantity"] = {"value": units}

    # Unit price
    if unit_amount is not None:
        item["unitPrice"] = {"value": unit_amount}

    # Net amount
    if amount is not None:
        item["net"] = {"value": amount}

    # Diagnosis sequence
    if diagnosis_sequences:
        item["diagnosisSequence"] = diagnosis_sequences

    # Notes on item
    item_notes = []
    if department_id:
        item_notes.append({"text": f"Department ID: {department_id}"})
    if fee_schedule_id:
        item_notes.append({"text": f"Fee Schedule ID: {fee_schedule_id}"})
    if item_notes:
        item["note"] = item_notes

    # Transaction ID extension on item
    if transaction_id:
        item.setdefault("extension", []).append(
            {
                "url": "http://synthea.tools/StructureDefinition/transaction-id",
                "valueString": transaction_id,
            }
        )

    if item:
        resource["item"] = [item]

    # Set notes
    claim_notes = []
    if notes:
        claim_notes.append({"text": notes})
    if line_note and not procedure_code:  # Only add if not already used as display
        claim_notes.append({"text": line_note})
    if claim_notes:
        resource["note"] = claim_notes

    return resource


def map_claim_response(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea claims_transactions.csv row to a FHIR R4 ClaimResponse resource.

    Args:
        csv_row: Dictionary with keys from claims_transactions.csv

    Returns:
        Dictionary representing a FHIR ClaimResponse resource
    """

    # Extract and process fields
    transaction_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    claim_id = csv_row.get("Claim ID", "").strip() if csv_row.get("Claim ID") else ""
    patient_id = (
        csv_row.get("Patient ID", "").strip() if csv_row.get("Patient ID") else ""
    )
    patient_insurance_id = (
        csv_row.get("Patient Insurance ID", "").strip()
        if csv_row.get("Patient Insurance ID")
        else ""
    )
    transaction_type = csv_row.get("Type", "").strip() if csv_row.get("Type") else ""
    method = csv_row.get("Method", "").strip() if csv_row.get("Method") else ""
    to_date = csv_row.get("To Date", "").strip() if csv_row.get("To Date") else ""
    transfer_out_id = (
        csv_row.get("Transfer Out ID", "").strip()
        if csv_row.get("Transfer Out ID")
        else ""
    )
    transfer_type = (
        csv_row.get("Transfer Type", "").strip() if csv_row.get("Transfer Type") else ""
    )

    # Parse numeric fields
    charge_id_str = (
        csv_row.get("Charge ID", "").strip() if csv_row.get("Charge ID") else ""
    )
    payments_str = (
        csv_row.get("Payments", "").strip() if csv_row.get("Payments") else ""
    )
    adjustments_str = (
        csv_row.get("Adjustments", "").strip() if csv_row.get("Adjustments") else ""
    )
    transfers_str = (
        csv_row.get("Transfers", "").strip() if csv_row.get("Transfers") else ""
    )
    outstanding_str = (
        csv_row.get("Outstanding", "").strip() if csv_row.get("Outstanding") else ""
    )

    charge_id = None
    if charge_id_str:
        try:
            charge_id = int(charge_id_str)
        except (ValueError, TypeError):
            pass

    payments = None
    if payments_str:
        try:
            payments = float(payments_str)
        except (ValueError, TypeError):
            pass

    adjustments = None
    if adjustments_str:
        try:
            adjustments = float(adjustments_str)
        except (ValueError, TypeError):
            pass

    transfers = None
    if transfers_str:
        try:
            transfers = float(transfers_str)
        except (ValueError, TypeError):
            pass

    outstanding = None
    if outstanding_str:
        try:
            outstanding = float(outstanding_str)
        except (ValueError, TypeError):
            pass

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "ClaimResponse",
        "id": transaction_id if transaction_id else "",
    }

    # Set request reference
    if claim_id:
        claim_ref = create_reference("Claim", claim_id)
        if claim_ref:
            resource["request"] = claim_ref

    # Set patient reference
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["patient"] = patient_ref

    # Set insurance
    if patient_insurance_id:
        insurance_ref = create_reference("Coverage", patient_insurance_id)
        if insurance_ref:
            resource["insurance"] = [{"coverage": insurance_ref}]

    # Set item with adjudication
    if charge_id is not None:
        item: dict[str, Any] = {"itemSequence": charge_id, "adjudication": []}

        # Build adjudications based on transaction type
        if transaction_type:
            # Category coding for transaction type
            category_coding = {
                "system": "http://synthea.tools/CodeSystem/claims-transaction-type",
                "code": transaction_type,
            }

            # Payments
            if transaction_type == "PAYMENT" and payments is not None:
                item["adjudication"].append(
                    {
                        "category": {"coding": [category_coding]},
                        "amount": {"value": payments},
                    }
                )

            # Adjustments
            if transaction_type == "ADJUSTMENT" and adjustments is not None:
                item["adjudication"].append(
                    {
                        "category": {
                            "coding": [{**category_coding, "code": "adjustment"}]
                        },
                        "amount": {"value": adjustments},
                    }
                )

            # Transfers
            if (
                transaction_type in ("TRANSFERIN", "TRANSFEROUT")
                and transfers is not None
            ):
                transfer_adjudication: dict[str, Any] = {
                    "category": {"coding": [{**category_coding, "code": "transfer"}]},
                    "amount": {"value": transfers},
                }

                # Add transfer details as reason
                transfer_reasons = []
                if transfer_out_id:
                    transfer_reasons.append(f"Transfer Out ID: {transfer_out_id}")
                if transfer_type:
                    transfer_reasons.append(f"Transfer Type: {transfer_type}")

                if transfer_reasons:
                    transfer_adjudication["reason"] = {
                        "text": "; ".join(transfer_reasons)
                    }

                item["adjudication"].append(transfer_adjudication)

            # CHARGE - no adjudication needed, just category
            if transaction_type == "CHARGE":
                item["adjudication"].append({"category": {"coding": [category_coding]}})

        # Outstanding note
        if outstanding is not None:
            item["note"] = [{"text": f"Outstanding: {outstanding}"}]

        if item.get("adjudication") or item.get("note"):
            resource["item"] = [item]

    # Set payment
    if payments is not None and transaction_type == "PAYMENT":
        payment: dict[str, Any] = {"amount": {"value": payments}}

        if method:
            payment["type"] = {
                "coding": [
                    {
                        "system": "http://synthea.tools/CodeSystem/payment-method",
                        "code": method,
                    }
                ]
            }

        if to_date:
            iso_date = format_datetime(to_date)
            if iso_date:
                payment["date"] = iso_date

        resource["payment"] = payment

    return resource
