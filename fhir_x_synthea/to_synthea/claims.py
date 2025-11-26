"""
Mapping function for converting FHIR Claim resources to Synthea claims.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import (
    extract_extension_string,
    extract_reference_id,
    parse_datetime_to_date,
)


def map_fhir_claim_to_csv(fhir_resource: dict[str, Any]) -> dict[str, Any]:
    """
    Map a FHIR R4 Claim resource to a Synthea claims.csv row.

    Args:
        fhir_resource: Dictionary representing a FHIR Claim resource

    Returns:
        Dictionary with CSV column names as keys
    """

    # Helper to find event by type code
    def find_event_by_code(events: list[dict[str, Any]], event_code: str) -> str:
        for event in events:
            event_type = event.get("type", {})
            codings = event_type.get("coding", [])
            for coding in codings:
                code = coding.get("code", "")
                if code == event_code:
                    when = event.get("whenDateTime")
                    if when:
                        return parse_datetime_to_date(when)
        return ""

    # Initialize CSV row
    csv_row: dict[str, str] = {
        "Id": "",
        "Patient ID": "",
        "Provider ID": "",
        "Primary Patient Insurance ID": "",
        "Secondary Patient Insurance ID": "",
        "Department ID": "",
        "Patient Department ID": "",
        "Diagnosis1": "",
        "Diagnosis2": "",
        "Diagnosis3": "",
        "Diagnosis4": "",
        "Diagnosis5": "",
        "Diagnosis6": "",
        "Diagnosis7": "",
        "Diagnosis8": "",
        "Referring Provider ID": "",
        "Appointment ID": "",
        "Current Illness Date": "",
        "Service Date": "",
        "Supervising Provider ID": "",
        "Status1": "",
        "Status2": "",
        "StatusP": "",
        "Outstanding1": "",
        "Outstanding2": "",
        "OutstandingP": "",
        "LastBilledDate1": "",
        "LastBilledDate2": "",
        "LastBilledDateP": "",
        "HealthcareClaimTypeID1": "",
        "HealthcareClaimTypeID2": "",
    }

    # Extract Id
    resource_id = fhir_resource.get("id", "")
    if resource_id:
        csv_row["Id"] = resource_id

    # Extract Patient ID
    patient = fhir_resource.get("patient")
    if patient:
        csv_row["Patient ID"] = extract_reference_id(patient)

    # Extract Provider ID
    provider = fhir_resource.get("provider")
    if provider:
        csv_row["Provider ID"] = extract_reference_id(provider)

    # Extract Insurance (Primary and Secondary)
    insurance_list = fhir_resource.get("insurance", [])
    for i, insurance in enumerate(insurance_list[:2]):
        coverage = insurance.get("coverage")
        if coverage:
            coverage_id = extract_reference_id(coverage)
            sequence = insurance.get("sequence", i + 1)
            focal = insurance.get("focal", sequence == 1)

            if sequence == 1 or focal:
                csv_row["Primary Patient Insurance ID"] = coverage_id
            elif sequence == 2 or not focal:
                csv_row["Secondary Patient Insurance ID"] = coverage_id

    # Extract Department IDs from extensions
    csv_row["Department ID"] = extract_extension_string(
        fhir_resource, "http://synthea.tools/StructureDefinition/department-id"
    )
    csv_row["Patient Department ID"] = extract_extension_string(
        fhir_resource, "http://synthea.tools/StructureDefinition/patient-department-id"
    )

    # Extract Diagnosis codes (up to 8)
    diagnoses = fhir_resource.get("diagnosis", [])
    diagnosis_indices = [
        "Diagnosis1",
        "Diagnosis2",
        "Diagnosis3",
        "Diagnosis4",
        "Diagnosis5",
        "Diagnosis6",
        "Diagnosis7",
        "Diagnosis8",
    ]

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
                csv_row[diagnosis_indices[i]] = code

    # Extract Appointment ID from item
    items = fhir_resource.get("item", [])
    if items:
        first_item = items[0]
        encounters = first_item.get("encounter", [])
        if encounters:
            first_encounter = encounters[0]
            csv_row["Appointment ID"] = extract_reference_id(first_encounter)

    # Extract events
    events = fhir_resource.get("event", [])
    csv_row["Current Illness Date"] = find_event_by_code(events, "onset")
    csv_row["LastBilledDate1"] = find_event_by_code(events, "bill-primary")
    csv_row["LastBilledDate2"] = find_event_by_code(events, "bill-secondary")
    csv_row["LastBilledDateP"] = find_event_by_code(events, "bill-patient")

    # Extract Service Date from billablePeriod
    billable_period = fhir_resource.get("billablePeriod", {})
    start = billable_period.get("start")
    end = billable_period.get("end")
    if start:
        csv_row["Service Date"] = parse_datetime_to_date(start)
    elif end:
        csv_row["Service Date"] = parse_datetime_to_date(end)

    # Extract Supervising Provider from careTeam
    care_team = fhir_resource.get("careTeam", [])
    for team_member in care_team:
        role = team_member.get("role", {})
        role_text = role.get("text", "")
        if role_text == "supervising":
            provider_ref = team_member.get("provider")
            if provider_ref:
                csv_row["Supervising Provider ID"] = extract_reference_id(provider_ref)
                break

    # Extract Claim Type
    claim_type = fhir_resource.get("type", {})
    type_codings = claim_type.get("coding", [])
    for coding in type_codings:
        code = coding.get("code", "")
        if code == "professional":
            csv_row["HealthcareClaimTypeID1"] = "1"
        elif code == "institutional":
            csv_row["HealthcareClaimTypeID1"] = "2"
        break

    # Extract SubType
    sub_type = fhir_resource.get("subType", {})
    sub_type_codings = sub_type.get("coding", [])
    if sub_type_codings:
        csv_row["HealthcareClaimTypeID2"] = sub_type_codings[0].get("code", "")

    # Note: Status1/Status2/StatusP and Outstanding1/2/P are not on Claim
    # They would need to come from ClaimResponse if available

    return csv_row
