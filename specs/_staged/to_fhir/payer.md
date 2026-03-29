### Synthea payers.csv ➜ FHIR R4 Organization (plus extensions)

This spec defines how a Synthea `payers.csv` row maps to a FHIR R4 `Organization` resource representing the payer entity. Aggregate/statistical fields are represented via a custom extension, since they are not first-class Organization attributes.

## Field Mappings
```python
# Synthea CSV payers → FHIR Organization mapping
# (source_field, target_field, semantic_concept, transform, notes)
payers_mapping = [
    ("payers.Id", "Organization.id", "Organization Identity", "Direct copy", "Required primary key (UUID)"),
    ("payers.Name", "Organization.name", "Payer Name", "Direct copy", "Required payer display name"),
    ("payers.Ownership", "Organization.extension[url=http://synthea.mitre.org/fhir/StructureDefinition/payer-ownership].valueCode", "Ownership", "Lowercase", "Values such as Government or Private; stored as lowercase code in extension"),
    ("payers.Address", "Organization.address[0].line[0]", "Street Address", "Direct copy", "Optional street address"),
    ("payers.City", "Organization.address[0].city", "City", "Direct copy", "Optional city"),
    ("payers.State_Headquartered", "Organization.address[0].state", "State", "Direct copy", "Optional state/province (US state abbreviation)"),
    ("payers.Zip", "Organization.address[0].postalCode", "Postal Code", "Direct copy", "Optional postal code"),
    ("payers.Phone", "Organization.telecom[n]", "Phone Numbers", "Split on [,;/|] and trim", "system=phone for each"),
    (None, "Organization.type[0].coding[0]", "Organization Type", "Set to Insurance Company", "system=http://terminology.hl7.org/CodeSystem/organization-type, code=ins"),
    ("Amount_Covered", "Organization.extension[payer-stats].extension[amountCovered].valueDecimal", "Amount Covered", "Decimal", "Custom extension"),
    ("Amount_Uncovered", "Organization.extension[payer-stats].extension[amountUncovered].valueDecimal", "Amount Uncovered", "Decimal", "Custom extension"),
    ("Revenue", "Organization.extension[payer-stats].extension[revenue].valueDecimal", "Revenue", "Decimal", "Custom extension"),
    ("Covered_Encounters", "Organization.extension[payer-stats].extension[coveredEncounters].valueInteger", "Covered Encounters", "Integer", "Custom extension"),
    ("Uncovered_Encounters", "Organization.extension[payer-stats].extension[uncoveredEncounters].valueInteger", "Uncovered Encounters", "Integer", "Custom extension"),
    ("Covered_Medications", "Organization.extension[payer-stats].extension[coveredMedications].valueInteger", "Covered Medications", "Integer", "Custom extension"),
    ("Uncovered_Medications", "Organization.extension[payer-stats].extension[uncoveredMedications].valueInteger", "Uncovered Medications", "Integer", "Custom extension"),
    ("Covered_Procedures", "Organization.extension[payer-stats].extension[coveredProcedures].valueInteger", "Covered Procedures", "Integer", "Custom extension"),
    ("Uncovered_Procedures", "Organization.extension[payer-stats].extension[uncoveredProcedures].valueInteger", "Uncovered Procedures", "Integer", "Custom extension"),
    ("Covered_Immunizations", "Organization.extension[payer-stats].extension[coveredImmunizations].valueInteger", "Covered Immunizations", "Integer", "Custom extension"),
    ("Uncovered_Immunizations", "Organization.extension[payer-stats].extension[uncoveredImmunizations].valueInteger", "Uncovered Immunizations", "Integer", "Custom extension"),
    ("Unique_Customers", "Organization.extension[payer-stats].extension[uniqueCustomers].valueInteger", "Unique Customers", "Integer", "Custom extension"),
    ("QOLS_Avg", "Organization.extension[payer-stats].extension[qolsAvg].valueDecimal", "QOLS Average", "Decimal", "Custom extension"),
    ("Member_Months", "Organization.extension[payer-stats].extension[memberMonths].valueInteger", "Member Months", "Integer", "Custom extension"),
]
# Note: payer-stats extension URL = http://synthea.mitre.org/fhir/StructureDefinition/payer-stats
```

## Semantic Notes

- The payer entity is captured as `Organization`. Specific offerings would be modeled with `InsurancePlan`, and patient enrollment under a plan with `Coverage`. The CSV does not contain per-plan/enrollment records, so those resources are not directly produced here.
- Aggregate statistics are not standard elements and therefore are placed into a custom extension as described above.
- Ownership is stored as an extension to preserve the original Synthea semantics. A separate `type` coding of insurance company is included to broadly classify the organization.
