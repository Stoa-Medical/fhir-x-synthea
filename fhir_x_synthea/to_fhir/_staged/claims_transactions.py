"""Synthea ClaimTransaction → FHIR R4 Claim and ClaimResponse"""

from fhir.resources.claim import Claim
from fhir.resources.claimresponse import ClaimResponse
from synthea_pydantic import ClaimTransaction

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import format_datetime, ref


def _build_billable_period(from_date: str | None, to_date: str | None):
    """Build billablePeriod."""
    result = {}
    if from_date:
        iso_from = format_datetime(from_date)
        if iso_from:
            result["start"] = iso_from
    if to_date:
        iso_to = format_datetime(to_date)
        if iso_to:
            result["end"] = iso_to
    return result if result else None


def _build_care_team(supervising_provider_id: str | None):
    """Build careTeam."""
    if not supervising_provider_id:
        return None
    provider_ref = ref("Practitioner", supervising_provider_id)
    if not provider_ref:
        return None
    return [
        {
            "sequence": 1,
            "provider": provider_ref,
            "role": {"text": "supervising"},
        }
    ]


def _build_diagnosis_sequences(d: dict):
    """Build diagnosis sequence list."""
    sequences = []
    for i in range(1, 5):
        diag_ref = grab(d, f"diagnosisref{i}")
        if diag_ref is not None:
            try:
                sequences.append(int(diag_ref))
            except (ValueError, TypeError):
                pass
    return sequences if sequences else None


def _build_claim_item(d: dict) -> list:
    """Build claim item structure."""
    item: dict = {"sequence": 1}

    charge_id = grab(d, "chargeid")
    if charge_id is not None:
        try:
            item["sequence"] = int(charge_id)
        except (ValueError, TypeError):
            pass

    # Encounter reference
    appointment_id = grab(d, "appointmentid")
    if appointment_id:
        encounter_ref = ref("Encounter", appointment_id)
        if encounter_ref:
            item["encounter"] = [encounter_ref]

    # Product or service
    procedure_code = grab(d, "procedurecode")
    line_note = grab(d, "linenote")
    if procedure_code:
        coding = {"system": "http://snomed.info/sct", "code": str(procedure_code)}
        if line_note:
            coding["display"] = line_note
        item["productOrService"] = {"coding": [coding]}
    else:
        item["productOrService"] = {"text": "Service"}

    # Quantity
    units = grab(d, "units")
    if units is not None:
        item["quantity"] = {"value": float(units)}

    # Unit price
    unit_amount = grab(d, "unitamount")
    if unit_amount is not None:
        item["unitPrice"] = {"value": float(unit_amount), "currency": "USD"}

    # Net amount
    amount = grab(d, "amount")
    if amount is not None:
        item["net"] = {"value": float(amount), "currency": "USD"}

    # Diagnosis sequence
    diag_seq = _build_diagnosis_sequences(d)
    if diag_seq:
        item["diagnosisSequence"] = diag_seq

    # Notes on item
    item_notes = []
    department_id = grab(d, "departmentid")
    if department_id:
        item_notes.append({"text": f"Department ID: {department_id}"})
    fee_schedule_id = grab(d, "feescheduleid")
    if fee_schedule_id:
        item_notes.append({"text": f"Fee Schedule ID: {fee_schedule_id}"})
    if item_notes:
        item["note"] = item_notes

    # Transaction ID extension on item
    transaction_id = grab(d, "id")
    if transaction_id:
        item["extension"] = [
            {
                "url": "http://synthea.tools/StructureDefinition/transaction-id",
                "valueString": str(transaction_id),
            }
        ]

    return [item]


def _build_claim_notes(d: dict):
    """Build claim notes."""
    notes = []
    main_notes = grab(d, "notes")
    if main_notes:
        notes.append({"text": str(main_notes)})

    line_note = grab(d, "linenote")
    procedure_code = grab(d, "procedurecode")
    if line_note and not procedure_code:  # Only add if not already used as display
        notes.append({"text": str(line_note)})

    return notes if notes else None


@mapper
def _to_fhir_claim_transaction(d: dict):
    """Core mapping from dict to FHIR Claim structure (from transaction)."""
    claim_id = grab(d, "claimid")
    patient_insurance_id = grab(d, "patientinsuranceid")

    insurance = None
    if patient_insurance_id:
        insurance_ref = ref("Coverage", patient_insurance_id)
        if insurance_ref:
            insurance = [{"sequence": 1, "focal": True, "coverage": insurance_ref}]

    return {
        "resourceType": "Claim",
        "id": claim_id,
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
        "patient": ref("Patient", grab(d, "patientid")),
        "provider": ref("Practitioner", grab(d, "providerid")),
        "facility": ref("Organization", grab(d, "placeofservice")),
        "billablePeriod": _build_billable_period(
            grab(d, "fromdate"), grab(d, "todate")
        ),
        "insurance": insurance,
        "careTeam": _build_care_team(grab(d, "supervisingproviderid")),
        "item": _build_claim_item(d),
        "note": _build_claim_notes(d),
    }


