# Immunization

## Semantic Context
This mapping transforms Synthea `immunizations.csv` rows (patient immunization administrations) into FHIR R4 `Immunization` resources. The resource is categorized under Clinical/Pharmacy (FHIR Maturity Level: 5). The `Patient` it references is Normative.

## Field Mappings
```python
# Synthea CSV immunizations → FHIR Immunization mapping
# (source_field, target_field, semantic_concept, transform, notes)
immunizations_mapping = [
    ("immunizations.DATE", "Immunization.occurrenceDateTime", "Administration Date/Time", "Format as ISO 8601", "When the immunization was administered"),
    ("immunizations.PATIENT", "Immunization.patient", "Patient Reference", "Create Reference(\"Patient/{id}\")", "Recipient patient"),
    ("immunizations.ENCOUNTER", "Immunization.encounter", "Encounter Reference", "Create Reference(\"Encounter/{id}\")", "Encounter where administered"),
    ("immunizations.CODE", "Immunization.vaccineCode.coding[0].code", "CVX Code", "Direct copy", "Vaccine administered"),
    ("immunizations.DESCRIPTION", "Immunization.vaccineCode.coding[0].display", "Code Display", "Direct copy", "Human-readable vaccine description"),
    ("immunizations.CODE", "Immunization.vaccineCode.coding[0].system", "Code System", "Set to \"http://hl7.org/fhir/sid/cvx\"", "CVX code system URI"),
    ("immunizations.DESCRIPTION", "Immunization.vaccineCode.text", "Code Text", "Direct copy", "Fallback text"),
    ("immunizations.COST", "Immunization.extension[url=http://synthea.mitre.org/fhir/StructureDefinition/immunization-cost].valueDecimal", "Line Item Cost", "Copy as decimal", "Not part of core; preserved via extension"),
    (None, "Immunization.status", "Administration Status", "Set to \"completed\"", "Synthea exports administered immunizations"),
    (None, "Immunization.id", "Resource ID", "Generate from DATE+PATIENT+CODE", "Composite key"),
]
```

## Notes on Financial Data
Cost is not part of the core `Immunization` resource. It is most appropriately modeled in financial resources such as `Claim` or `ExplanationOfBenefit` (Maturity Level: 2). This mapping preserves `COST` using a simple extension at `http://synthea.mitre.org/fhir/StructureDefinition/immunization-cost` with `valueDecimal`. Downstream systems may alternatively materialize financial resources.

## Semantic Rules and Constraints
- CVX codes from Synthea are preserved in `vaccineCode`.
- `status` is set to `completed` for administered immunizations.
- `occurrenceDateTime` is required and formatted as ISO 8601.
- Patient and Encounter are represented as references.

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_fhir.immunization.map_immunization`
- Uses common transformers for datetime formatting and reference building.
- Generates stable IDs for resource references from composite keys.
