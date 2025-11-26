"""Synthea Claim → FHIR R4 Claim"""

from typing import Any

from fhir.resources.claim import Claim
from synthea_pydantic import Claim as SyntheaClaim

from ..fhir_lib import create_reference, format_datetime
from ..utils import to_str


def convert(src: SyntheaClaim) -> Claim:
    """Convert Synthea Claim to FHIR R4 Claim.

    Args:
        src: Synthea Claim model

    Returns:
        FHIR R4 Claim resource
    """
    d = src.model_dump()

    # Extract and process fields (synthea_pydantic uses lowercase keys)
    claim_id = to_str(d.get("id"))
    patient_id = to_str(d.get("patientid"))
    provider_id = to_str(d.get("providerid"))
    primary_insurance_id = to_str(d.get("primarypatientinsuranceid"))
    secondary_insurance_id = to_str(d.get("secondarypatientinsuranceid"))
    department_id = to_str(d.get("departmentid"))
    patient_department_id = to_str(d.get("patientdepartmentid"))
    appointment_id = to_str(d.get("appointmentid"))
    current_illness_date = to_str(d.get("currentillnessdate"))
    service_date = to_str(d.get("servicedate"))
    supervising_provider_id = to_str(d.get("supervisingproviderid"))
    healthcare_claim_type_id1 = to_str(d.get("healthcareclaimtypeid1"))
    healthcare_claim_type_id2 = to_str(d.get("healthcareclaimtypeid2"))

    # Extract diagnosis codes (diagnosis1-8)
    diagnoses = []
    for i in range(1, 9):
        diag_code = to_str(d.get(f"diagnosis{i}"))
        if diag_code:
            diagnoses.append(
                {
                    "sequence": i,
                    "diagnosisCodeableConcept": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": diag_code}
                        ]
                    },
                }
            )

    # Extract status notes (status1, status2, statusp)
    status_notes = []
    for status_key in ["status1", "status2", "statusp"]:
        status_value = to_str(d.get(status_key))
        if status_value:
            status_notes.append({"text": status_value})

    # Extract outstanding amounts (outstanding1, outstanding2, outstandingp)
    outstanding_notes = []
    for outstanding_key in ["outstanding1", "outstanding2", "outstandingp"]:
        outstanding_value = to_str(d.get(outstanding_key))
        if outstanding_value:
            outstanding_notes.append({"text": f"Outstanding: {outstanding_value}"})

    # Extract billing events (lastbilleddate1, lastbilleddate2, lastbilleddatep)
    events = []
    billing_dates = [
        ("lastbilleddate1", "bill-primary"),
        ("lastbilleddate2", "bill-secondary"),
        ("lastbilleddatep", "bill-patient"),
    ]
    for date_key, event_code in billing_dates:
        date_value = to_str(d.get(date_key))
        if date_value:
            iso_date = format_datetime(date_value)
            if iso_date:
                events.append(
                    {
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
                )

    # Illness onset event
    if current_illness_date:
        iso_date = format_datetime(current_illness_date)
        if iso_date:
            events.append(
                {
                    "type": {
                        "coding": [
                            {
                                "system": "http://synthea.tools/CodeSystem/claim-event",
                                "code": "onset",
                            }
                        ]
                    },
                    "whenDateTime": iso_date,
                }
            )

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Claim",
        "status": "active",
        "use": "claim",
    }

    if claim_id:
        resource["id"] = claim_id
        resource["identifier"] = [{"system": "urn:synthea:claim", "value": claim_id}]

    # Set patient reference
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["patient"] = patient_ref

    # Set provider reference
    if provider_id:
        provider_ref = create_reference("Practitioner", provider_id)
        if provider_ref:
            resource["provider"] = provider_ref

    # Set insurance
    insurance = []
    if primary_insurance_id:
        primary_ref = create_reference("Coverage", primary_insurance_id)
        if primary_ref:
            insurance.append({"sequence": 1, "focal": True, "coverage": primary_ref})

    if secondary_insurance_id:
        secondary_ref = create_reference("Coverage", secondary_insurance_id)
        if secondary_ref:
            insurance.append({"sequence": 2, "focal": False, "coverage": secondary_ref})

    if insurance:
        resource["insurance"] = insurance

    # Set extensions (department IDs)
    extensions = []
    if department_id:
        extensions.append(
            {
                "url": "http://synthea.tools/StructureDefinition/department-id",
                "valueString": department_id,
            }
        )

    if patient_department_id:
        extensions.append(
            {
                "url": "http://synthea.tools/StructureDefinition/patient-department-id",
                "valueString": patient_department_id,
            }
        )

    if extensions:
        resource["extension"] = extensions

    # Set diagnosis
    if diagnoses:
        resource["diagnosis"] = diagnoses

    # Set item with encounter (if present)
    if appointment_id:
        encounter_ref = create_reference("Encounter", appointment_id)
        if encounter_ref:
            resource["item"] = [
                {
                    "sequence": 1,
                    "productOrService": {"text": "Encounter"},
                    "encounter": [encounter_ref],
                }
            ]

    # Set billablePeriod
    if service_date:
        iso_date = format_datetime(service_date)
        if iso_date:
            resource["billablePeriod"] = {"start": iso_date, "end": iso_date}

    # Set careTeam (supervising provider)
    if supervising_provider_id:
        provider_ref = create_reference("Practitioner", supervising_provider_id)
        if provider_ref:
            resource["careTeam"] = [
                {
                    "sequence": 1,
                    "provider": provider_ref,
                    "role": {"text": "supervising"},
                }
            ]

    # Set type and subType
    type_codings = []
    if healthcare_claim_type_id1 == "1":
        type_codings.append(
            {
                "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                "code": "professional",
                "display": "Professional",
            }
        )
    elif healthcare_claim_type_id1 == "2":
        type_codings.append(
            {
                "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                "code": "institutional",
                "display": "Institutional",
            }
        )

    if type_codings:
        resource["type"] = {"coding": type_codings}
    else:
        # Default type required by FHIR
        resource["type"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                    "code": "professional",
                }
            ]
        }

    if healthcare_claim_type_id2:
        resource["subType"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                    "code": healthcare_claim_type_id2,
                }
            ]
        }

    # Set events
    if events:
        resource["event"] = events

    # Set notes (combine status and outstanding notes)
    notes = status_notes + outstanding_notes
    if notes:
        resource["note"] = notes

    # Set priority (required in FHIR R4B)
    resource["priority"] = {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/processpriority",
                "code": "normal",
            }
        ]
    }

    return Claim(**resource)
