### FHIR R4 Coverage ➜ Synthea payer_transitions.csv

Maps a FHIR `Coverage` resource back to a `payer_transitions.csv` row.

## Field Mappings
```python
# FHIR Coverage → Synthea CSV payer_transitions mapping
# (source_field, target_field, semantic_concept, transform, notes)
payer_transitions_reverse_mapping = [
    ("Coverage.beneficiary.reference", "payer_transitions.Patient", "Patient Reference", "Extract Patient/{id} → id", ""),
    ("Coverage.subscriberId or Coverage.identifier", "payer_transitions.Member ID", "Member ID", "Direct copy", "Prefer subscriberId; else first identifier.value"),
    ("Coverage.period.start", "payer_transitions.Start_Year", "Start Year", "Year component of date (YYYY)", ""),
    ("Coverage.period.end", "payer_transitions.End_Year", "End Year", "Year component of date (YYYY)", ""),
    ("Coverage.payor[0].reference", "payer_transitions.Payer", "Payer Reference", "Extract Organization/{id} → id", ""),
    ("Coverage.payor[1].reference", "payer_transitions.Secondary Payer", "Secondary Payer Reference", "Extract Organization/{id} → id", "Optional second payer id if present"),
    ("Coverage.relationship", "payer_transitions.Ownership", "Ownership", "Map codes from subscriber-relationship", "Self→Self, Spouse→Spouse; if text=Guardian, emit Guardian; otherwise empty"),
    ("Coverage.extension[policy-owner-name].valueString", "payer_transitions.Owner Name", "Owner Name", "Direct copy", "url=http://synthea.mitre.org/fhir/StructureDefinition/policy-owner-name; optional"),
]
```

## Notes

- If dates are missing, emit empty strings; CSV schema allows blanks.
- Year extraction should be robust to full datetime strings.
- Unknown relationship codes map to empty string to avoid incorrect semantics.
