# Mapping Specifications

Each file in the directory has the following structure:

## Template Structure

```markdown
# Resource / Model Name

## Semantic Context
Brief description of the semantic entity and scope of this mapping.

## Field Mappings
| Source Field | Target Field | Semantic Concept | Transform | Semantic Notes |
|--------------|--------------|------------------|-----------|----------------|
| Patient.id | person.person_id | Patient Identity | | Unique patient identifier |
| Patient.birthDate | person.year_of_birth | Birth Date | Extract year only | Precision loss acceptable for analytics |
| Patient.gender | person.gender_concept_id | Administrative Gender | Lookup OMOP concept | Maps to gender identity, not biological sex |
| Patient.deceased[x] | person.death_datetime | Death Status | Convert boolean to datetime | If boolean true, set death_datetime to NULL |

## Semantic Rules and Constraints
- Semantic decisions and constraints
- Data quality assumptions
- Terminology mappings (SNOMED, LOINC, etc.)

## Implementation Notes
- Code references and functions
- Performance considerations
- Known semantic edge cases
```

## Directory Structure
- `to_fhir/` — Synthea CSV → FHIR mappings (core: patient, encounter, condition, allergy)
- `to_synthea/` — FHIR → Synthea CSV mappings (core: patient, encounter, condition, allergy)
- `_staged/` — Specs for additional resource types not yet wired into orchestration
