"""FHIR R4 Claim → Synthea Claim"""

import logging
from datetime import date
from typing import Any

from fhir.resources.claim import Claim
from synthea_pydantic import Claim as SyntheaClaim

from ..synthea_csv_lib import (
    extract_extension_string,
    extract_reference_id,
    parse_datetime_to_date,
)

logger = logging.getLogger(__name__)


def _find_event_by_code(events: list[dict[str, Any]], event_code: str) -> date | None:
    """Find event by type code and return its date."""
    for event in events:
        event_type = event.get("type", {})
        codings = event_type.get("coding", [])
        for coding in codings:
            code = coding.get("code", "")
            if code == event_code:
                when = event.get("whenDateTime")
                if when:
                    parsed = parse_datetime_to_date(when)
                    if parsed:
                        return date.fromisoformat(parsed)
    return None


def convert(src: Claim) -> SyntheaClaim:
    """Convert FHIR R4 Claim to Synthea Claim.

    Args:
        src: FHIR R4 Claim resource

    Returns:
        Synthea Claim model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract Id
    resource_id = fhir_resource.get("id", "")

    # Extract Patient ID
    patient_id = ""
    patient = fhir_resource.get("patient")
    if patient:
        patient_id = extract_reference_id(patient)

    # Extract Provider ID
    provider_id = ""
    provider = fhir_resource.get("provider")
    if provider:
        provider_id = extract_reference_id(provider)

    # Extract Insurance (Primary and Secondary)
    primary_insurance_id = ""
    secondary_insurance_id = ""
    insurance_list = fhir_resource.get("insurance", [])
    for i, insurance in enumerate(insurance_list[:2]):
        coverage = insurance.get("coverage")
        if coverage:
            coverage_id = extract_reference_id(coverage)
            sequence = insurance.get("sequence", i + 1)
            focal = insurance.get("focal", sequence == 1)

            if sequence == 1 or focal:
                primary_insurance_id = coverage_id
            elif sequence == 2 or not focal:
                secondary_insurance_id = coverage_id

    # Extract Department IDs from extensions
    department_id = extract_extension_string(
        fhir_resource, "http://synthea.tools/StructureDefinition/department-id"
    )
    patient_department_id = extract_extension_string(
        fhir_resource, "http://synthea.tools/StructureDefinition/patient-department-id"
    )

    # Extract Diagnosis codes (up to 8)
    diagnoses = fhir_resource.get("diagnosis", [])
    diagnosis_codes = ["", "", "", "", "", "", "", ""]
    for i, diagnosis in enumerate(diagnoses[:8]):
        diagnosis_codeable = diagnosis.get("diagnosisCodeableConcept", {})
        codings = diagnosis_codeable.get("coding", [])
        if codings:
            # Prefer SNOMED
            code = ""
            for coding in codings:
                if "snomed.info" in coding.get("system", ""):
                    code = coding.get("code", "")
                    break
            if not code and codings:
                code = codings[0].get("code", "")
            if code:
                diagnosis_codes[i] = code

    # Extract Appointment ID from item
    appointment_id = ""
    items = fhir_resource.get("item", [])
    if items:
        first_item = items[0]
        encounters = first_item.get("encounter", [])
        if encounters:
            first_encounter = encounters[0]
            appointment_id = extract_reference_id(first_encounter)

    # Extract events
    events = fhir_resource.get("event", [])
    current_illness_date = _find_event_by_code(events, "onset")
    last_billed_date1 = _find_event_by_code(events, "bill-primary")
    last_billed_date2 = _find_event_by_code(events, "bill-secondary")
    last_billed_datep = _find_event_by_code(events, "bill-patient")

    # Extract Service Date from billablePeriod
    service_date = None
    billable_period = fhir_resource.get("billablePeriod", {})
    start = billable_period.get("start")
    end = billable_period.get("end")
    if start:
        parsed = parse_datetime_to_date(start)
        if parsed:
            service_date = date.fromisoformat(parsed)
    elif end:
        parsed = parse_datetime_to_date(end)
        if parsed:
            service_date = date.fromisoformat(parsed)

    # Extract Supervising Provider from careTeam
    supervising_provider_id = ""
    care_team = fhir_resource.get("careTeam", [])
    for team_member in care_team:
        role = team_member.get("role", {})
        role_text = role.get("text", "")
        if role_text == "supervising":
            provider_ref = team_member.get("provider")
            if provider_ref:
                supervising_provider_id = extract_reference_id(provider_ref)
                break

    # Extract Claim Type
    healthcare_claim_type_id1 = ""
    healthcare_claim_type_id2 = ""
    claim_type = fhir_resource.get("type", {})
    type_codings = claim_type.get("coding", [])
    for coding in type_codings:
        code = coding.get("code", "")
        if code == "professional":
            healthcare_claim_type_id1 = "1"
        elif code == "institutional":
            healthcare_claim_type_id1 = "2"
        break

    # Extract SubType
    sub_type = fhir_resource.get("subType", {})
    sub_type_codings = sub_type.get("coding", [])
    if sub_type_codings:
        healthcare_claim_type_id2 = sub_type_codings[0].get("code", "")

    # Note: Status1/Status2/StatusP and Outstanding1/2/P from notes
    # These would need parsing from note text if present
    status1 = ""
    status2 = ""
    statusp = ""
    outstanding1 = ""
    outstanding2 = ""
    outstandingp = ""

    notes = fhir_resource.get("note", [])
    for note in notes:
        text = note.get("text", "")
        if text.startswith("Outstanding:"):
            # This is a simplified extraction
            pass

    # Log lossy conversions
    if len(diagnoses) > 8:
        logger.warning(
            "Claim %s has %d diagnoses; only first 8 preserved",
            src.id,
            len(diagnoses),
        )

    return SyntheaClaim(
        id=resource_id or None,
        patientid=patient_id or None,
        providerid=provider_id or None,
        primarypatientinsuranceid=primary_insurance_id or None,
        secondarypatientinsuranceid=secondary_insurance_id or None,
        departmentid=department_id or None,
        patientdepartmentid=patient_department_id or None,
        diagnosis1=diagnosis_codes[0] or None,
        diagnosis2=diagnosis_codes[1] or None,
        diagnosis3=diagnosis_codes[2] or None,
        diagnosis4=diagnosis_codes[3] or None,
        diagnosis5=diagnosis_codes[4] or None,
        diagnosis6=diagnosis_codes[5] or None,
        diagnosis7=diagnosis_codes[6] or None,
        diagnosis8=diagnosis_codes[7] or None,
        referringproviderid=None,  # Not in FHIR Claim
        appointmentid=appointment_id or None,
        currentillnessdate=current_illness_date,
        servicedate=service_date,
        supervisingproviderid=supervising_provider_id or None,
        status1=status1 or None,
        status2=status2 or None,
        statusp=statusp or None,
        outstanding1=outstanding1 or None,
        outstanding2=outstanding2 or None,
        outstandingp=outstandingp or None,
        lastbilleddate1=last_billed_date1,
        lastbilleddate2=last_billed_date2,
        lastbilleddatep=last_billed_datep,
        healthcareclaimtypeid1=healthcare_claim_type_id1 or None,
        healthcareclaimtypeid2=healthcare_claim_type_id2 or None,
        healthcareclaimtypeidp=None,  # Not commonly used
    )
