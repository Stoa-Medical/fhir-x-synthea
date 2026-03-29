### FHIR R4 Organization ➜ Synthea payers.csv

This spec defines how a FHIR R4 `Organization` resource representing a payer maps back to a Synthea `payers.csv` row. Aggregate/statistical fields are expected in a custom extension.

## Field Mappings
```python
# FHIR Organization → Synthea CSV payers mapping
# (source_field, target_field, semantic_concept, transform, notes)
payers_reverse_mapping = [
    ("Organization.id", "payers.Id", "Organization Identity", "Direct copy", "Required"),
    ("Organization.name", "payers.Name", "Payer Name", "Direct copy", "Required"),
    ("Organization.extension[payer-ownership].valueCode", "payers.Ownership", "Ownership", "Direct copy", "url=http://synthea.mitre.org/fhir/StructureDefinition/payer-ownership; if missing, output empty string"),
    ("Organization.address[0].line[0]", "payers.Address", "Street Address", "Direct copy", "Optional"),
    ("Organization.address[0].city", "payers.City", "City", "Direct copy", "Optional"),
    ("Organization.address[0].state", "payers.State_Headquartered", "State", "Direct copy", "Optional"),
    ("Organization.address[0].postalCode", "payers.Zip", "Postal Code", "Direct copy", "Optional"),
    ("Organization.telecom where system=phone", "payers.Phone", "Phone Numbers", "Join values with ; ", "Optional"),
    ("Organization.extension[payer-stats].extension[amountCovered]", "payers.Amount_Covered", "Amount Covered", "valueDecimal (stringified)", "url=http://synthea.mitre.org/fhir/StructureDefinition/payer-stats"),
    ("Organization.extension[payer-stats].extension[amountUncovered]", "payers.Amount_Uncovered", "Amount Uncovered", "valueDecimal", ""),
    ("Organization.extension[payer-stats].extension[revenue]", "payers.Revenue", "Revenue", "valueDecimal", ""),
    ("Organization.extension[payer-stats].extension[coveredEncounters]", "payers.Covered_Encounters", "Covered Encounters", "valueInteger (string)", ""),
    ("Organization.extension[payer-stats].extension[uncoveredEncounters]", "payers.Uncovered_Encounters", "Uncovered Encounters", "valueInteger", ""),
    ("Organization.extension[payer-stats].extension[coveredMedications]", "payers.Covered_Medications", "Covered Medications", "valueInteger", ""),
    ("Organization.extension[payer-stats].extension[uncoveredMedications]", "payers.Uncovered_Medications", "Uncovered Medications", "valueInteger", ""),
    ("Organization.extension[payer-stats].extension[coveredProcedures]", "payers.Covered_Procedures", "Covered Procedures", "valueInteger", ""),
    ("Organization.extension[payer-stats].extension[uncoveredProcedures]", "payers.Uncovered_Procedures", "Uncovered Procedures", "valueInteger", ""),
    ("Organization.extension[payer-stats].extension[coveredImmunizations]", "payers.Covered_Immunizations", "Covered Immunizations", "valueInteger", ""),
    ("Organization.extension[payer-stats].extension[uncoveredImmunizations]", "payers.Uncovered_Immunizations", "Uncovered Immunizations", "valueInteger", ""),
    ("Organization.extension[payer-stats].extension[uniqueCustomers]", "payers.Unique_Customers", "Unique Customers", "valueInteger", ""),
    ("Organization.extension[payer-stats].extension[qolsAvg]", "payers.QOLS_Avg", "QOLS Average", "valueDecimal", ""),
    ("Organization.extension[payer-stats].extension[memberMonths]", "payers.Member_Months", "Member Months", "valueInteger", ""),
]
# Note: Values should be stringified without additional formatting. Missing values should be rendered as empty strings.
```
