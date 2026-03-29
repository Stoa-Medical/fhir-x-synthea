# Device

## Semantic Context
Maps FHIR R4 `Device` resources to Synthea `devices.csv`. The CSV captures a patient association window, encounter context, device type (SNOMED), description, and UDI.

## Field Mappings
```python
# FHIR Device → Synthea CSV devices mapping
# (source_field, target_field, semantic_concept, transform, notes)
devices_reverse_mapping = [
    ("Device.extension[device-use-period].valuePeriod.start", "devices.START", "Association start", "Parse FHIR datetime to Synthea datetime", "url=http://synthea.tools/fhir/StructureDefinition/device-use-period; prefer explicit use-period.start; if absent, leave empty"),
    ("Device.extension[device-use-period].valuePeriod.end", "devices.STOP", "Association end", "Parse FHIR datetime to Synthea datetime", "Optional"),
    ("Device.patient.reference", "devices.PATIENT", "Device subject", "Extract Patient/{id} → {id}", "Required"),
    ("Device.extension[resource-encounter].valueReference", "devices.ENCOUNTER", "Encounter", "Extract Encounter/{id} → {id}", "url=http://hl7.org/fhir/StructureDefinition/resource-encounter; optional"),
    ("Device.type (SNOMED)", "devices.CODE", "Device type", "Extract SNOMED coding code", "Fall back to first available coding"),
    ("Device.type.text or coding.display", "devices.DESCRIPTION", "Description", "Copy", "Prefer display, fallback to text"),
    ("Device.udiCarrier[0].deviceIdentifier or carrierHRF", "devices.UDI", "Unique Device Identifier", "Copy", "Prefer deviceIdentifier; fallback to carrierHRF"),
]
```

## Semantic Rules and Constraints
- Derive START/STOP only from the explicit period extension defined by this toolkit; absence yields empty values.
- SNOMED CT preferred for `CODE`.
- If both `deviceIdentifier` and `carrierHRF` exist, use `deviceIdentifier`.

## Implementation Notes
- Keep output strings; convert None to empty strings for CSV compatibility.
- Do not infer values beyond the available resource content to avoid semantic drift.
