### FHIR → CSV mapping: Claim / ClaimResponse to claims_transactions.csv

This spec defines how to produce `claims_transactions.csv` rows from FHIR R4 `Claim` and `ClaimResponse` resources.

Scope and approach
- From a `Claim`, we produce one `CHARGE` row per `Claim.item` (sequence is used as `Charge ID`).
- From a `ClaimResponse`, we produce a transaction row aligned to its first `item` (by `itemSequence`) with the appropriate `Type` and monetary fields (`Payments`, `Adjustments`, `Transfers`).
- When a single resource lacks fields required by CSV (e.g., `Procedure Code` inside `ClaimResponse`), fields are left blank. Upstream callers can merge data from `Claim` and `ClaimResponse` sharing the same `Claim ID` and `Charge ID` if complete rows are needed.

## Field Mappings

### Claim → CSV (Type = CHARGE)
```python
# FHIR Claim → Synthea CSV claims_transactions mapping (CHARGE type)
# (source_field, target_field, semantic_concept, transform, notes)
claims_to_transactions_mapping = [
    (None, "claims_transactions.Id", "Transaction ID", "Generate txn-<Claim.id>-<item.sequence>", "Deterministic synthetic id for the row"),
    ("Claim.id", "claims_transactions.Claim ID", "Claim Identity", "Direct copy", ""),
    ("Claim.item.sequence", "claims_transactions.Charge ID", "Item Sequence", "Direct copy", ""),
    ("Claim.patient.reference", "claims_transactions.Patient ID", "Patient Reference", "Extract reference id", ""),
    (None, "claims_transactions.Type", "Transaction Type", "Set to CHARGE", ""),
    ("Claim.item.net.value", "claims_transactions.Amount", "Net Amount", "Direct copy", ""),
    ("Claim.billablePeriod.start", "claims_transactions.From Date", "Period Start", "Direct copy", ""),
    ("Claim.billablePeriod.end", "claims_transactions.To Date", "Period End", "Direct copy", ""),
    ("Claim.facility.reference", "claims_transactions.Place of Service", "Facility Reference", "Extract reference id", ""),
    ("Claim.item.productOrService", "claims_transactions.Procedure Code", "Procedure Code", "First coding code", ""),
    ("Claim.item.modifier", "claims_transactions.Modifier1/Modifier2", "Modifiers", "First two modifier codes", "If present"),
    ("Claim.item.diagnosisSequence", "claims_transactions.DiagnosisRef1..4", "Diagnosis References", "First 4 integers", ""),
    ("Claim.item.quantity.value", "claims_transactions.Units", "Quantity", "Direct copy", ""),
    ("Claim.note[].text", "claims_transactions.Notes/Line Note", "Notes", "Direct copy", ""),
    ("Claim.item.unitPrice.value", "claims_transactions.Unit Amount", "Unit Price", "Direct copy", ""),
    ("Claim.item.encounter[0].reference", "claims_transactions.Appointment ID", "Encounter Reference", "Extract reference id", "First encounter"),
    ("Claim.insurance[0].coverage.reference", "claims_transactions.Patient Insurance ID", "Insurance Coverage", "Extract reference id", ""),
    ("Claim.provider.reference", "claims_transactions.Provider ID", "Provider Reference", "Extract reference id", ""),
    ("Claim.careTeam where role.text=supervising", "claims_transactions.Supervising Provider ID", "Supervising Provider", "Extract provider reference id", "If any"),
]
```

### ClaimResponse → CSV (Type in {PAYMENT, ADJUSTMENT, TRANSFERIN, TRANSFEROUT})
```python
# FHIR ClaimResponse → Synthea CSV claims_transactions mapping
# (source_field, target_field, semantic_concept, transform, notes)
claimresponse_to_transactions_mapping = [
    ("ClaimResponse.id", "claims_transactions.Id", "Transaction ID", "Direct copy", ""),
    ("ClaimResponse.request.reference", "claims_transactions.Claim ID", "Claim Reference", "Extract reference id", ""),
    ("ClaimResponse.item[0].itemSequence", "claims_transactions.Charge ID", "Item Sequence", "Direct copy", "If present"),
    ("ClaimResponse.patient.reference", "claims_transactions.Patient ID", "Patient Reference", "Extract reference id", ""),
    ("ClaimResponse.payment.amount or adjudication", "claims_transactions.Type", "Transaction Type", "Derive from adjudication/payment", "PAYMENT if payment.amount present; ADJUSTMENT if adjudication category=adjustment; TRANSFERIN/TRANSFEROUT if category=transfer"),
    ("ClaimResponse.payment.type", "claims_transactions.Method", "Payment Method", "Extract coding.code or text", ""),
    ("ClaimResponse.payment.amount.value or adjudication.amount", "claims_transactions.Payments/Adjustments/Transfers", "Monetary Amounts", "Set from corresponding amounts", "Precedence as per Type derivation"),
    ("ClaimResponse.item.note containing Outstanding", "claims_transactions.Outstanding", "Outstanding Amount", "Extract amount from note text", "If note contains Outstanding: <amount>"),
    ("ClaimResponse.payment.date", "claims_transactions.From/To Date", "Payment Date", "Direct copy if present", "Otherwise leave blank"),
]
# Note: Place of Service, Procedure Code, Provider ID, etc. left blank if not present in ClaimResponse
```

Formatting rules
- Dates are converted to Synthea CSV style (ISO 8601 string accepted by this project).
- Unknown values are empty strings. Numeric values are stringified without altering the numeric value.

Limitations
- `ClaimResponse` does not carry certain line-level attributes required by CSV; complete enrichment requires joining with the corresponding `Claim` by `Claim ID` and `Charge ID`.
