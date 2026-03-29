"""Shared test fixtures with inline sample data.

No external downloads needed — these fixtures provide realistic Synthea data
for the core 4 resource types: Patient, Encounter, Condition, Allergy.
"""

from __future__ import annotations

import uuid

import pytest
from synthea_pydantic import Allergy, Condition, Encounter, Patient


# Stable UUIDs for cross-referencing
PATIENT_ID = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
ENCOUNTER_ID_1 = uuid.UUID("e1e1e1e1-1111-2222-3333-444444444444")
ENCOUNTER_ID_2 = uuid.UUID("e2e2e2e2-1111-2222-3333-444444444444")
ORGANIZATION_ID = uuid.UUID("00000000-aaaa-bbbb-cccc-dddddddddddd")
PROVIDER_ID = uuid.UUID("11111111-aaaa-bbbb-cccc-dddddddddddd")
PAYER_ID = uuid.UUID("22222222-aaaa-bbbb-cccc-dddddddddddd")


@pytest.fixture
def sample_patient() -> Patient:
    return Patient(
        id=PATIENT_ID,
        birthdate="1965-11-05",
        deathdate=None,
        ssn="999-12-3456",
        drivers="S99912345",
        passport="X12345678X",
        prefix="Mr.",
        first="John",
        last="Smith",
        suffix=None,
        maiden=None,
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


@pytest.fixture
def sample_encounter_1() -> Encounter:
    return Encounter(
        id=ENCOUNTER_ID_1,
        start="2020-03-15T10:00:00Z",
        stop="2020-03-15T10:45:00Z",
        patient=PATIENT_ID,
        organization=ORGANIZATION_ID,
        provider=PROVIDER_ID,
        payer=PAYER_ID,
        encounterclass="ambulatory",
        code="185349003",
        description="Encounter for check up (procedure)",
        base_encounter_cost="129.16",
        total_claim_cost="129.16",
        payer_coverage="0.00",
        reasoncode=None,
        reasondescription=None,
    )


@pytest.fixture
def sample_encounter_2() -> Encounter:
    return Encounter(
        id=ENCOUNTER_ID_2,
        start="2021-06-01T14:30:00Z",
        stop="2021-06-01T15:15:00Z",
        patient=PATIENT_ID,
        organization=ORGANIZATION_ID,
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


@pytest.fixture
def sample_encounters(sample_encounter_1, sample_encounter_2) -> list[Encounter]:
    return [sample_encounter_1, sample_encounter_2]


@pytest.fixture
def sample_condition() -> Condition:
    return Condition(
        start="2021-06-01",
        stop=None,
        patient=PATIENT_ID,
        encounter=ENCOUNTER_ID_2,
        code="10509002",
        description="Acute bronchitis (disorder)",
    )


@pytest.fixture
def sample_condition_resolved() -> Condition:
    return Condition(
        start="2020-03-15",
        stop="2020-04-15",
        patient=PATIENT_ID,
        encounter=ENCOUNTER_ID_1,
        code="44054006",
        description="Diabetes mellitus type 2 (disorder)",
    )


@pytest.fixture
def sample_allergy() -> Allergy:
    return Allergy(
        start="2019-05-20",
        stop=None,
        patient=PATIENT_ID,
        encounter=ENCOUNTER_ID_1,
        code="7980",
        system="http://www.nlm.nih.gov/research/umls/rxnorm",
        description="Penicillin V",
        type="allergy",
        category="medication",
        reaction1="247472004",
        description1="Hives",
        severity1="MODERATE",
        reaction2=None,
        description2=None,
        severity2=None,
    )
