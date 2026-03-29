### CSV → FHIR mapping: claims.csv to Claim (and related)

This spec defines how `claims.csv` rows map into elements of the FHIR R4 `Claim` resource. Some fields reflect claim lifecycle and adjudication semantics which, in FHIR, belong to `ClaimResponse`. Where appropriate, we note those relationships.

Assumptions
- Each `claims.csv` row represents a single insurance claim submitted by a provider on behalf of a patient.
- The mapping targets FHIR R4. Elements introduced in R5 (e.g., `Claim.encounter`) are represented using R4-compatible structures (e.g., `Claim.item.encounter`).
- Codes are preserved in `code` and, when known, expressed with standard systems.

## Field Mappings
```python
# Synthea CSV claims → FHIR Claim mapping
# (source_field, target_field, semantic_concept, transform, notes)
claims_mapping = [
    ("Id", "Claim.id", "Claim Identity", "Direct copy", "Also include business identifier in Claim.identifier (system urn:synthea:claim)"),
    ("Patient ID", "Claim.patient", "Patient Reference", "Patient/{Patient ID}", ""),
    ("Provider ID", "Claim.provider", "Provider Reference", "Practitioner/{Provider ID}", ""),
    ("Primary Patient Insurance ID", "Claim.insurance[0]", "Primary Insurance", "Coverage/{Primary Patient Insurance ID}", "sequence=1, focal=true"),
    ("Secondary Patient Insurance ID", "Claim.insurance[1]", "Secondary Insurance", "Coverage/{Secondary Patient Insurance ID}", "sequence=2, focal=false"),
    ("Department ID", "Claim.extension[url=http://synthea.tools/StructureDefinition/department-id].valueString", "Department ID", "Direct copy", "No direct standard element; use extension"),
    ("Patient Department ID", "Claim.extension[url=http://synthea.tools/StructureDefinition/patient-department-id].valueString", "Patient Department ID", "Direct copy", "Extension with valueString"),
    ("Diagnosis1..Diagnosis8", "Claim.diagnosis[]", "Diagnosis Codes", "SNOMED CT codes with sequence 1-8", "diagnosis.diagnosisCodeableConcept.coding[0].system=http://snomed.info/sct"),
    ("Referring Provider ID", "Claim.referral", "Referring Provider", "ServiceRequest/{id}", "Omit by default; only if ServiceRequest available"),
    ("Appointment ID", "Claim.item[0].encounter[0]", "Encounter Reference", "Encounter/{Appointment ID}", "R4 representation"),
    ("Current Illness Date", "Claim.event[]", "Illness Onset Event", "event.type code=onset, event.whenDateTime=date", "Local system http://synthea.tools/CodeSystem/claim-event"),
    ("Service Date", "Claim.billablePeriod", "Service Period", "start=end=service date", ""),
    ("Supervising Provider ID", "Claim.careTeam[]", "Supervising Provider", "provider=Practitioner/{Supervising Provider ID}", "sequence=1, role.text=supervising"),
    ("Status1/Status2/StatusP", "Claim.note[].text", "Adjudication Statuses", "Preserve as note for traceability", "Do not map to Claim.status; belongs in ClaimResponse"),
    ("Outstanding1/2/P", "Claim.note[].text", "Outstanding Amounts", "Preserve as note for traceability", "Adjudication semantics belong in ClaimResponse"),
    ("LastBilledDate1/2/P", "Claim.event[]", "Billing Events", "event.type codes bill-primary/bill-secondary/bill-patient", "event.whenDateTime set to respective date"),
    ("HealthcareClaimTypeID1/2", "Claim.type and Claim.subType", "Claim Type", "1→professional, 2→institutional", "system=http://terminology.hl7.org/CodeSystem/claim-type"),
]
```

Data typing and formatting
- Dates are emitted in ISO 8601 (YYYY-MM-DD or full datetime). This library normalizes via helpers.
- Amounts are not on Claim in this CSV; any amounts present (Outstanding*) are not mapped to Claim elements.

Notes
- This spec intentionally scopes to a self-contained Claim resource using R4 elements. Any adjudication, amounts due, or final outcome should be produced as `ClaimResponse` using other CSV sources (e.g., `claims_transactions.csv`).
