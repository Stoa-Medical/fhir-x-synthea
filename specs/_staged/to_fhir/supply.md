### Synthea supplies.csv ➜ FHIR R4 SupplyDelivery

This spec defines how a single row from Synthea `supplies.csv` maps to a FHIR R4 `SupplyDelivery` resource. The CSV records supplies used (fulfilled), which aligns most closely with `SupplyDelivery`.

## Field Mappings
```python
# Synthea CSV supplies → FHIR SupplyDelivery mapping
# (source_field, target_field, semantic_concept, transform, notes)
supplies_mapping = [
    ("DATE", "SupplyDelivery.occurrenceDateTime", "Date", "date → FHIR dateTime (ISO 8601)", "If only a date is present, time defaults to 00:00:00+00:00"),
    ("PATIENT", "SupplyDelivery.patient", "Patient", "Patient/{PATIENT}", "Reference(Patient)"),
    ("ENCOUNTER", "SupplyDelivery.extension[url=http://hl7.org/fhir/StructureDefinition/resource-encounter].valueReference", "Encounter", "Encounter/{ENCOUNTER}", "SupplyDelivery in R4 does not have an encounter element, so the standard Resource Encounter extension is used"),
    ("CODE", "SupplyDelivery.suppliedItem.itemCodeableConcept.coding[0].code", "Code (SNOMED-CT)", "Direct copy", "system = http://snomed.info/sct"),
    ("DESCRIPTION", "SupplyDelivery.suppliedItem.itemCodeableConcept.coding[0].display", "Description", "Direct copy", "Also set suppliedItem.itemCodeableConcept.text"),
    ("DESCRIPTION", "SupplyDelivery.suppliedItem.itemCodeableConcept.text", "Description text", "Direct copy", "Fallback text"),
    ("QUANTITY", "SupplyDelivery.suppliedItem.quantity.value", "Quantity", "Numeric conversion", "No unit is assumed"),
    (None, "SupplyDelivery.status", "Status", "Set to completed", "Since supplies were used/fulfilled"),
    (None, "SupplyDelivery.id", "Resource ID", "Generate supply-{PATIENT}-{DATE}{time?}-{CODE}", "Deterministic string for consistency"),
]
```

### Notes on SupplyRequest

While `supplies.csv` best represents fulfillment (`SupplyDelivery`), the following correspondences are common if a request view is desired:

- Date → `SupplyRequest.authoredOn`
- Patient → `SupplyRequest.subject`
- Encounter → same extension `resource-encounter`
- Code/Description → `SupplyRequest.itemCodeableConcept`
- Quantity → `SupplyRequest.quantity`

This library’s forward mapper produces `SupplyDelivery` per above.
