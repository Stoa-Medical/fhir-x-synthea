# Device

## Semantic Context
Maps Synthea `devices.csv` rows (patient-affixed permanent and semi-permanent devices) to the FHIR R4 `Device` resource. Start/Stop represent the association period of the device to a patient. Since FHIR R4 lacks a native association period on `Device`, this mapping uses an extension to capture the period, and another extension to keep the encounter linkage consistent with other mappings.

## Field Mappings
```python
# Synthea CSV devices → FHIR Device mapping
# (source_field, target_field, semantic_concept, transform, notes)
devices_mapping = [
    ("START", "Device.extension[url=http://synthea.tools/fhir/StructureDefinition/device-use-period].valuePeriod.start", "Association start", "Convert to FHIR datetime", "Required in CSV; represents when the device became associated with the patient"),
    ("STOP", "Device.extension[url=http://synthea.tools/fhir/StructureDefinition/device-use-period].valuePeriod.end", "Association end", "Convert to FHIR datetime", "Optional in CSV; indicates removal/disassociation"),
    ("PATIENT", "Device.patient.reference", "Device subject (patient)", "Patient/{id}", "Required foreign key to patient"),
    ("ENCOUNTER", "Device.extension[url=http://hl7.org/fhir/StructureDefinition/resource-encounter].valueReference", "Association encounter", "Encounter/{id}", "Mirrors encounter linkage pattern used elsewhere in this repo"),
    ("CODE", "Device.type.coding[0].code", "Device type (SNOMED CT)", "Copy", "SNOMED-CT code; Device.type.coding[0].system = http://snomed.info/sct"),
    ("DESCRIPTION", "Device.type.coding[0].display and Device.type.text", "Device description", "Copy", "Provide both display and human-readable text"),
    ("UDI", "Device.udiCarrier[0].deviceIdentifier and Device.udiCarrier[0].carrierHRF", "Unique Device Identifier", "Copy", "UDI stored in deviceIdentifier; duplicated to carrierHRF for human-readable UDI"),
]
```

## Semantic Rules and Constraints
- **Device.status**: Derived from association period. `active` when no STOP provided; `inactive` when STOP is present.
- **Coding system**: SNOMED CT for `Device.type`.
- **Extensions**:
  - Use period captured via a custom extension at `http://synthea.tools/fhir/StructureDefinition/device-use-period` with `valuePeriod`.
  - Encounter linkage via `http://hl7.org/fhir/StructureDefinition/resource-encounter` with `valueReference`.

## Implementation Notes
- Ensure datetime values are formatted as FHIR datetimes.
- Filter out empty/None fields to keep the resource compact.
- Deterministic `Device.id` may be constructed from `PATIENT`, `START`, and `CODE` for stable roundtrips within this toolkit.
