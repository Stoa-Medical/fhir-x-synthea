# Organization (organizations.csv → Organization)

## Semantic Context
Synthea `organizations.csv` describes provider organizations (e.g., hospitals). This mapping produces a FHIR R4 `Organization` resource representing the provider entity. Geolocation is modeled via the standard Address geolocation extension; aggregate metrics are preserved via a custom extension for roundtrip fidelity.

## Field Mappings
```python
# Synthea CSV organizations → FHIR Organization mapping
# (source_field, target_field, semantic_concept, transform, notes)
organizations_mapping = [
    ("organizations.Id", "Organization.id", "Organization Identity", "Direct copy", "Primary key (UUID)"),
    ("organizations.Name", "Organization.name", "Official Name", "Direct copy", "Required"),
    ("organizations.Address", "Organization.address[0].line[0]", "Street Address", "Direct copy", "Required by CSV; optional in FHIR"),
    ("organizations.City", "Organization.address[0].city", "City", "Direct copy", ""),
    ("organizations.State", "Organization.address[0].state", "State/Province", "Direct copy", "Optional"),
    ("organizations.Zip", "Organization.address[0].postalCode", "Postal Code", "Direct copy", "Optional"),
    ("organizations.Lat", "Organization.address[0].extension", "Geolocation", "Create HL7 geolocation extension", "valueDecimal latitude"),
    ("organizations.Lon", "Organization.address[0].extension", "Geolocation", "Create HL7 geolocation extension", "valueDecimal longitude"),
    ("organizations.Phone", "Organization.telecom[]", "Contact Points", "Split into multiple phone entries", "Split on `, ; / |` and trim"),
    ("organizations.Revenue", "Organization.extension[org-stats].extension[revenue]", "Aggregate Metric", "valueDecimal", "Custom extension preserves simulation revenue"),
    ("organizations.Utilization", "Organization.extension[org-stats].extension[utilization]", "Aggregate Metric", "valueInteger", "Number of encounters performed"),
]
```

## Extensions
- Geolocation: `http://hl7.org/fhir/StructureDefinition/geolocation`
- Organization statistics (custom): `http://synthea.mitre.org/fhir/StructureDefinition/organization-stats`
  - Sub-extensions:
    - `revenue` (valueDecimal)
    - `utilization` (valueInteger)

## Implementation Notes
- Forward function: `fhir_x_synthea_csv.to_fhir.organization.map_organization`
- Address array is included only when at least one component is present.
- Multiple phones are split and each becomes a `telecom` entry with `system="phone"`.
- Numeric parsing is best-effort; unparseable values are skipped from the stats extension.
