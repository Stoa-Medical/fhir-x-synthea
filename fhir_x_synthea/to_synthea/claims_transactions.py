"""FHIR R4 Claim/ClaimResponse → Synthea ClaimTransaction"""

import logging
from decimal import Decimal

from fhir.resources.claim import Claim
from fhir.resources.claimresponse import ClaimResponse
from synthea_pydantic import ClaimTransaction

from ..chidian_ext import extract_ref_id, grab, parse_date, to_dict
from ..synthea_lib import to_decimal

logger = logging.getLogger(__name__)


def _extract_supervising_provider(d: dict) -> str:
    """Extract supervising provider from careTeam."""
    care_team = grab(d, "careTeam") or []
    for team_member in care_team:
        role = team_member.get("role", {})
        if role.get("text") == "supervising":
            provider = team_member.get("provider")
            if provider:
                return extract_ref_id({"p": provider}, "p")
    return ""


def convert(src: Claim) -> list[ClaimTransaction]:
    """Convert FHIR R4 Claim to Synthea ClaimTransaction(s).

    Produces one CHARGE row per Claim.item.

    Args:
        src: FHIR R4 Claim resource

    Returns:
        List of Synthea ClaimTransaction models
    """
    d = to_dict(src)
    transactions = []

    claim_id = grab(d, "id") or ""
    patient_id = extract_ref_id(d, "patient")
    place_of_service = extract_ref_id(d, "facility")
    provider_id = extract_ref_id(d, "provider")

    # Extract billable period
    billable_period = grab(d, "billablePeriod") or {}
    from_date = (
        parse_date({"dt": billable_period.get("start")}, "dt")
        if billable_period.get("start")
        else None
    )
    to_date = (
        parse_date({"dt": billable_period.get("end")}, "dt")
        if billable_period.get("end")
        else None
    )

    # Extract insurance
    insurance_list = grab(d, "insurance") or []
    patient_insurance_id = ""
    if insurance_list:
        coverage = insurance_list[0].get("coverage")
        if coverage:
            patient_insurance_id = extract_ref_id({"c": coverage}, "c")

    supervising_provider_id = _extract_supervising_provider(d)

    # Extract notes
    notes_list = grab(d, "note") or []
    notes_text = "; ".join(
        [note.get("text", "") for note in notes_list if note.get("text")]
    )

    # Process each item
    items = grab(d, "item") or []
    for item in items:
        charge_id = item.get("sequence")
        if charge_id is None:
            continue

        transaction_id = f"txn-{claim_id}-{charge_id}"

        # Extract item-specific fields
        net = item.get("net", {})
        amount = to_decimal(net.get("value")) if net.get("value") is not None else None

        product_or_service = item.get("productOrService", {})
        codings = product_or_service.get("coding", [])
        procedure_code = codings[0].get("code", "") if codings else ""
        line_note = codings[0].get("display", "") if codings else ""

        modifiers = item.get("modifier", [])
        modifier1 = modifiers[0].get("code", "") if len(modifiers) > 0 else ""
        modifier2 = modifiers[1].get("code", "") if len(modifiers) > 1 else ""

        diagnosis_sequences = item.get("diagnosisSequence", [])
        diagnosisref1 = (
            str(diagnosis_sequences[0]) if len(diagnosis_sequences) > 0 else None
        )
        diagnosisref2 = (
            str(diagnosis_sequences[1]) if len(diagnosis_sequences) > 1 else None
        )
        diagnosisref3 = (
            str(diagnosis_sequences[2]) if len(diagnosis_sequences) > 2 else None
        )
        diagnosisref4 = (
            str(diagnosis_sequences[3]) if len(diagnosis_sequences) > 3 else None
        )

        quantity = item.get("quantity", {})
        units = (
            to_decimal(quantity.get("value"))
            if quantity.get("value") is not None
            else None
        )

        unit_price = item.get("unitPrice", {})
        unit_amount = (
            to_decimal(unit_price.get("value"))
            if unit_price.get("value") is not None
            else None
        )

        encounters = item.get("encounter", [])
        appointment_id = extract_ref_id({"e": encounters[0]}, "e") if encounters else ""

        # Extract notes
        item_notes = item.get("note", [])
        department_id = ""
        fee_schedule_id = ""
        for note in item_notes:
            note_text = note.get("text", "")
            if "Department ID:" in note_text:
                department_id = note_text.replace("Department ID:", "").strip()
            elif "Fee Schedule ID:" in note_text:
                fee_schedule_id = note_text.replace("Fee Schedule ID:", "").strip()

        tx = ClaimTransaction(
            id=transaction_id or None,
            claimid=claim_id or None,
            chargeid=int(charge_id) if charge_id is not None else None,
            patientid=patient_id or None,
            type="CHARGE",
            amount=amount,
            method=None,
            fromdate=from_date,
            todate=to_date,
            placeofservice=place_of_service or None,
            procedurecode=procedure_code or None,
            modifier1=modifier1 or None,
            modifier2=modifier2 or None,
            diagnosisref1=diagnosisref1,
            diagnosisref2=diagnosisref2,
            diagnosisref3=diagnosisref3,
            diagnosisref4=diagnosisref4,
            units=units,
            departmentid=department_id or None,
            notes=notes_text or None,
            unitamount=unit_amount,
            transferoutid=None,
            transfertype=None,
            payments=None,
            adjustments=None,
            transfers=None,
            outstanding=None,
            appointmentid=appointment_id or None,
            linenote=line_note or None,
            patientinsuranceid=patient_insurance_id or None,
            feescheduleid=fee_schedule_id or None,
            providerid=provider_id or None,
            supervisingproviderid=supervising_provider_id or None,
        )
        transactions.append(tx)

    return transactions


