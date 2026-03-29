"""FHIR R4 Claim → Synthea Claim"""

import logging
from datetime import date

from fhir.resources.claim import Claim
from synthea_pydantic import Claim as SyntheaClaim

from ..chidian_ext import extract_ext, extract_ref_id, grab, mapper, parse_date, to_dict

logger = logging.getLogger(__name__)


def _find_event_by_code(events: list, event_code: str) -> date | None:
    """Find event by type code and return its date."""
    for event in events:
        codings = event.get("type", {}).get("coding", [])
        for coding in codings:
            if coding.get("code") == event_code:
                when = event.get("whenDateTime")
                if when:
                    parsed = parse_date({"dt": when}, "dt")
                    if parsed:
                        return date.fromisoformat(parsed)
    return None


def _extract_diagnosis_codes(d: dict) -> list[str]:
    """Extract up to 8 diagnosis codes."""
    diagnoses = grab(d, "diagnosis") or []
    codes = [""] * 8

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
            codes[i] = code

    # Log lossy conversions
    if len(diagnoses) > 8:
        logger.warning("Claim has %d diagnoses; only first 8 preserved", len(diagnoses))

    return codes


def _extract_insurance(d: dict) -> tuple[str, str]:
    """Extract primary and secondary insurance IDs."""
    insurance_list = grab(d, "insurance") or []
    primary = ""
    secondary = ""

    for insurance in insurance_list[:2]:
        coverage = insurance.get("coverage")
        if coverage:
            coverage_id = extract_ref_id({"c": coverage}, "c")
            sequence = insurance.get("sequence", 0)
            focal = insurance.get("focal", sequence == 1)

            if sequence == 1 or focal:
                primary = coverage_id
            elif sequence == 2 or not focal:
                secondary = coverage_id

    return primary, secondary


def _extract_supervising_provider(d: dict) -> str:
    """Extract supervising provider from careTeam."""
    care_team = grab(d, "careTeam") or []
    for team_member in care_team:
        role = team_member.get("role", {})
        if role.get("text") == "supervising":
            provider = team_member.get("provider")
            if provider:
                return extract_ref_id({"p": provider}, "p")
    return ""


def _extract_claim_type(d: dict) -> tuple[str, str]:
    """Extract claim type ID1 and ID2."""
    claim_type = grab(d, "type") or {}
    codings = claim_type.get("coding", [])
    type_id1 = ""
    for coding in codings:
        code = coding.get("code", "")
        if code == "professional":
            type_id1 = "1"
        elif code == "institutional":
            type_id1 = "2"
        break

    sub_type = grab(d, "subType") or {}
    sub_codings = sub_type.get("coding", [])
    type_id2 = sub_codings[0].get("code", "") if sub_codings else ""

    return type_id1, type_id2


@mapper(remove_empty=False)
def _to_synthea_claim(d: dict):
    """Core mapping from dict to Synthea Claim structure."""
    diagnosis_codes = _extract_diagnosis_codes(d)
    primary_insurance, secondary_insurance = _extract_insurance(d)
    type_id1, type_id2 = _extract_claim_type(d)

    # Extract events
    events = grab(d, "event") or []
    current_illness_date = _find_event_by_code(events, "onset")
    last_billed_date1 = _find_event_by_code(events, "bill-primary")
    last_billed_date2 = _find_event_by_code(events, "bill-secondary")
    last_billed_datep = _find_event_by_code(events, "bill-patient")

    # Extract service date from billablePeriod
    billable_period = grab(d, "billablePeriod") or {}
    service_date = None
    start = billable_period.get("start")
    end = billable_period.get("end")
    if start:
        parsed = parse_date({"dt": start}, "dt")
        if parsed:
            service_date = date.fromisoformat(parsed)
    elif end:
        parsed = parse_date({"dt": end}, "dt")
        if parsed:
            service_date = date.fromisoformat(parsed)

    # Extract appointment ID from item
    appointment_id = ""
    items = grab(d, "item") or []
    if items:
        encounters = items[0].get("encounter", [])
        if encounters:
            appointment_id = extract_ref_id({"e": encounters[0]}, "e")

    return {
        "id": grab(d, "id") or None,
        "patientid": extract_ref_id(d, "patient") or None,
        "providerid": extract_ref_id(d, "provider") or None,
        "primarypatientinsuranceid": primary_insurance or None,
        "secondarypatientinsuranceid": secondary_insurance or None,
        "departmentid": extract_ext(
            d,
            "http://synthea.tools/StructureDefinition/department-id",
            "valueString",
            "",
        )
        or None,
        "patientdepartmentid": extract_ext(
            d,
            "http://synthea.tools/StructureDefinition/patient-department-id",
            "valueString",
            "",
        )
        or None,
        "diagnosis1": diagnosis_codes[0] or None,
        "diagnosis2": diagnosis_codes[1] or None,
        "diagnosis3": diagnosis_codes[2] or None,
        "diagnosis4": diagnosis_codes[3] or None,
        "diagnosis5": diagnosis_codes[4] or None,
        "diagnosis6": diagnosis_codes[5] or None,
        "diagnosis7": diagnosis_codes[6] or None,
        "diagnosis8": diagnosis_codes[7] or None,
        "referringproviderid": None,
        "appointmentid": appointment_id or None,
        "currentillnessdate": current_illness_date,
        "servicedate": service_date,
        "supervisingproviderid": _extract_supervising_provider(d) or None,
        "status1": None,
        "status2": None,
        "statusp": None,
        "outstanding1": None,
        "outstanding2": None,
        "outstandingp": None,
        "lastbilleddate1": last_billed_date1,
        "lastbilleddate2": last_billed_date2,
        "lastbilleddatep": last_billed_datep,
        "healthcareclaimtypeid1": type_id1 or None,
        "healthcareclaimtypeid2": type_id2 or None,
        "healthcareclaimtypeidp": None,
    }


def convert(src: Claim) -> SyntheaClaim:
    """Convert FHIR R4 Claim to Synthea Claim.

    Args:
        src: FHIR R4 Claim resource

    Returns:
        Synthea Claim model
    """
    return SyntheaClaim(**_to_synthea_claim(to_dict(src)))
