# CarePlan (careplans.csv → FHIR CarePlan)

## Semantic Context
The `careplans.csv` table records care plans initiated for patients. This mapping targets the FHIR R4 `CarePlan` resource. Core temporal context is captured in `CarePlan.period`. Patient and encounter linkage are modeled with references. The clinical rationale is represented with `CarePlan.reasonCode` using SNOMED CT (addresses may reference `Condition` when a condition identifier is available).

## Field Mappings
```python
# Synthea CSV careplans → FHIR CarePlan mapping
# (source_field, target_field, semantic_concept, transform, notes)
careplans_mapping = [
    ("careplans.Id", "CarePlan.id", "Logical id", "Direct", "Also could be represented in identifier as a business id"),
    ("careplans.Start", "CarePlan.period.start", "Plan start", "ISO 8601", "From Synthea datetime"),
    ("careplans.Stop", "CarePlan.period.end", "Plan end", "ISO 8601", "Optional"),
    ("careplans.Patient", "CarePlan.subject", "Subject", "Reference(\"Patient/{id}\")", "Required reference"),
    ("careplans.Encounter", "CarePlan.encounter", "Encounter", "Reference(\"Encounter/{id}\")", "Optional reference"),
    ("careplans.Code", "CarePlan.category[0].coding[0].code", "Category code", "Direct", "SNOMED CT"),
    (None, "CarePlan.category[0].coding[0].system", "Code system", "http://snomed.info/sct", ""),
    ("careplans.Description", "CarePlan.description", "Narrative description", "Direct", "Free text description"),
    ("careplans.Description", "CarePlan.title", "Human title", "Direct", "Optional convenience field"),
    ("careplans.ReasonCode", "CarePlan.reasonCode[0].coding[0].code", "Rationale code", "Direct", "SNOMED CT; see note on addresses"),
    ("careplans.ReasonDescription", "CarePlan.reasonCode[0].coding[0].display", "Rationale text", "Direct", ""),
    (None, "CarePlan.status", "Lifecycle status", "active if no Stop else completed", "Heuristic"),
    (None, "CarePlan.intent", "Intent", "plan", "Required by profile"),
]
```

## Notes on Addresses vs Reason
- FHIR R4 `CarePlan.addresses` accepts references to `Condition`/`Observation`/`MedicationRequest`, not a `CodeableConcept`.
- When only a SNOMED diagnosis code/description is available (no Condition id), the mapping uses `CarePlan.reasonCode`.
- If a related `Condition` identifier is provided by the source in the future, add a `CarePlan.addresses` reference to `Condition/{id}`.

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_fhir.careplan.map_careplan`
- Uses helper utilities from `fhir_x_synthea_csv.common.transformers`.