def convert_response(src: ClaimResponse) -> list[ClaimTransaction]:
    """Convert FHIR R4 ClaimResponse to Synthea ClaimTransaction(s).

    Args:
        src: FHIR R4 ClaimResponse resource

    Returns:
        List of Synthea ClaimTransaction models
    """
    d = to_dict(src)
    transactions = []

    transaction_id = grab(d, "id") or ""
    claim_id = extract_ref_id(d, "request")
    patient_id = extract_ref_id(d, "patient")

    # Extract payment
    payment = grab(d, "payment") or {}
    payment_amount = payment.get("amount", {}).get("value")
    payment_type = payment.get("type", {})
    codings = payment_type.get("coding", [])
    payment_method = (
        codings[0].get("code", "") if codings else payment_type.get("text", "")
    )
    payment_date = (
        parse_date({"dt": payment.get("date")}, "dt") if payment.get("date") else None
    )

    # Process items
    items = grab(d, "item") or []
    for item in items:
        charge_id = item.get("itemSequence")

        # Determine transaction type from adjudications
        transaction_type = ""
        amount_value = None
        transfers_value = None
        transfer_out_id = ""
        transfer_type = ""

        for adj in item.get("adjudication", []):
            category = adj.get("category", {})
            for coding in category.get("coding", []):
                code = coding.get("code", "")
                if code in ("PAYMENT", "payment"):
                    transaction_type = "PAYMENT"
                    if adj.get("amount"):
                        amount_value = to_decimal(adj["amount"].get("value", 0))
                    break
                elif code in ("ADJUSTMENT", "adjustment"):
                    transaction_type = "ADJUSTMENT"
                    if adj.get("amount"):
                        amount_value = to_decimal(adj["amount"].get("value", 0))
                    break
                elif code in ("TRANSFERIN", "TRANSFEROUT", "transfer"):
                    transaction_type = (
                        "TRANSFERIN" if "IN" in code.upper() else "TRANSFEROUT"
                    )
                    if adj.get("amount"):
                        transfers_value = to_decimal(adj["amount"].get("value", 0))

                    reason = adj.get("reason", {})
                    reason_text = reason.get("text", "")
                    if reason_text:
                        for part in reason_text.split(";"):
                            if "Transfer Out ID:" in part:
                                transfer_out_id = part.replace(
                                    "Transfer Out ID:", ""
                                ).strip()
                            elif "Transfer Type:" in part:
                                transfer_type = part.replace(
                                    "Transfer Type:", ""
                                ).strip()
                    break

        if payment_amount is not None and not transaction_type:
            transaction_type = "PAYMENT"
            amount_value = to_decimal(payment_amount)

        # Extract outstanding from notes
        outstanding = None
        for note in item.get("note", []):
            note_text = note.get("text", "")
            if "Outstanding:" in note_text:
                try:
                    outstanding = Decimal(note_text.replace("Outstanding:", "").strip())
                except (ValueError, TypeError, ArithmeticError):
                    pass

        tx = ClaimTransaction(
            id=transaction_id or None,
            claimid=claim_id or None,
            chargeid=int(charge_id) if charge_id is not None else None,
            patientid=patient_id or None,
            type=transaction_type or None,
            amount=amount_value,
            method=payment_method or None,
            fromdate=payment_date,
            todate=payment_date,
            placeofservice=None,
            procedurecode=None,
            modifier1=None,
            modifier2=None,
            diagnosisref1=None,
            diagnosisref2=None,
            diagnosisref3=None,
            diagnosisref4=None,
            units=None,
            departmentid=None,
            notes=None,
            unitamount=None,
            transferoutid=transfer_out_id or None,
            transfertype=transfer_type or None,
            payments=to_decimal(payment_amount)
            if transaction_type == "PAYMENT" and payment_amount is not None
            else None,
            adjustments=amount_value if transaction_type == "ADJUSTMENT" else None,
            transfers=transfers_value
            if transaction_type in ("TRANSFERIN", "TRANSFEROUT")
            else None,
            outstanding=outstanding,
            appointmentid=None,
            linenote=None,
            patientinsuranceid=None,
            feescheduleid=None,
            providerid=None,
            supervisingproviderid=None,
        )
        transactions.append(tx)

    # If no items, create one transaction from payment info
    if not transactions and payment_amount is not None:
        tx = ClaimTransaction(
            id=transaction_id or None,
            claimid=claim_id or None,
            chargeid=None,
            patientid=patient_id or None,
            type="PAYMENT",
            amount=None,
            method=payment_method or None,
            fromdate=payment_date,
            todate=payment_date,
            placeofservice=None,
            procedurecode=None,
            modifier1=None,
            modifier2=None,
            diagnosisref1=None,
            diagnosisref2=None,
            diagnosisref3=None,
            diagnosisref4=None,
            units=None,
            departmentid=None,
            notes=None,
            unitamount=None,
            transferoutid=None,
            transfertype=None,
            payments=to_decimal(payment_amount),
            adjustments=None,
            transfers=None,
            outstanding=None,
            appointmentid=None,
            linenote=None,
            patientinsuranceid=None,
            feescheduleid=None,
            providerid=None,
            supervisingproviderid=None,
        )
        transactions.append(tx)

    return transactions
