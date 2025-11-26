"""
Mapping function for converting Synthea claims.csv rows to FHIR Claim resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime


def map_claim(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea claims.csv row to a FHIR R4 Claim resource.

    Args:
        csv_row: Dictionary with keys like Id, Patient ID, Provider ID,
                Primary Patient Insurance ID, Secondary Patient Insurance ID,
                Department ID, Patient Department ID, Diagnosis1-Diagnosis8,
                Referring Provider ID, Appointment ID, Current Illness Date,
                Service Date, Supervising Provider ID, Status1/Status2/StatusP,
                Outstanding1/2/P, LastBilledDate1/2/P, HealthcareClaimTypeID1/2

    Returns:
        Dictionary representing a FHIR Claim resource
    """

    # Extract and process fields
    claim_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    patient_id = (
        csv_row.get("Patient ID", "").strip() if csv_row.get("Patient ID") else ""
    )
    provider_id = (
        csv_row.get("Provider ID", "").strip() if csv_row.get("Provider ID") else ""
    )
    primary_insurance_id = (
        csv_row.get("Primary Patient Insurance ID", "").strip()
        if csv_row.get("Primary Patient Insurance ID")
        else ""
    )
    secondary_insurance_id = (
        csv_row.get("Secondary Patient Insurance ID", "").strip()
        if csv_row.get("Secondary Patient Insurance ID")
        else ""
    )
    department_id = (
        csv_row.get("Department ID", "").strip() if csv_row.get("Department ID") else ""
    )
    patient_department_id = (
        csv_row.get("Patient Department ID", "").strip()
        if csv_row.get("Patient Department ID")
        else ""
    )
    appointment_id = (
        csv_row.get("Appointment ID", "").strip()
        if csv_row.get("Appointment ID")
        else ""
    )
    current_illness_date = (
        csv_row.get("Current Illness Date", "").strip()
        if csv_row.get("Current Illness Date")
        else ""
    )
    service_date = (
        csv_row.get("Service Date", "").strip() if csv_row.get("Service Date") else ""
    )
    supervising_provider_id = (
        csv_row.get("Supervising Provider ID", "").strip()
        if csv_row.get("Supervising Provider ID")
        else ""
    )
    healthcare_claim_type_id1 = (
        csv_row.get("HealthcareClaimTypeID1", "").strip()
        if csv_row.get("HealthcareClaimTypeID1")
        else ""
    )
    healthcare_claim_type_id2 = (
        csv_row.get("HealthcareClaimTypeID2", "").strip()
        if csv_row.get("HealthcareClaimTypeID2")
        else ""
    )

    # Extract diagnosis codes (Diagnosis1-8)
    diagnoses = []
    for i in range(1, 9):
        diag_key = f"Diagnosis{i}"
        diag_code = csv_row.get(diag_key, "").strip() if csv_row.get(diag_key) else ""
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

    # Extract status notes (Status1, Status2, StatusP)
    status_notes = []
    for status_key in ["Status1", "Status2", "StatusP"]:
        status_value = (
            csv_row.get(status_key, "").strip() if csv_row.get(status_key) else ""
        )
        if status_value:
            status_notes.append({"text": status_value})

    # Extract outstanding amounts (Outstanding1, Outstanding2, OutstandingP)
    outstanding_notes = []
    for outstanding_key in ["Outstanding1", "Outstanding2", "OutstandingP"]:
        outstanding_value = (
            csv_row.get(outstanding_key, "").strip()
            if csv_row.get(outstanding_key)
            else ""
        )
        if outstanding_value:
            outstanding_notes.append({"text": f"Outstanding: {outstanding_value}"})

    # Extract billing events (LastBilledDate1, LastBilledDate2, LastBilledDateP)
    events = []
    billing_dates = [
        ("LastBilledDate1", "bill-primary"),
        ("LastBilledDate2", "bill-secondary"),
        ("LastBilledDateP", "bill-patient"),
    ]
    for date_key, event_code in billing_dates:
        date_value = csv_row.get(date_key, "").strip() if csv_row.get(date_key) else ""
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
        "id": claim_id if claim_id else "",
    }

    # Set identifier (business identifier)
    if claim_id:
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
            resource["item"] = [{"encounter": [encounter_ref]}]

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

    return resource
