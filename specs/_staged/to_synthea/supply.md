### FHIR R4 SupplyDelivery ➜ Synthea supplies.csv

This spec defines how a FHIR R4 `SupplyDelivery` resource maps back to a Synthea `supplies.csv` row.

## Field Mappings
```python
# FHIR SupplyDelivery → Synthea CSV supplies mapping
# (source_field, target_field, semantic_concept, transform, notes)
supplies_reverse_mapping = [
    ("SupplyDelivery.occurrenceDateTime or occurrencePeriod.start", "supplies.DATE", "Date", "Parse FHIR dateTime to date-only string", "YYYY-MM-DD"),
    ("SupplyDelivery.patient.reference", "supplies.PATIENT", "Patient Reference", "Extract Patient/{id} → {id}", "Required"),
    ("SupplyDelivery.extension[resource-encounter].valueReference", "supplies.ENCOUNTER", "Encounter Reference", "Extract Encounter/{id} → {id}", "url=http://hl7.org/fhir/StructureDefinition/resource-encounter; empty if extension missing"),
    ("SupplyDelivery.suppliedItem.itemCodeableConcept.coding (SNOMED)", "supplies.CODE", "Code (SNOMED-CT)", "Extract coding.code", "Prefer system=http://snomed.info/sct; else first coding"),
    ("SupplyDelivery.suppliedItem.itemCodeableConcept", "supplies.DESCRIPTION", "Description", "Prefer coding.display; fallback to text", ""),
    ("SupplyDelivery.suppliedItem.quantity.value", "supplies.QUANTITY", "Quantity", "Numeric value (stringified)", ""),
]
```

### Accepted FHIR variants

- If `occurrencePeriod` present, use `.start` for DATE; otherwise `occurrenceDateTime`.
- If no SNOMED coding, use first available coding.
- If no `resource-encounter` extension, output `ENCOUNTER` empty.
