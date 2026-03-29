# Provider (providers.csv → Practitioner, PractitionerRole)

## Semantic Context
Synthea `providers.csv` contains clinicians providing care. This mapping produces:
- Practitioner: the individual clinician (identity, name, gender, address)
- PractitionerRole: the clinician’s role within an organization (organization link, specialty)

## Field Mappings
```python
# Synthea CSV providers → FHIR Practitioner and PractitionerRole mapping
# (source_field, target_field, semantic_concept, transform, notes)
providers_mapping = [
    ("providers.Id", "Practitioner.id", "Practitioner Identity", "Direct copy", "Primary key (UUID)"),
    ("providers.Name", "Practitioner.name[0]", "Human Name", "Split into given/family", "use=official; first token→given, last token→family"),
    ("providers.Gender", "Practitioner.gender", "Administrative Gender", "Map M→male, F→female", "Use gender lexicon"),
    ("providers.Address", "Practitioner.address[0].line[0]", "Street Address", "Direct copy", "Primary address line"),
    ("providers.City", "Practitioner.address[0].city", "City", "Direct copy", "City name"),
    ("providers.State", "Practitioner.address[0].state", "State", "Direct copy", "State/province"),
    ("providers.Zip", "Practitioner.address[0].postalCode", "Postal Code", "Direct copy", "ZIP/postal code"),
    ("providers.Lat", "Practitioner.address[0].extension", "Geolocation", "Create geolocation extension", "Latitude coordinate"),
    ("providers.Lon", "Practitioner.address[0].extension", "Geolocation", "Create geolocation extension", "Longitude coordinate"),
    ("providers.Id", "PractitionerRole.practitioner", "Practitioner Reference", "Create Reference(\"Practitioner/{Id}\")", "Links role to practitioner"),
    ("providers.Organization", "PractitionerRole.organization", "Organization Reference", "Create Reference(\"Organization/{Organization}\")", "Links role to org"),
    ("providers.Speciality", "PractitionerRole.code[0]", "Role/Specialty", "Text to CodeableConcept", "Put string in text (and display if coding used)"),
    ("providers.Encounters", "PractitionerRole.extension", "Aggregate Stats", "Custom extension", "url=http://example.org/fhir/StructureDefinition/provider-stats, subext encounters as valueInteger"),
    ("providers.Procedures", "PractitionerRole.extension", "Aggregate Stats", "Custom extension", "Same extension, subext procedures as valueInteger"),
    (None, "PractitionerRole.id", "Resource ID", "Generate from Id+Organization", "prr-{Id}-{Organization} (deterministic)"),
]
```

## Semantic Rules and Constraints
- Name is split heuristically: first token as given, last token as family; middle tokens ignored.
- Geolocation uses HL7 `geolocation` extension on Address.
- Aggregate counts (Encounters, Procedures) are not part of core Practitioner/Role; preserved via a custom extension for roundtrip fidelity.
- Specialty is represented in `PractitionerRole.code[ ]` as a CodeableConcept with `text` when no code system is provided.

## Implementation Notes
- Forward functions: `map_practitioner`, `map_practitioner_role` in `fhir_x_synthea_csv.to_fhir.provider`.
- Reverse function: `map_fhir_provider_to_csv` in `fhir_x_synthea_csv.to_synthea_csv.provider`.
- Reuse existing gender lexicon and geolocation extension helpers (same as Patient mapping).
