# Medication (FHIR → medications.csv)

## Primary Source Resource
- MedicationRequest

## Field Mappings
```python
# FHIR MedicationRequest → Synthea CSV medications mapping
# (source_field, target_field, semantic_concept, transform, notes)
medications_reverse_mapping = [
    ("MedicationRequest.authoredOn or occurrencePeriod.start", "medications.Start", "Start Date/Time", "Parse FHIR datetime → Synthea format", "Prefer authoredOn"),
    ("MedicationRequest.occurrencePeriod.end", "medications.Stop", "End Date/Time", "Parse FHIR datetime", "Optional"),
    ("MedicationRequest.subject", "medications.Patient", "Patient Reference", "Extract reference id", "Patient/{id}"),
    ("MedicationRequest.encounter", "medications.Encounter", "Encounter Reference", "Extract reference id", "Encounter/{id}"),
    ("MedicationRequest.insurance[0]", "medications.Payer", "Payer Reference", "Extract reference id", "Coverage/{id} or Organization/{id}"),
    ("MedicationRequest.medicationCodeableConcept (RxNorm)", "medications.Code", "RxNorm Code", "Extract coding by RxNorm system", "Fallback to first coding"),
    ("MedicationRequest.medicationCodeableConcept", "medications.Description", "Description", "Display or text fallback", ""),
    ("MedicationRequest.dispenseRequest.numberOfRepeatsAllowed", "medications.Dispenses", "Dispenses", "Stringify", ""),
    ("MedicationRequest.reasonCode[0]", "medications.ReasonCode", "Reason Code", "SNOMED coding code", "Fallback to first coding"),
    ("MedicationRequest.reasonCode[0]", "medications.ReasonDescription", "Reason Description", "SNOMED display or text", ""),
    ("ext(baseCost)", "medications.Base_Cost", "Base Cost", "Extract extension valueDecimal", "URL: .../medication-baseCost"),
    ("ext(payerCoverage)", "medications.Payer_Coverage", "Payer Coverage", "Extract extension valueDecimal", "URL: .../medication-payerCoverage"),
    ("ext(totalCost)", "medications.TotalCost", "Total Cost", "Extract extension valueDecimal", "URL: .../medication-totalCost"),
]
```

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_synthea_csv.medication.map_fhir_medication_request_to_csv`
- Only `MedicationRequest` is supported for now. `MedicationDispense`/`MedicationAdministration` can be added later.
