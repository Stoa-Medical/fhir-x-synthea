# CarePlan (FHIR → careplans.csv)

## Primary Source Resource
- CarePlan

## Field Mappings
```python
# FHIR CarePlan → Synthea CSV careplans mapping
# (source_field, target_field, semantic_concept, transform, notes)
careplans_reverse_mapping = [
    ("CarePlan.id", "careplans.Id", "Logical id", "Direct", ""),
    ("CarePlan.period.start", "careplans.Start", "Start Date/Time", "Parse FHIR datetime → Synthea format", ""),
    ("CarePlan.period.end", "careplans.Stop", "End Date/Time", "Parse FHIR datetime", "Optional"),
    ("CarePlan.subject", "careplans.Patient", "Patient Reference", "Extract reference id", "Patient/{id}"),
    ("CarePlan.encounter", "careplans.Encounter", "Encounter Reference", "Extract reference id", "Encounter/{id}"),
    ("CarePlan.category[0] (SNOMED)", "careplans.Code", "Category Code", "Extract coding by SNOMED system", "Fallback to first coding"),
    ("CarePlan.description or title", "careplans.Description", "Description", "Prefer description; fallback title", ""),
    ("CarePlan.reasonCode[0] (SNOMED)", "careplans.ReasonCode", "Reason Code", "Extract coding code", "Fallback to first coding"),
    ("CarePlan.reasonCode[0] (SNOMED)", "careplans.ReasonDescription", "Reason Description", "Extract display or text", ""),
]
```

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_synthea_csv.careplan.map_fhir_careplan_to_csv`
- `CarePlan.addresses` is not mapped unless a concrete `Condition` id is present in source data.
