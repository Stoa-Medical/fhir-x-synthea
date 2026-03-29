# Medication (medications.csv → FHIR)

## Semantic Context
The `medications.csv` table records prescribed medications per patient. This mapping focuses on FHIR R4 `MedicationRequest` as the primary representation, embedding the RxNorm code via `medicationCodeableConcept`. Optional financial details are captured with extensions. References are created to `Patient`, `Encounter`, and `Coverage` (via `MedicationRequest.insurance`) when available.

## Field Mappings
```python
# Synthea CSV medications → FHIR MedicationRequest mapping
# (source_field, target_field, semantic_concept, transform, notes)
medications_mapping = [
    ("medications.Start", "MedicationRequest.authoredOn", "Authored Date/Time", "ISO 8601", "When request was made"),
    ("medications.Start", "MedicationRequest.occurrencePeriod.start", "Intended start", "ISO 8601", "Start of intended use"),
    ("medications.Stop", "MedicationRequest.occurrencePeriod.end", "Intended end", "ISO 8601", "Optional"),
    ("medications.Patient", "MedicationRequest.subject", "Subject", "Reference(\"Patient/{id}\")", "Required"),
    ("medications.Encounter", "MedicationRequest.encounter", "Encounter", "Reference(\"Encounter/{id}\")", "Required"),
    ("medications.Payer", "MedicationRequest.insurance[0]", "Payer", "Reference(\"Coverage/{id}\")", "Uses Coverage reference"),
    ("medications.Code", "MedicationRequest.medicationCodeableConcept.coding[0].code", "RxNorm Code", "Direct", "RxNorm"),
    ("medications.Description", "MedicationRequest.medicationCodeableConcept.coding[0].display", "Display", "Direct", "Human-readable"),
    ("medications.Code", "MedicationRequest.medicationCodeableConcept.coding[0].system", "Code System", "http://www.nlm.nih.gov/research/umls/rxnorm", "RxNorm"),
    ("medications.Description", "MedicationRequest.medicationCodeableConcept.text", "Text", "Direct", "Fallback text"),
    ("medications.Dispenses", "MedicationRequest.dispenseRequest.numberOfRepeatsAllowed", "Repeats", "to integer", "Interpreted as refills allowed"),
    ("medications.ReasonCode", "MedicationRequest.reasonCode[0].coding[0].code", "Reason Code", "Direct", "SNOMED CT"),
    ("medications.ReasonDescription", "MedicationRequest.reasonCode[0].coding[0].display", "Reason Text", "Direct", "Description"),
    ("medications.Base_Cost", "MedicationRequest.extension[baseCost]", "Base Cost", "Decimal → extension", "http://synthea.org/fhir/StructureDefinition/medication-baseCost"),
    ("medications.Payer_Coverage", "MedicationRequest.extension[payerCoverage]", "Covered Amount", "Decimal → extension", "http://synthea.org/fhir/StructureDefinition/medication-payerCoverage"),
    ("medications.TotalCost", "MedicationRequest.extension[totalCost]", "Total Cost", "Decimal → extension", "http://synthea.org/fhir/StructureDefinition/medication-totalCost"),
    (None, "MedicationRequest.status", "Status", "active if no Stop else completed", "Heuristic"),
    (None, "MedicationRequest.intent", "Intent", "order", "Prescription"),
]
```

## Semantic Rules and Constraints
- RxNorm is used for medication identification (code system: `http://www.nlm.nih.gov/research/umls/rxnorm`).
- `insurance` references `Coverage/{Payer}`; linking to `Organization` or full financial resources may be added separately.
- Financial columns are modeled as extensions if no `Claim`/`EOB` context is generated.
- `Dispenses` is mapped to `numberOfRepeatsAllowed`; semantics may differ across implementations.

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_fhir.medication.map_medication`
- Returns a FHIR `MedicationRequest` with `medicationCodeableConcept` (no separate `Medication` resource created).
