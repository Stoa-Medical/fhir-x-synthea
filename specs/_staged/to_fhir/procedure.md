# Procedure

## Semantic Context
The Procedure resource represents an action that is or was performed on or for a patient. This mapping transforms Synthea `procedures.csv` rows into FHIR R4 Procedure resources.

## Field Mappings
```python
# Synthea CSV procedures → FHIR Procedure mapping
# (source_field, target_field, semantic_concept, transform, notes)
procedures_mapping = [
    ("procedures.START", "Procedure.performedDateTime or Procedure.performedPeriod.start", "Procedure Start", "Format as ISO 8601", "If STOP present, use performedPeriod; else performedDateTime"),
    ("procedures.STOP", "Procedure.performedPeriod.end", "Procedure End", "Format as ISO 8601", "Optional; only when present"),
    ("procedures.PATIENT", "Procedure.subject", "Patient Reference", "Create Reference(\"Patient/{id}\")", "Subject patient"),
    ("procedures.ENCOUNTER", "Procedure.encounter", "Encounter Reference", "Create Reference(\"Encounter/{id}\")", "Associated encounter"),
    ("procedures.SYSTEM", "Procedure.code.coding[0].system", "Code System", "Direct copy", "Typically http://snomed.info/sct"),
    ("procedures.CODE", "Procedure.code.coding[0].code", "Procedure Code", "Direct copy", "SNOMED CT code"),
    ("procedures.DESCRIPTION", "Procedure.code.coding[0].display", "Code Display", "Direct copy", "Human-readable description"),
    ("procedures.DESCRIPTION", "Procedure.code.text", "Code Text", "Direct copy", "Fallback text description"),
    ("procedures.BASE_COST", "Procedure.extension[baseCost]", "Line Item Cost", "Create extension valueMoney(USD)", "Costs are often modeled in Claim/ChargeItem; extension used here"),
    ("procedures.REASONCODE", "Procedure.reasonCode[0].coding[0].code", "Reason Code", "Direct copy", "SNOMED CT reason code"),
    ("procedures.REASONDESCRIPTION", "Procedure.reasonCode[0].coding[0].display", "Reason Display", "Direct copy", "Human-readable reason"),
]
```

## Defaults and Rules
- Procedure.status is set to "completed" for finalized CSV records.
- If both START and STOP are present → use `performedPeriod` with start and end.
- If only START is present → use `performedDateTime`.
- `id` is generated deterministically from PATIENT, START, and CODE.
- Cost represented via extension:
```json
{
  "url": "http://example.org/fhir/StructureDefinition/baseCost",
  "valueMoney": { "value": <number>, "currency": "USD" }
}
```

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_fhir.procedure.map_procedure`
- Uses common transformers for datetime formatting and reference creation
- Accepts numeric BASE_COST; non-numeric values are ignored
