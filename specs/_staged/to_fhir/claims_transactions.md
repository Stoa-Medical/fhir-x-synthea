### CSV → FHIR mapping: claims_transactions.csv to Claim and ClaimResponse

This spec defines how a single row in `claims_transactions.csv` maps into elements of FHIR R4 `Claim` and/or `ClaimResponse` resources. The CSV represents transactions at the line-item level. We map line-item attributes to `Claim.item` and financial outcomes to `ClaimResponse.item.adjudication` (and top-level `payment` when applicable).

Assumptions and scope
- One CSV row corresponds to one Claim line item (identified by `Claim ID` + `Charge ID`) and may also carry adjudication/payment info for that line item.
- We do not aggregate multiple CSV rows into a single Claim/ClaimResponse here; instead, each row can produce:
  - a `Claim` skeleton focusing on a single `item` and contextual fields, and
  - a `ClaimResponse` skeleton referencing the `Claim` and the same `item` sequence with adjudication data.
- Codes for transaction `Type` and `Method` are captured in CodeableConcepts using local code systems where HL7 core codes do not provide a precise fit, keeping values in `code` and/or `text` for round-trip fidelity.

## Field Mappings
```python
# Synthea CSV claims_transactions → FHIR Claim and ClaimResponse mapping
# (source_field, target_field, semantic_concept, transform, notes)
claims_transactions_mapping = [
    ("Id", "ClaimResponse.id", "Transaction ID", "Unique per transaction", "Also carried as Claim.item.extension for traceability"),
    ("Claim ID", "Claim.id", "Claim Identity", "Direct copy", "Also referenced by ClaimResponse.request=Claim/{Claim ID}"),
    ("Charge ID", "Claim.item.sequence", "Item Sequence", "Integer", "Also ClaimResponse.item.itemSequence"),
    ("Patient ID", "Claim.patient and ClaimResponse.patient", "Patient Reference", "Patient/{Patient ID}", ""),
    ("Place of Service", "Claim.facility", "Facility Reference", "Organization/{Place of Service}", ""),
    ("Procedure Code", "Claim.item.productOrService.coding[0]", "Procedure Code", "system=http://snomed.info/sct, code=value", "display from Notes/Line Note if present"),
    ("Provider ID", "Claim.provider", "Provider Reference", "Practitioner/{Provider ID}", ""),
    ("From Date", "Claim.billablePeriod.start", "Period Start", "ISO 8601", ""),
    ("To Date", "Claim.billablePeriod.end", "Period End", "ISO 8601", ""),
    ("Appointment ID", "Claim.item.encounter[0]", "Encounter Reference", "Encounter/{Appointment ID}", "If present"),
    ("Units", "Claim.item.quantity.value", "Quantity", "Decimal", ""),
    ("Unit Amount", "Claim.item.unitPrice.value", "Unit Price", "Decimal", ""),
    ("Amount", "Claim.item.net.value", "Net Amount", "Decimal", "For CHARGE or TRANSFERIN"),
    ("DiagnosisRef1..4", "Claim.item.diagnosisSequence", "Diagnosis References", "List of integers 1-8", "Refer to Claim.diagnosis entries at claim level"),
    ("Type", "ClaimResponse.item.adjudication.category", "Transaction Type", "Local system code", "system=http://synthea.tools/CodeSystem/claims-transaction-type, codes: CHARGE/PAYMENT/ADJUSTMENT/TRANSFERIN/TRANSFEROUT"),
    ("Method", "ClaimResponse.payment.type", "Payment Method", "CodeableConcept", "Local system http://synthea.tools/CodeSystem/payment-method; also set ClaimResponse.payment.date from To Date"),
    ("Payments", "ClaimResponse.payment.amount.value", "Payment Amount", "Decimal if Type=PAYMENT", "Also include adjudication with category code payment"),
    ("Adjustments", "ClaimResponse.item.adjudication", "Adjustment Amount", "Decimal if Type=ADJUSTMENT", "category code adjustment (local)"),
    ("Transfers", "ClaimResponse.item.adjudication", "Transfer Amount", "Decimal if Type=TRANSFERIN/TRANSFEROUT", "category code transfer; carry Transfer Out ID and Transfer Type as adjudication.reason.text"),
    ("Outstanding", "ClaimResponse.item.note.text", "Outstanding Amount", "Append-only text", "Form: Outstanding: <amount>"),
    ("Department ID, Fee Schedule ID", "Claim.item.note.text", "Additional Info", "Text if present", ""),
    ("Notes, Line Note", "Claim.note[].text", "Notes", "Text", "Implementation uses Claim.note[].text for simplicity"),
    ("Supervising Provider ID", "Claim.careTeam", "Supervising Provider", "Practitioner/{Supervising Provider ID}", "role.text=supervising"),
    ("Patient Insurance ID", "Claim.insurance[0].coverage", "Insurance Coverage", "Coverage/{Patient Insurance ID}", "If present; also mirrored to ClaimResponse.insurance"),
    ("Transfer Out ID, Transfer Type", "ClaimResponse.item.adjudication.reason.text", "Transfer Details", "Text", "As noted in adjudication.reason.text"),
]
```

Data typing and formatting
- All dates are emitted as ISO 8601 strings (e.g., `YYYY-MM-DD` or `YYYY-MM-DDThh:mm:ss+00:00`) consistent with the rest of this library.
- Numeric fields (`Units`, `Unit Amount`, `Amount`, `Payments`, `Adjustments`, `Transfers`, `Outstanding`) are mapped to decimal values in FHIR and preserved as strings on CSV round-trip.

Limitations
- This mapping produces self-contained `Claim`/`ClaimResponse` fragments per transaction; assembling a full Claim with multiple items requires upstream grouping by `Claim ID`.
- Standard adjudication categories are not exhaustive for all Synthea transaction types; we therefore use a local code system to preserve semantics without loss.
