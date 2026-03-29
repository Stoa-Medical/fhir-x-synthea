"""
Throughline example: Synthea CSV → FHIR Bundle → Synthea CSV roundtrip.

Demonstrates the core mapping workflow using inline data (no external files needed).
This is the foundational pattern that fhir-x-omop will build on.

Run:
    uv run python examples/roundtrip.py
"""

import json
import uuid

from synthea_pydantic import Allergy, Condition, Encounter, Patient

from fhir_x_synthea import extract_tables, patient_bundle

# ── Step 1: Create Synthea data (as if read from CSV) ───────────────────────

PATIENT_ID = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
ENCOUNTER_ID = uuid.UUID("e1e1e1e1-1111-2222-3333-444444444444")
ORG_ID = uuid.UUID("00000000-aaaa-bbbb-cccc-dddddddddddd")
PROVIDER_ID = uuid.UUID("11111111-aaaa-bbbb-cccc-dddddddddddd")
PAYER_ID = uuid.UUID("22222222-aaaa-bbbb-cccc-dddddddddddd")

patient = Patient(
    id=PATIENT_ID,
    birthdate="1965-11-05",
    ssn="999-12-3456",
    drivers="S99912345",
    passport="X12345678X",
    prefix="Mr.",
    first="John",
    last="Smith",
    marital="M",
    race="white",
    ethnicity="nonhispanic",
    gender="M",
    birthplace="Boston MA US",
    address="123 Main St",
    city="Bedford",
    state="Massachusetts",
    county="Middlesex County",
    zip="01730",
    lat="42.4906",
    lon="-71.2760",
    healthcare_expenses="12345.67",
    healthcare_coverage="9876.54",
)

encounter = Encounter(
    id=ENCOUNTER_ID,
    start="2021-06-01T14:30:00Z",
    stop="2021-06-01T15:15:00Z",
    patient=PATIENT_ID,
    organization=ORG_ID,
    provider=PROVIDER_ID,
    payer=PAYER_ID,
    encounterclass="emergency",
    code="50849002",
    description="Emergency room admission (procedure)",
    base_encounter_cost="750.00",
    total_claim_cost="750.00",
    payer_coverage="500.00",
    reasoncode="10509002",
    reasondescription="Acute bronchitis (disorder)",
)

condition = Condition(
    start="2021-06-01",
    patient=PATIENT_ID,
    encounter=ENCOUNTER_ID,
    code="10509002",
    description="Acute bronchitis (disorder)",
)

allergy = Allergy(
    start="2019-05-20",
    patient=PATIENT_ID,
    encounter=ENCOUNTER_ID,
    code="7980",
    system="http://www.nlm.nih.gov/research/umls/rxnorm",
    description="Penicillin V",
    type="allergy",
    category="medication",
    reaction1="247472004",
    description1="Hives",
    severity1="MODERATE",
)

# ── Step 2: Build a FHIR Bundle ────────────────────────────────────────────

bundle = patient_bundle(
    patient,
    encounters=[encounter],
    conditions=[condition],
    allergies=[allergy],
)

print("=== FHIR Bundle ===")
print(f"Type: {bundle.type}")
print(f"Entries: {len(bundle.entry)}")
for entry in bundle.entry:
    r = entry.resource
    print(f"  - {r.__class__.__name__}/{r.id}")

# Show the Patient resource as JSON (pretty-printed)
print("\n=== FHIR Patient (JSON) ===")
fhir_patient = bundle.entry[0].resource
print(json.dumps(json.loads(fhir_patient.model_dump_json()), indent=2))

# ── Step 3: Extract back to Synthea tables ──────────────────────────────────

tables = extract_tables(bundle)

print("\n=== Extracted Synthea Tables ===")
for table_name, rows in tables.items():
    print(f"  {table_name}: {len(rows)} row(s)")

# ── Step 4: Verify the roundtrip ───────────────────────────────────────────

rt_patient = tables["patients"][0]
rt_encounter = tables["encounters"][0]
rt_condition = tables["conditions"][0]
rt_allergy = tables["allergies"][0]

checks = [
    ("Patient.first", rt_patient.first, patient.first),
    ("Patient.last", rt_patient.last, patient.last),
    ("Patient.gender", rt_patient.gender, patient.gender),
    ("Patient.id", str(rt_patient.id), str(patient.id)),
    ("Encounter.code", rt_encounter.code, encounter.code),
    ("Encounter.id", str(rt_encounter.id), str(encounter.id)),
    ("Condition.code", rt_condition.code, condition.code),
    ("Allergy.code", rt_allergy.code, allergy.code),
    ("Allergy.description", rt_allergy.description, allergy.description),
]

print("\n=== Roundtrip Verification ===")
all_passed = True
for label, actual, expected in checks:
    ok = actual == expected
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}: {expected!r} -> {actual!r}")
    if not ok:
        all_passed = False

print(f"\n{'All checks passed!' if all_passed else 'SOME CHECKS FAILED'}")
