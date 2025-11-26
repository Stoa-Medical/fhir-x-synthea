"""
Mapping functions for converting FHIR Claim and ClaimResponse resources to Synthea claims_transactions.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import extract_reference_id, parse_datetime_to_date


def map_fhir_claim_to_transactions(
    fhir_resource: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Map a FHIR R4 Claim resource to Synthea claims_transactions.csv rows.
    Produces one CHARGE row per Claim.item.

    Args:
        fhir_resource: Dictionary representing a FHIR Claim resource

    Returns:
        List of dictionaries, each representing a CSV row
    """

    rows = []
    claim_id = fhir_resource.get("id", "")

    # Extract common fields
    patient = fhir_resource.get("patient")
    patient_id = extract_reference_id(patient) if patient else ""

    facility = fhir_resource.get("facility")
    place_of_service = extract_reference_id(facility) if facility else ""

    provider = fhir_resource.get("provider")
    provider_id = extract_reference_id(provider) if provider else ""

    billable_period = fhir_resource.get("billablePeriod", {})
    from_date = parse_datetime_to_date(billable_period.get("start"))
    to_date = parse_datetime_to_date(billable_period.get("end"))

    insurance_list = fhir_resource.get("insurance", [])
    patient_insurance_id = ""
    if insurance_list:
        first_insurance = insurance_list[0]
        coverage = first_insurance.get("coverage")
        if coverage:
            patient_insurance_id = extract_reference_id(coverage)

    care_team = fhir_resource.get("careTeam", [])
    supervising_provider_id = ""
    for team_member in care_team:
        role = team_member.get("role", {})
        if role.get("text") == "supervising":
            provider_ref = team_member.get("provider")
            if provider_ref:
                supervising_provider_id = extract_reference_id(provider_ref)
                break

    notes_list = fhir_resource.get("note", [])
    notes_text = "; ".join(
        [note.get("text", "") for note in notes_list if note.get("text")]
    )

    # Process each item
    items = fhir_resource.get("item", [])
    for item in items:
        charge_id = item.get("sequence")
        if charge_id is None:
            continue

        # Generate transaction ID
        transaction_id = f"txn-{claim_id}-{charge_id}"

        row: dict[str, str] = {
            "Id": transaction_id,
            "Claim ID": claim_id,
            "Charge ID": str(charge_id),
            "Patient ID": patient_id,
            "Type": "CHARGE",
            "Amount": "",
            "From Date": from_date,
            "To Date": to_date,
            "Place of Service": place_of_service,
            "Procedure Code": "",
            "Modifier1": "",
            "Modifier2": "",
            "DiagnosisRef1": "",
            "DiagnosisRef2": "",
            "DiagnosisRef3": "",
            "DiagnosisRef4": "",
            "Units": "",
            "Unit Amount": "",
            "Notes": notes_text,
            "Line Note": "",
            "Department ID": "",
            "Fee Schedule ID": "",
            "Appointment ID": "",
            "Provider ID": provider_id,
            "Supervising Provider ID": supervising_provider_id,
            "Patient Insurance ID": patient_insurance_id,
            "Method": "",
            "Payments": "",
            "Adjustments": "",
            "Transfers": "",
            "Transfer Out ID": "",
            "Transfer Type": "",
            "Outstanding": "",
        }

        # Extract item-specific fields
        net = item.get("net", {})
        if net.get("value") is not None:
            row["Amount"] = str(net.get("value", ""))

        product_or_service = item.get("productOrService", {})
        codings = product_or_service.get("coding", [])
        if codings:
            row["Procedure Code"] = codings[0].get("code", "")

        modifiers = item.get("modifier", [])
        if len(modifiers) > 0:
            row["Modifier1"] = modifiers[0].get("code", "")
        if len(modifiers) > 1:
            row["Modifier2"] = modifiers[1].get("code", "")

        diagnosis_sequences = item.get("diagnosisSequence", [])
        for i, seq in enumerate(diagnosis_sequences[:4]):
            row[f"DiagnosisRef{i+1}"] = str(seq)

        quantity = item.get("quantity", {})
        if quantity.get("value") is not None:
            row["Units"] = str(quantity.get("value", ""))

        unit_price = item.get("unitPrice", {})
        if unit_price.get("value") is not None:
            row["Unit Amount"] = str(unit_price.get("value", ""))

        encounters = item.get("encounter", [])
        if encounters:
            row["Appointment ID"] = extract_reference_id(encounters[0])

        item_notes = item.get("note", [])
        if item_notes:
            row["Line Note"] = item_notes[0].get("text", "")

        # Extract Department ID and Fee Schedule ID from item notes
        for note in item_notes:
            note_text = note.get("text", "")
            if "Department ID:" in note_text:
                row["Department ID"] = note_text.replace("Department ID:", "").strip()
            elif "Fee Schedule ID:" in note_text:
                row["Fee Schedule ID"] = note_text.replace(
                    "Fee Schedule ID:", ""
                ).strip()

        rows.append(row)

    return rows


