### FHIR R4 Organization ➜ Synthea organizations.csv

This spec defines how a FHIR R4 `Organization` resource for providers maps back to a Synthea `organizations.csv` row.

## Field Mappings
```python
# FHIR Organization → Synthea CSV organizations mapping
# (source_field, target_field, semantic_concept, transform, notes)
organizations_reverse_mapping = [
    ("Organization.id", "organizations.Id", "Organization Identity", "Direct copy", "Required"),
    ("Organization.name", "organizations.Name", "Organization Name", "Direct copy", "Required"),
    ("Organization.address[0].line[0]", "organizations.Address", "Street Address", "Direct copy", "Optional"),
    ("Organization.address[0].city", "organizations.City", "City", "Direct copy", "Optional"),
    ("Organization.address[0].state", "organizations.State", "State", "Direct copy", "Optional"),
    ("Organization.address[0].postalCode", "organizations.Zip", "Postal Code", "Direct copy", "Optional"),
    ("Organization.address[0].extension[geolocation].latitude", "organizations.Lat", "Latitude", "Extract valueDecimal; stringify", "url=http://hl7.org/fhir/StructureDefinition/geolocation"),
    ("Organization.address[0].extension[geolocation].longitude", "organizations.Lon", "Longitude", "Extract valueDecimal; stringify", "url=http://hl7.org/fhir/StructureDefinition/geolocation"),
    ("Organization.telecom where system=phone", "organizations.Phone", "Phone Numbers", "Join multiple values with ; ", ""),
    ("Organization.extension[org-stats].extension[revenue]", "organizations.Revenue", "Revenue", "valueDecimal; stringify", "url=http://synthea.mitre.org/fhir/StructureDefinition/organization-stats"),
    ("Organization.extension[org-stats].extension[utilization]", "organizations.Utilization", "Utilization", "valueInteger; stringify", "url=http://synthea.mitre.org/fhir/StructureDefinition/organization-stats"),
]
```

## Notes
- If fields are missing in FHIR, output empty strings to preserve CSV schema.
- If no geolocation extension is present, `Lat` and `Lon` are empty.
- If multiple phone numbers are present, join with `; ` in the CSV.
