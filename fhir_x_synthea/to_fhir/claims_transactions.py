"""Synthea ClaimTransaction → FHIR R4 Claim and ClaimResponse"""

from typing import Any

from fhir.resources.claim import Claim
from fhir.resources.claimresponse import ClaimResponse
from synthea_pydantic import ClaimTransaction

from ..fhir_lib import create_reference, format_datetime
from ..utils import to_str


def convert(src: ClaimTransaction) -> Claim:
    """Convert Synthea ClaimTransaction to FHIR R4 Claim.

    Args:
        src: Synthea ClaimTransaction model

    Returns:
        FHIR R4 Claim resource (skeleton based on transaction data)
    """
    d = src.model_dump()

    # Extract and process fields (synthea_pydantic uses lowercase keys)
    claim_id = to_str(d.get("claimid"))
    transaction_id = to_str(d.get("id"))
    patient_id = to_str(d.get("patientid"))
    place_of_service_id = to_str(d.get("placeofservice"))
    provider_id = to_str(d.get("providerid"))
    from_date = to_str(d.get("fromdate"))
    to_date = to_str(d.get("todate"))
    appointment_id = to_str(d.get("appointmentid"))
    procedure_code = to_str(d.get("procedurecode"))
    notes = to_str(d.get("notes"))
    line_note = to_str(d.get("linenote"))
    supervising_provider_id = to_str(d.get("supervisingproviderid"))
    patient_insurance_id = to_str(d.get("patientinsuranceid"))
    department_id = to_str(d.get("departmentid"))
    fee_schedule_id = to_str(d.get("feescheduleid"))

    # Parse numeric fields
    charge_id = d.get("chargeid")
    units = d.get("units")
    unit_amount = d.get("unitamount")
    amount = d.get("amount")

    # Extract diagnosis references (diagnosisref1-4)
    diagnosis_sequences = []
    for i in range(1, 5):
        diag_ref = d.get(f"diagnosisref{i}")
        if diag_ref is not None:
            try:
                diagnosis_sequences.append(int(diag_ref))
            except (ValueError, TypeError):
                pass

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Claim",
        "status": "active",
        "use": "claim",
        "type": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                    "code": "professional",
                }
            ]
        },
        "priority": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/processpriority",
                    "code": "normal",
                }
            ]
        },
    }

    if claim_id:
        resource["id"] = claim_id

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
            resource["insurance"] = [
                {"sequence": 1, "focal": True, "coverage": insurance_ref}
            ]

    # Set careTeam (supervising provider)
    if supervising_provider_id:
        provider_ref = create_reference("Practitioner", supervising_provider_id)
        if provider_ref:
            resource["careTeam"] = [
                {
                    "sequence": 1,
                    "provider": provider_ref,
                    "role": {"text": "supervising"},
                }
            ]

    # Set item
    item: dict[str, Any] = {"sequence": 1}

    if charge_id is not None:
        item["sequence"] = int(charge_id)

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
    else:
        item["productOrService"] = {"text": "Service"}

    # Quantity
    if units is not None:
        item["quantity"] = {"value": float(units)}

    # Unit price
    if unit_amount is not None:
        item["unitPrice"] = {"value": float(unit_amount), "currency": "USD"}

    # Net amount
    if amount is not None:
        item["net"] = {"value": float(amount), "currency": "USD"}

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

    resource["item"] = [item]

    # Set notes
    claim_notes = []
    if notes:
        claim_notes.append({"text": notes})
    if line_note and not procedure_code:  # Only add if not already used as display
        claim_notes.append({"text": line_note})
    if claim_notes:
        resource["note"] = claim_notes

    return Claim(**resource)


def convert_response(src: ClaimTransaction) -> ClaimResponse:
    """Convert Synthea ClaimTransaction to FHIR R4 ClaimResponse.

    Args:
        src: Synthea ClaimTransaction model

    Returns:
        FHIR R4 ClaimResponse resource
    """
    d = src.model_dump()

    # Extract and process fields
    transaction_id = to_str(d.get("id"))
    claim_id = to_str(d.get("claimid"))
    patient_id = to_str(d.get("patientid"))
    patient_insurance_id = to_str(d.get("patientinsuranceid"))
    transaction_type = to_str(d.get("type"))
    method = to_str(d.get("method"))
    to_date = to_str(d.get("todate"))
    transfer_out_id = to_str(d.get("transferoutid"))
    transfer_type = to_str(d.get("transfertype"))

    # Parse numeric fields
    charge_id = d.get("chargeid")
    payments = d.get("payments")
    adjustments = d.get("adjustments")
    transfers = d.get("transfers")
    outstanding = d.get("outstanding")

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "ClaimResponse",
        "status": "active",
        "use": "claim",
        "type": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                    "code": "professional",
                }
            ]
        },
        "outcome": "complete",
    }

    if transaction_id:
        resource["id"] = transaction_id

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

    # Set insurer (required in R4B)
    resource["insurer"] = {"display": "Unknown Insurer"}

    # Set insurance
    if patient_insurance_id:
        insurance_ref = create_reference("Coverage", patient_insurance_id)
        if insurance_ref:
            resource["insurance"] = [
                {"sequence": 1, "focal": True, "coverage": insurance_ref}
            ]

    # Set item with adjudication
    if charge_id is not None:
        item: dict[str, Any] = {"itemSequence": int(charge_id), "adjudication": []}

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
                        "amount": {"value": float(payments), "currency": "USD"},
                    }
                )

            # Adjustments
            if transaction_type == "ADJUSTMENT" and adjustments is not None:
                item["adjudication"].append(
                    {
                        "category": {
                            "coding": [{**category_coding, "code": "adjustment"}]
                        },
                        "amount": {"value": float(adjustments), "currency": "USD"},
                    }
                )

            # Transfers
            if (
                transaction_type in ("TRANSFERIN", "TRANSFEROUT")
                and transfers is not None
            ):
                transfer_adjudication: dict[str, Any] = {
                    "category": {"coding": [{**category_coding, "code": "transfer"}]},
                    "amount": {"value": float(transfers), "currency": "USD"},
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

        # Ensure at least one adjudication for valid structure
        if not item["adjudication"]:
            item["adjudication"].append(
                {
                    "category": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/adjudication",
                                "code": "submitted",
                            }
                        ]
                    },
                }
            )

        resource["item"] = [item]

    # Set payment
    if payments is not None and transaction_type == "PAYMENT":
        payment: dict[str, Any] = {
            "amount": {"value": float(payments), "currency": "USD"}
        }

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

    return ClaimResponse(**resource)
