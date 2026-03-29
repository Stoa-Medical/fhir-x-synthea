# Observation

## Semantic Context
The Observation resource represents measurements and simple assertions about a patient. This mapping transforms Synthea CSV observation data (vital signs, lab results, social history) into FHIR R4 Observation resources.

## Field Mappings
```python
# Synthea CSV observations → FHIR Observation mapping
# (source_field, target_field, semantic_concept, transform, notes)
observations_mapping = [
    ("observations.DATE", "Observation.effectiveDateTime", "Observation Date/Time", "Format as ISO 8601", "When observation was made"),
    ("observations.PATIENT", "Observation.subject", "Patient Reference", "Create Reference(\"Patient/{id}\")", "Subject of observation"),
    ("observations.ENCOUNTER", "Observation.encounter", "Encounter Reference", "Create Reference(\"Encounter/{id}\")", "Associated encounter"),
    ("observations.CODE", "Observation.code.coding[0].code", "LOINC Code", "Direct copy", "LOINC observation code"),
    ("observations.DESCRIPTION", "Observation.code.coding[0].display", "Code Display", "Direct copy", "Human-readable description"),
    ("observations.CODE", "Observation.code.coding[0].system", "Code System", "Set to \"http://loinc.org\"", "LOINC system URI"),
    ("observations.DESCRIPTION", "Observation.code.text", "Code Text", "Direct copy", "Fallback text"),
    ("observations.VALUE", "Observation.value[x]", "Observation Value", "Type-based conversion", "Numeric→valueQuantity, Text→valueString"),
    ("observations.UNITS", "Observation.valueQuantity.unit", "Value Units", "Direct copy", "Unit of measure"),
    ("observations.UNITS", "Observation.valueQuantity.code", "UCUM Code", "Direct copy", "UCUM unit code"),
    ("observations.UNITS", "Observation.valueQuantity.system", "Unit System", "Set to \"http://unitsofmeasure.org\"", "UCUM system"),
    ("observations.TYPE", "Observation.category", "Observation Category", "Map to category coding", "vital-signs, laboratory, social-history, etc."),
    (None, "Observation.status", "Observation Status", "Set to \"final\"", "All CSV observations are final"),
    (None, "Observation.id", "Resource ID", "Generate from DATE+PATIENT+CODE", "Composite key"),
]
```

## Value Type Detection Rules
- If VALUE is numeric and UNITS present → valueQuantity
- If VALUE is numeric without UNITS → valueQuantity with unit "1"
- If VALUE is text/string → valueString
- If VALUE is boolean (true/false) → valueBoolean
- If VALUE is empty/null → no value element

## Category Mapping
| TYPE Value | FHIR Category |
|------------|---------------|
| vital-signs | {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]} |
| laboratory | {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory", "display": "Laboratory"}]} |
| survey | {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "survey", "display": "Survey"}]} |
| social-history | {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "social-history", "display": "Social History"}]} |
| imaging | {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "imaging", "display": "Imaging"}]} |
| procedure | {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "procedure", "display": "Procedure"}]} |

## Semantic Rules and Constraints
- All observations have status="final" (CSV export only contains completed observations)
- LOINC codes are preserved directly from Synthea
- Units should be UCUM-compliant (Synthea generally uses UCUM)
- Observation.issued can be set to DATE if tracking when result was reported
- Multiple observations with same DATE+PATIENT+ENCOUNTER may exist (different codes)

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_fhir.observation.observation_mapper`
- Handles both vital signs and laboratory results
- Smart value type detection based on content
- Preserves LOINC coding from Synthea
- Uses common transformers for datetime formatting
