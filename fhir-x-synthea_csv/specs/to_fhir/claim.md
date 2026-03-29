### Synthea `claims.csv` → FHIR R5 `Claim`

- **Source**: Synthea `claims.csv`
- **Target**: FHIR R5 `Claim` (Financial → Billing; Maturity Level: 2)
- **Scope**: Header-level mapping only (no line-item breakdown). Where FHIR lacks a direct header field, `Claim.supportingInfo` is used. Some operational states are better modeled as `ClaimResponse`/`ExplanationOfBenefit` but are captured here for completeness.

#### Assumptions
- UUIDs reference existing resources using `Reference(ResourceType/<UUID>)`.
- SNOMED CT codes in Diagnosis columns are used as-is in `CodeableConcept.coding` with `system = "http://snomed.info/sct"`.
- Money values without currency are represented as `Money` with configurable default currency (assume `USD` unless otherwise specified).
- Department identifiers map to `Location` resources; if only numeric placeholders exist, they are used as `Location/<id>`.
- Provider identifiers map to `Practitioner` unless your dataset models providers as `Organization`.
- For Primary vs Secondary insurance, `Claim.insurance[0]` is focal (primary), `Claim.insurance[1]` is non-focal (secondary).

#### Field mapping

| CSV Column | Description | Type | Required | FHIR Target | Notes |
|---|---|---|---|---|---|
| Id | Primary key, unique identifier of the claim | UUID | Yes | `Claim.id` | Keep original UUID. |
| Patient ID | FK to Patient | UUID | Yes | `Claim.patient = Reference(Patient/<uuid>)` | |
| Provider ID | FK to Provider | UUID | Yes | `Claim.provider = Reference(Practitioner/<uuid>)` | Use `Organization` if that’s how providers are modeled. |
| Primary Patient Insurance ID | FK to primary Payer | UUID | No | `Claim.insurance[0].focal = true`; `Claim.insurance[0].coverage = Reference(Coverage/<uuid>)` | Intended recipient may also be duplicated to `Claim.insurer` when sending to primary. |
| Secondary Patient Insurance ID | FK to secondary Payer | UUID | No | `Claim.insurance[1].focal = false`; `Claim.insurance[1].coverage = Reference(Coverage/<uuid>)` | |
| Department ID | Department placeholder | Numeric | Yes | `Claim.facility = Reference(Location/<id>)` | If a richer department model exists, map accordingly. |
| Patient Department ID | Patient department placeholder | Numeric | Yes | `Claim.supportingInfo` (category: `patient-department`, valueReference: `Location/<id>`) | Custom category code; see Supporting Info section. |
| Diagnosis1 … Diagnosis8 | SNOMED-CT diagnosis codes related to the claim | String | No | `Claim.diagnosis[n]` | For each non-empty column in order: `sequence = n`, `diagnosisCodeableConcept.coding[0] = {system: snomed, code: <value>}`. |
| Referring Provider ID | FK to referring Provider | UUID | No | `Claim.careTeam` entry | `Claim.careTeam[].provider = Reference(Practitioner/<uuid>)`, `role = referring`. |
| Appointment ID | FK to Encounter | UUID | No | `Claim.encounter[0] = Reference(Encounter/<uuid>)` | |
| Current Illness Date | Date symptoms began | DateTime (UTC) | Yes | `Claim.supportingInfo` | Category `illness-onset`, `valueDateTime = <date>`. |
| Service Date | Date of services on the claim | DateTime (UTC) | Yes | `Claim.billablePeriod.start = <date>` | If only a single date is known, set `start` and optionally `end = start`. |
| Supervising Provider ID | FK to supervising Provider | UUID | No | `Claim.careTeam` entry | `provider = Reference(Practitioner/<uuid>)`, `role = supervising`. |
| Status1 | Status from Primary Insurance | String (`BILLED`\|`CLOSED`) | No | `Claim.supportingInfo` | Category `primary-billing-status`, `valueCodeableConcept` with code `BILLED`/`CLOSED`. Consider modeling as `ClaimResponse` in production. |
| Status2 | Status from Secondary Insurance | String (`BILLED`\|`CLOSED`) | No | `Claim.supportingInfo` | Category `secondary-billing-status`, `valueCodeableConcept`. |
| StatusP | Status from Patient | String (`BILLED`\|`CLOSED`) | No | `Claim.supportingInfo` | Category `patient-billing-status`, `valueCodeableConcept`. |
| Outstanding1 | Amount owed by Primary Insurance | Numeric | No | `Claim.supportingInfo` | Category `primary-outstanding`, `valueMoney = {value, currency}`. |
| Outstanding2 | Amount owed by Secondary Insurance | Numeric | No | `Claim.supportingInfo` | Category `secondary-outstanding`, `valueMoney`. |
| OutstandingP | Amount owed by Patient | Numeric | No | `Claim.supportingInfo` | Category `patient-outstanding`, `valueMoney`. |
| LastBilledDate1 | Date sent to Primary Insurance | DateTime (UTC) | No | `Claim.supportingInfo` | Category `primary-last-billed`, `valueDateTime`. |
| LastBilledDate2 | Date sent to Secondary Insurance | DateTime (UTC) | No | `Claim.supportingInfo` | Category `secondary-last-billed`, `valueDateTime`. |
| LastBilledDateP | Date sent to Patient | DateTime (UTC) | No | `Claim.supportingInfo` | Category `patient-last-billed`, `valueDateTime`. |
| HealthcareClaimTypeID1 | Type: 1=professional, 2=institutional | Numeric | No | `Claim.type` | Map: `1 → professional`, `2 → institutional`. |
| HealthcareClaimTypeID2 | Type: 1=professional, 2=institutional | Numeric | No | `Claim.supportingInfo` | Category `secondary-claim-type`, `valueCodeableConcept` mirroring HealthcareClaimTypeID1 mapping. |

#### Supporting Info categories
When using `Claim.supportingInfo`, use consistent codes in `CodeableConcept`. Example system: `http://example.org/fhir/CodeSystem/claim-supporting-info-category`.

Recommended category codes used above:
- `patient-department`
- `illness-onset`
- `primary-billing-status`, `secondary-billing-status`, `patient-billing-status`
- `primary-outstanding`, `secondary-outstanding`, `patient-outstanding`
- `primary-last-billed`, `secondary-last-billed`, `patient-last-billed`
- `secondary-claim-type`

#### Claim type mapping
- `1` → `Claim.type = { coding: [{ system: "http://terminology.hl7.org/CodeSystem/claim-type", code: "professional" }] }`
- `2` → `Claim.type = { coding: [{ system: "http://terminology.hl7.org/CodeSystem/claim-type", code: "institutional" }] }`

#### Notes and alternatives
- Insurer-specific statuses and outstanding balances are typically represented in `ClaimResponse`/`ExplanationOfBenefit`. This spec captures them on `Claim.supportingInfo` to preserve CSV data without introducing additional resources.
- If you maintain `Coverage` resources, ensure `Coverage.payor` references the correct `Organization` for the Primary/Secondary Payer.
- If your implementation uses R4 instead of R5, the above elements are largely compatible; `supportingInfo`, `diagnosis`, `insurance`, `careTeam`, `billablePeriod`, and `encounter` exist in R4 with equivalent semantics.