def map_fhir_claim_response_to_transactions(
    fhir_resource: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Map a FHIR R4 ClaimResponse resource to Synthea claims_transactions.csv rows.

    Args:
        fhir_resource: Dictionary representing a FHIR ClaimResponse resource

    Returns:
        List of dictionaries, each representing a CSV row
    """

    rows = []
    transaction_id = fhir_resource.get("id", "")

    # Extract request reference (Claim ID)
    request = fhir_resource.get("request")
    claim_id = extract_reference_id(request) if request else ""

    # Extract patient
    patient = fhir_resource.get("patient")
    patient_id = extract_reference_id(patient) if patient else ""

    # Extract payment
    payment = fhir_resource.get("payment", {})
    payment_amount = payment.get("amount", {}).get("value")
    payment_method_obj = payment.get("type", {})
    payment_method = ""
    codings = payment_method_obj.get("coding", [])
    if codings:
        payment_method = codings[0].get("code", "")
    elif payment_method_obj.get("text"):
        payment_method = payment_method_obj.get("text", "")

    payment_date = parse_datetime_to_date(payment.get("date"))

    # Process items
    items = fhir_resource.get("item", [])
    for item in items:
        charge_id = item.get("itemSequence")

        # Determine transaction type from adjudications
        transaction_type = ""
        amount_value = ""

        adjudications = item.get("adjudication", [])
        for adj in adjudications:
            category = adj.get("category", {})
            codings = category.get("coding", [])
            for coding in codings:
                code = coding.get("code", "")
                if code in ("PAYMENT", "payment"):
                    transaction_type = "PAYMENT"
                    amount_value = (
                        str(adj.get("amount", {}).get("value", ""))
                        if adj.get("amount")
                        else ""
                    )
                    break
                elif code in ("ADJUSTMENT", "adjustment"):
                    transaction_type = "ADJUSTMENT"
                    amount_value = (
                        str(adj.get("amount", {}).get("value", ""))
                        if adj.get("amount")
                        else ""
                    )
                    break
                elif code in ("TRANSFERIN", "TRANSFEROUT", "transfer"):
                    transaction_type = (
                        "TRANSFERIN" if "IN" in code.upper() else "TRANSFEROUT"
                    )
                    amount_value = (
                        str(adj.get("amount", {}).get("value", ""))
                        if adj.get("amount")
                        else ""
                    )

                    # Extract transfer details from reason
                    reason = adj.get("reason", {})
                    reason_text = reason.get("text", "")
                    transfer_out_id = ""
                    transfer_type = ""

                    if reason_text:
                        # Parse "Transfer Out ID: xxx; Transfer Type: yyy"
                        parts = reason_text.split(";")
                        for part in parts:
                            if "Transfer Out ID:" in part:
                                transfer_out_id = part.replace(
                                    "Transfer Out ID:", ""
                                ).strip()
                            elif "Transfer Type:" in part:
                                transfer_type = part.replace(
                                    "Transfer Type:", ""
                                ).strip()

                    break

        # If payment.amount present, override with PAYMENT
        if payment_amount is not None and not transaction_type:
            transaction_type = "PAYMENT"
            amount_value = str(payment_amount)

        # Extract outstanding from notes
        outstanding = ""
        item_notes = item.get("note", [])
        for note in item_notes:
            note_text = note.get("text", "")
            if "Outstanding:" in note_text:
                outstanding = note_text.replace("Outstanding:", "").strip()

        row: dict[str, str] = {
            "Id": transaction_id,
            "Claim ID": claim_id,
            "Charge ID": str(charge_id) if charge_id is not None else "",
            "Patient ID": patient_id,
            "Type": transaction_type,
            "Amount": amount_value,
            "From Date": payment_date,
            "To Date": payment_date,
            "Place of Service": "",
            "Procedure Code": "",
            "Modifier1": "",
            "Modifier2": "",
            "DiagnosisRef1": "",
            "DiagnosisRef2": "",
            "DiagnosisRef3": "",
            "DiagnosisRef4": "",
            "Units": "",
            "Unit Amount": "",
            "Notes": "",
            "Line Note": "",
            "Department ID": "",
            "Fee Schedule ID": "",
            "Appointment ID": "",
            "Provider ID": "",
            "Supervising Provider ID": "",
            "Patient Insurance ID": "",
            "Method": payment_method,
            "Payments": str(payment_amount)
            if transaction_type == "PAYMENT" and payment_amount is not None
            else "",
            "Adjustments": amount_value if transaction_type == "ADJUSTMENT" else "",
            "Transfers": amount_value
            if transaction_type in ("TRANSFERIN", "TRANSFEROUT")
            else "",
            "Transfer Out ID": transfer_out_id
            if transaction_type in ("TRANSFERIN", "TRANSFEROUT")
            else "",
            "Transfer Type": transfer_type
            if transaction_type in ("TRANSFERIN", "TRANSFEROUT")
            else "",
            "Outstanding": outstanding,
        }

        rows.append(row)

    # If no items, create one row from payment info
    if not rows and payment_amount is not None:
        row = {
            "Id": transaction_id,
            "Claim ID": claim_id,
            "Charge ID": "",
            "Patient ID": patient_id,
            "Type": "PAYMENT",
            "Amount": "",
            "From Date": payment_date,
            "To Date": payment_date,
            "Place of Service": "",
            "Procedure Code": "",
            "Modifier1": "",
            "Modifier2": "",
            "DiagnosisRef1": "",
            "DiagnosisRef2": "",
            "DiagnosisRef3": "",
            "DiagnosisRef4": "",
            "Units": "",
            "Unit Amount": "",
            "Notes": "",
            "Line Note": "",
            "Department ID": "",
            "Fee Schedule ID": "",
            "Appointment ID": "",
            "Provider ID": "",
            "Supervising Provider ID": "",
            "Patient Insurance ID": "",
            "Method": payment_method,
            "Payments": str(payment_amount),
            "Adjustments": "",
            "Transfers": "",
            "Transfer Out ID": "",
            "Transfer Type": "",
            "Outstanding": "",
        }
        rows.append(row)

    return rows
