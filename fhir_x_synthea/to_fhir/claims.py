"""Synthea Claim → FHIR R4 Claim"""

from fhir.resources.claim import Claim
from synthea_pydantic import Claim as SyntheaClaim

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import format_datetime, identifier, ref


def _build_diagnoses(d: dict):
    """Build diagnosis list from diagnosis1-8 fields."""
    diagnoses = []
    for i in range(1, 9):
        diag_code = grab(d, f"diagnosis{i}")
        if diag_code:
            diagnoses.append(
                {
                    "sequence": i,
                    "diagnosisCodeableConcept": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": str(diag_code)}
                        ]
                    },
                }
            )
    return diagnoses if diagnoses else None


def _build_status_notes(d: dict):
    """Build notes from status fields."""
    notes = []
    for key in ["status1", "status2", "statusp"]:
        value = grab(d, key)
        if value:
            notes.append({"text": str(value)})
    for key in ["outstanding1", "outstanding2", "outstandingp"]:
        value = grab(d, key)
        if value:
            notes.append({"text": f"Outstanding: {value}"})
    return notes if notes else None


def _build_billing_event(date_value: str | None, event_code: str):
    """Build a single billing event."""
    if not date_value:
        return None
    iso_date = format_datetime(date_value)
    if not iso_date:
        return None
    return {
        "type": {
            "coding": [
                {
                    "system": "http://synthea.tools/CodeSystem/claim-event",
                    "code": event_code,
                }
            ]
        },
        "whenDateTime": iso_date,
    }


def _build_events(d: dict):
    """Build events list from billing dates and illness onset."""
    events = []

    billing_dates = [
        ("lastbilleddate1", "bill-primary"),
        ("lastbilleddate2", "bill-secondary"),
        ("lastbilleddatep", "bill-patient"),
    ]
    for date_key, event_code in billing_dates:
        event = _build_billing_event(grab(d, date_key), event_code)
        if event:
            events.append(event)

    # Illness onset event
    onset_event = _build_billing_event(grab(d, "currentillnessdate"), "onset")
    if onset_event:
        events.append(onset_event)

    return events if events else None


def _build_insurance(d: dict):
    """Build insurance list."""
    insurance = []
    primary_id = grab(d, "primarypatientinsuranceid")
    if primary_id:
        primary_ref = ref("Coverage", primary_id)
        if primary_ref:
            insurance.append({"sequence": 1, "focal": True, "coverage": primary_ref})

    secondary_id = grab(d, "secondarypatientinsuranceid")
    if secondary_id:
        secondary_ref = ref("Coverage", secondary_id)
        if secondary_ref:
            insurance.append({"sequence": 2, "focal": False, "coverage": secondary_ref})

    return insurance if insurance else None


def _department_extension(department_id: str | None, ext_name: str):
    """Build department ID extension."""
    if not department_id:
        return None
    return {
        "url": f"http://synthea.tools/StructureDefinition/{ext_name}",
        "valueString": department_id,
    }


def _build_extensions(d: dict):
    """Build extensions list."""
    extensions = [
        e
        for e in [
            _department_extension(grab(d, "departmentid"), "department-id"),
            _department_extension(
                grab(d, "patientdepartmentid"), "patient-department-id"
            ),
        ]
        if e
    ]
    return extensions if extensions else None


def _build_item(appointment_id: str | None):
    """Build item with encounter reference."""
    if not appointment_id:
        return None
    encounter_ref = ref("Encounter", appointment_id)
    if not encounter_ref:
        return None
    return [
        {
            "sequence": 1,
            "productOrService": {"text": "Encounter"},
            "encounter": [encounter_ref],
        }
    ]


def _build_care_team(supervising_provider_id: str | None):
    """Build careTeam."""
    if not supervising_provider_id:
        return None
    provider_ref = ref("Practitioner", supervising_provider_id)
    if not provider_ref:
        return None
    return [
        {
            "sequence": 1,
            "provider": provider_ref,
            "role": {"text": "supervising"},
        }
    ]


def _build_claim_type(type_id1: str | None):
    """Build claim type CodeableConcept."""
    if type_id1 == "1":
        return {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                    "code": "professional",
                    "display": "Professional",
                }
            ]
        }
    elif type_id1 == "2":
        return {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                    "code": "institutional",
                    "display": "Institutional",
                }
            ]
        }
    # Default type required by FHIR
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                "code": "professional",
            }
        ]
    }


def _build_sub_type(type_id2: str | None):
    """Build claim subType CodeableConcept."""
    if not type_id2:
        return None
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                "code": type_id2,
            }
        ]
    }


def _build_billable_period(service_date: str | None):
    """Build billablePeriod."""
    if not service_date:
        return None
    iso_date = format_datetime(service_date)
    if not iso_date:
        return None
    return {"start": iso_date, "end": iso_date}


@mapper
def _to_fhir_claim(d: dict):
    """Core mapping from dict to FHIR Claim structure."""
    claim_id = grab(d, "id")

    return {
        "resourceType": "Claim",
        "id": claim_id,
        "status": "active",
        "use": "claim",
        "identifier": [identifier(system="urn:synthea:claim", value=claim_id)]
        if claim_id
        else None,
        "patient": ref("Patient", grab(d, "patientid")),
        "provider": ref("Practitioner", grab(d, "providerid")),
        "insurance": _build_insurance(d),
        "extension": _build_extensions(d),
        "diagnosis": _build_diagnoses(d),
        "item": _build_item(grab(d, "appointmentid")),
        "billablePeriod": _build_billable_period(grab(d, "servicedate")),
        "careTeam": _build_care_team(grab(d, "supervisingproviderid")),
        "type": _build_claim_type(grab(d, "healthcareclaimtypeid1")),
        "subType": _build_sub_type(grab(d, "healthcareclaimtypeid2")),
        "event": _build_events(d),
        "note": _build_status_notes(d),
        "priority": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/processpriority",
                    "code": "normal",
                }
            ]
        },
    }


def convert(src: SyntheaClaim) -> Claim:
    """Convert Synthea Claim to FHIR R4 Claim.

    Args:
        src: Synthea Claim model

    Returns:
        FHIR R4 Claim resource
    """
    return Claim(**_to_fhir_claim(to_dict(src)))
