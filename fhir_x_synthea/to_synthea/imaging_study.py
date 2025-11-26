"""
Mapping function for converting FHIR ImagingStudy resources to Synthea imaging_studies.csv rows.
Returns multiple rows (one per series-instance pair).
"""

from typing import Any

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_reference_id,
    normalize_sop_code,
    parse_datetime,
)


def map_fhir_imaging_study_to_csv(
    fhir_resource: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Map a FHIR R4 ImagingStudy resource to Synthea imaging_studies.csv rows.
    Returns one row per series-instance pair.

    Args:
        fhir_resource: Dictionary representing a FHIR ImagingStudy resource

    Returns:
        List of dictionaries, each with CSV column names as keys
    """

    # Extract common fields
    identifiers = fhir_resource.get("identifier", [])
    study_id = ""
    if identifiers:
        study_id = identifiers[0].get("value", "")

    started = fhir_resource.get("started", "")
    date_str = parse_datetime(started) if started else ""

    subject = fhir_resource.get("subject")
    patient_id = extract_reference_id(subject) if subject else ""

    encounter = fhir_resource.get("encounter")
    encounter_id = extract_reference_id(encounter) if encounter else ""

    # Extract Procedure Code
    procedure_codes = fhir_resource.get("procedureCode", [])
    procedure_code = ""
    if procedure_codes:
        first_procedure = procedure_codes[0]
        procedure_code = extract_coding_code(first_procedure, "http://snomed.info/sct")

    # Generate rows for each series-instance pair
    rows = []
    series_list = fhir_resource.get("series", [])

    for series in series_list:
        series_uid = series.get("uid", "")

        # Extract body site
        body_site = series.get("bodySite")
        body_site_code = ""
        body_site_description = ""
        if body_site:
            body_site_code = extract_coding_code(body_site, "http://snomed.info/sct")
            body_site_description = extract_display_or_text(body_site)

        # Extract modality
        modality = series.get("modality")
        modality_code = ""
        modality_description = ""
        if modality:
            codings = modality.get("coding", [])
            if codings:
                # Prefer DICOM-DCM system
                for coding in codings:
                    if "dicom.nema.org" in coding.get("system", ""):
                        modality_code = coding.get("code", "")
                        modality_description = coding.get("display", "")
                        break
                # Fallback to first coding
                if not modality_code and codings:
                    modality_code = codings[0].get("code", "")
                    modality_description = codings[0].get("display", "")

        # Extract instances
        instances = series.get("instance", [])

        # If no instances, create one row with empty instance fields
        if not instances:
            row: dict[str, str] = {
                "Id": study_id,
                "Date": date_str,
                "Patient": patient_id,
                "Encounter": encounter_id,
                "Series UID": series_uid,
                "Body Site Code": body_site_code,
                "Body Site Description": body_site_description,
                "Modality Code": modality_code,
                "Modality Description": modality_description,
                "Instance UID": "",
                "SOP Code": "",
                "SOP Description": "",
                "Procedure Code": procedure_code,
            }
            rows.append(row)
        else:
            # Create one row per instance
            for instance in instances:
                instance_uid = instance.get("uid", "")

                # Extract SOP Class
                sop_class = instance.get("sopClass")
                sop_code = ""
                sop_description = ""
                if sop_class:
                    codings = sop_class.get("coding", [])
                    if codings:
                        sop_code_raw = codings[0].get("code", "")
                        sop_code = normalize_sop_code(sop_code_raw)
                        sop_description = codings[0].get("display", "")
                    else:
                        # If no coding, try text
                        sop_code_raw = sop_class.get("text", "")
                        sop_code = normalize_sop_code(sop_code_raw)

                row = {
                    "Id": study_id,
                    "Date": date_str,
                    "Patient": patient_id,
                    "Encounter": encounter_id,
                    "Series UID": series_uid,
                    "Body Site Code": body_site_code,
                    "Body Site Description": body_site_description,
                    "Modality Code": modality_code,
                    "Modality Description": modality_description,
                    "Instance UID": instance_uid,
                    "SOP Code": sop_code,
                    "SOP Description": sop_description,
                    "Procedure Code": procedure_code,
                }
                rows.append(row)

    # If no series, return at least one row with common fields
    if not rows:
        row = {
            "Id": study_id,
            "Date": date_str,
            "Patient": patient_id,
            "Encounter": encounter_id,
            "Series UID": "",
            "Body Site Code": "",
            "Body Site Description": "",
            "Modality Code": "",
            "Modality Description": "",
            "Instance UID": "",
            "SOP Code": "",
            "SOP Description": "",
            "Procedure Code": procedure_code,
        }
        rows.append(row)

    return rows