def _build_adjudications(d: dict):
    """Build adjudication list based on transaction type."""
    transaction_type = grab(d, "type")
    if not transaction_type:
        return [
            {
                "category": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/adjudication",
                            "code": "submitted",
                        }
                    ]
                }
            }
        ]

    adjudications = []
    category_coding = {
        "system": "http://synthea.tools/CodeSystem/claims-transaction-type",
        "code": str(transaction_type),
    }

    # Payments
    payments = grab(d, "payments")
    if transaction_type == "PAYMENT" and payments is not None:
        adjudications.append(
            {
                "category": {"coding": [category_coding]},
                "amount": {"value": float(payments), "currency": "USD"},
            }
        )

    # Adjustments
    adjustments = grab(d, "adjustments")
    if transaction_type == "ADJUSTMENT" and adjustments is not None:
        adjudications.append(
            {
                "category": {"coding": [{**category_coding, "code": "adjustment"}]},
                "amount": {"value": float(adjustments), "currency": "USD"},
            }
        )

    # Transfers
    transfers = grab(d, "transfers")
    if transaction_type in ("TRANSFERIN", "TRANSFEROUT") and transfers is not None:
        transfer_adj = {
            "category": {"coding": [{**category_coding, "code": "transfer"}]},
            "amount": {"value": float(transfers), "currency": "USD"},
        }

        transfer_reasons = []
        transfer_out_id = grab(d, "transferoutid")
        if transfer_out_id:
            transfer_reasons.append(f"Transfer Out ID: {transfer_out_id}")
        transfer_type = grab(d, "transfertype")
        if transfer_type:
            transfer_reasons.append(f"Transfer Type: {transfer_type}")
        if transfer_reasons:
            transfer_adj["reason"] = {"text": "; ".join(transfer_reasons)}

        adjudications.append(transfer_adj)

    # CHARGE - no adjudication needed, just category
    if transaction_type == "CHARGE":
        adjudications.append({"category": {"coding": [category_coding]}})

    # Ensure at least one adjudication
    if not adjudications:
        adjudications.append(
            {
                "category": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/adjudication",
                            "code": "submitted",
                        }
                    ]
                }
            }
        )

    return adjudications


def _build_response_item(d: dict):
    """Build ClaimResponse item structure."""
    charge_id = grab(d, "chargeid")
    if charge_id is None:
        return None

    item = {
        "itemSequence": int(charge_id),
        "adjudication": _build_adjudications(d),
    }

    outstanding = grab(d, "outstanding")
    if outstanding is not None:
        item["note"] = [{"text": f"Outstanding: {outstanding}"}]

    return [item]


def _build_payment(d: dict) -> dict | None:
    """Build payment structure."""
    transaction_type = grab(d, "type")
    payments = grab(d, "payments")

    if transaction_type != "PAYMENT" or payments is None:
        return None

    payment: dict = {"amount": {"value": float(payments), "currency": "USD"}}

    method = grab(d, "method")
    if method:
        payment["type"] = {
            "coding": [
                {
                    "system": "http://synthea.tools/CodeSystem/payment-method",
                    "code": str(method),
                }
            ]
        }

    to_date = grab(d, "todate")
    if to_date:
        iso_date = format_datetime(to_date)
        if iso_date:
            payment["date"] = iso_date

    return payment


@mapper
def _to_fhir_claim_response(d: dict):
    """Core mapping from dict to FHIR ClaimResponse structure."""
    transaction_id = grab(d, "id")
    patient_insurance_id = grab(d, "patientinsuranceid")

    insurance = None
    if patient_insurance_id:
        insurance_ref = ref("Coverage", patient_insurance_id)
        if insurance_ref:
            insurance = [{"sequence": 1, "focal": True, "coverage": insurance_ref}]

    return {
        "resourceType": "ClaimResponse",
        "id": transaction_id,
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
        "request": ref("Claim", grab(d, "claimid")),
        "patient": ref("Patient", grab(d, "patientid")),
        "insurer": {"display": "Unknown Insurer"},
        "insurance": insurance,
        "item": _build_response_item(d),
        "payment": _build_payment(d),
    }


def convert(src: ClaimTransaction) -> Claim:
    """Convert Synthea ClaimTransaction to FHIR R4 Claim.

    Args:
        src: Synthea ClaimTransaction model

    Returns:
        FHIR R4 Claim resource (skeleton based on transaction data)
    """
    return Claim(**_to_fhir_claim_transaction(to_dict(src)))


def convert_response(src: ClaimTransaction) -> ClaimResponse:
    """Convert Synthea ClaimTransaction to FHIR R4 ClaimResponse.

    Args:
        src: Synthea ClaimTransaction model

    Returns:
        FHIR R4 ClaimResponse resource
    """
    return ClaimResponse(**_to_fhir_claim_response(to_dict(src)))
