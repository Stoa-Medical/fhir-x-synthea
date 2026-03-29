### FHIR → CSV mapping: Claim to claims.csv

This spec defines how a FHIR R4 `Claim` resource is flattened into a `claims.csv` row. Fields related to adjudication or balances are not available on Claim and remain blank unless implementers derive them from `ClaimResponse`.

## Field Mappings
```python
# FHIR Claim → Synthea CSV claims mapping
# (source_field, target_field, semantic_concept, transform, notes)
claims_reverse_mapping = [
    ("Claim.id", "claims.Id", "Claim Identity", "Direct copy", "Business identifier may be ignored if present"),
    ("Claim.patient.reference", "claims.Patient ID", "Patient Reference", "Extract reference id", ""),
    ("Claim.provider.reference", "claims.Provider ID", "Provider Reference", "Extract reference id", ""),
    ("Claim.insurance[0].coverage.reference", "claims.Primary Patient Insurance ID", "Primary Insurance", "Extract reference id", "sequence 1 or focal=true"),
    ("Claim.insurance[1].coverage.reference", "claims.Secondary Patient Insurance ID", "Secondary Insurance", "Extract reference id", "sequence 2 or focal=false"),
    ("Claim.extension[department-id].valueString", "claims.Department ID", "Department ID", "Extract from extension", "url=http://synthea.tools/StructureDefinition/department-id"),
    ("Claim.extension[patient-department-id].valueString", "claims.Patient Department ID", "Patient Department ID", "Extract from extension", "url=http://synthea.tools/StructureDefinition/patient-department-id"),
    ("Claim.diagnosis[].diagnosisCodeableConcept", "claims.Diagnosis1..Diagnosis8", "Diagnosis Codes", "Take up to 8 SNOMED CT codes in sequence order", "Fallback to text if no coding"),
    ("Claim.referral", "claims.Referring Provider ID", "Referring Provider", "Leave blank unless resolvable ServiceRequest", "Not available from Claim alone"),
    ("Claim.item[0].encounter.reference", "claims.Appointment ID", "Encounter Reference", "Extract reference id if present", "Otherwise blank"),
    ("Claim.event where type.code=onset", "claims.Current Illness Date", "Illness Onset Event", "Extract whenDateTime", "system=http://synthea.tools/CodeSystem/claim-event"),
    ("Claim.billablePeriod.start", "claims.Service Date", "Service Date", "Direct copy", "Prefer start; if only end present, use end"),
    ("Claim.careTeam where role.text=supervising", "claims.Supervising Provider ID", "Supervising Provider", "Extract provider reference id", ""),
    (None, "claims.Status1/Status2/StatusP", "Adjudication Statuses", "Leave blank", "Not on Claim; may be populated by ClaimResponse processing"),
    (None, "claims.Outstanding1/2/P", "Outstanding Amounts", "Leave blank", "Not on Claim"),
    ("Claim.event where type.code=bill-primary/bill-secondary/bill-patient", "claims.LastBilledDate1/2/P", "Billing Events", "Extract whenDateTime for respective codes", ""),
    ("Claim.type/subType", "claims.HealthcareClaimTypeID1/2", "Claim Type", "professional→1, institutional→2", "Unknown/other→leave blank"),
]
```

Formatting
- Dates are rendered as `YYYY-MM-DD` (or `YYYY-MM-DD HH:MM:SS` if time is present); helper functions normalize values.

Limitations
- Values that originate from adjudication/payment (statuses, outstanding) require `ClaimResponse` and are not populated here.
