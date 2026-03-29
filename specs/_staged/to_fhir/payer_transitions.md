### Synthea payer_transitions.csv ➜ FHIR R4 Coverage

Maps a Synthea `payer_transitions.csv` row (insurance coverage changes over time) to a FHIR `Coverage` resource. The payer is represented as `Organization`; the beneficiary is the `Patient`.

## Field Mappings
```python
# Synthea CSV payer_transitions → FHIR Coverage mapping
# (source_field, target_field, semantic_concept, transform, notes)
payer_transitions_mapping = [
    ("Patient", "Coverage.beneficiary.reference", "Patient Reference", "Patient/{uuid}", "Required beneficiary"),
    ("Member ID", "Coverage.subscriberId", "Member ID", "Direct copy", "Alternatively could be an identifier"),
    ("Start_Year", "Coverage.period.start", "Coverage Start", "Rendered as YYYY-01-01", "Inclusive start of year"),
    ("End_Year", "Coverage.period.end", "Coverage End", "Rendered as YYYY-12-31", "Inclusive end of year"),
    ("Payer", "Coverage.payor[0].reference", "Payer Reference", "Organization/{uuid}", "Primary payer"),
    ("Secondary Payer", "Coverage.payor[1].reference", "Secondary Payer Reference", "Organization/{uuid}", "Additional payer if present"),
    ("Ownership", "Coverage.relationship", "Subscriber Relationship", "Map to subscriber-relationship codes", "Self→self, Spouse→spouse; Guardian stored as text if no standard code"),
    ("Owner Name", "Coverage.extension[url=http://synthea.mitre.org/fhir/StructureDefinition/policy-owner-name].valueString", "Owner Name", "Direct copy", "Free-text name of policy owner"),
    (None, "Coverage.status", "Coverage Status", "Set to active", "Status is inferred from period"),
    (None, "Coverage.id", "Resource ID", "Generate cov-{Patient}-{Start_Year}-{Payer}", "Deterministic composite"),
]
```

## Semantic Notes

- The payer organization is modeled via `Organization` and referenced in `Coverage.payor`.
- Only year precision is available in the CSV; we materialize start/end as the first and last day of the year respectively to respect inclusive semantics.
- `Coverage.relationship` uses `http://terminology.hl7.org/CodeSystem/subscriber-relationship` where possible. `Guardian` is retained as `text` if no exact standard code applies.
- While this dataset could inform `EnrollmentRequest`/`EnrollmentResponse`, those resources are not emitted here.

## Implementation Notes

- Owner free-text goes into a dedicated extension to avoid manufacturing unmanaged `Patient`/`RelatedPerson` references.
- If `Member ID` needs stronger modeling, a `Coverage.identifier` with a local system can be added in a future iteration.
