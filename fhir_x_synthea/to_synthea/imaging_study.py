"""FHIR R4 ImagingStudy → Synthea ImagingStudy"""

import logging
from datetime import datetime

from fhir.resources.imagingstudy import ImagingStudy
from synthea_pydantic import ImagingStudy as SyntheaImagingStudy

from ..synthea_csv_lib import (
    extract_coding_code,
    extract_display_or_text,
    extract_reference_id,
    normalize_sop_code,
    parse_datetime,
)

logger = logging.getLogger(__name__)


def convert(src: ImagingStudy) -> list[SyntheaImagingStudy]:
    """Convert FHIR R4 ImagingStudy to Synthea ImagingStudy(s).

    Returns one row per series-instance pair.

    Args:
        src: FHIR R4 ImagingStudy resource

    Returns:
        List of Synthea ImagingStudy models

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Check logs for warnings about dropped data.
    """
    fhir_resource = src.model_dump(exclude_none=True)
    results = []

    # Extract common fields
    identifiers = fhir_resource.get("identifier", [])
    study_id = ""
    if identifiers:
        study_id = identifiers[0].get("value", "")

    started = fhir_resource.get("started", "")
    date_str = parse_datetime(started) if started else None
    study_date = None
    if date_str:
        try:
            study_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass

    subject = fhir_resource.get("subject")
    patient_id = extract_reference_id(subject) if subject else ""

    encounter = fhir_resource.get("encounter")
    encounter_id = extract_reference_id(encounter) if encounter else ""

    # Extract Procedure Code
    procedure_codes = fhir_resource.get("procedureCode", [])
    procedure_code = ""
    if procedure_codes:
        first_procedure = procedure_codes[0]
        procedure_code = extract_coding_code(
            first_procedure, preferred_system="http://snomed.info/sct"
        )

    # Generate rows for each series-instance pair
    series_list = fhir_resource.get("series", [])

    for series in series_list:
        series_uid = series.get("uid", "")

        # Extract body site
        body_site = series.get("bodySite")
        body_site_code = ""
        body_site_description = ""
        if body_site:
            body_site_code = extract_coding_code(
                body_site, preferred_system="http://snomed.info/sct"
            )
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
            imaging = SyntheaImagingStudy(
                id=study_id or None,
                date=study_date,
                patient=patient_id or None,
                encounter=encounter_id or None,
                series_uid=series_uid or None,
                bodysite_code=body_site_code or None,
                bodysite_description=body_site_description or None,
                modality_code=modality_code or None,
                modality_description=modality_description or None,
                instance_uid=None,
                sop_code=None,
                sop_description=None,
                procedure_code=procedure_code or None,
                instance_number=None,
                description=None,
            )
            results.append(imaging)
        else:
            # Create one row per instance
            for idx, instance in enumerate(instances):
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

                instance_number = instance.get("number")

                imaging = SyntheaImagingStudy(
                    id=study_id or None,
                    date=study_date,
                    patient=patient_id or None,
                    encounter=encounter_id or None,
                    series_uid=series_uid or None,
                    bodysite_code=body_site_code or None,
                    bodysite_description=body_site_description or None,
                    modality_code=modality_code or None,
                    modality_description=modality_description or None,
                    instance_uid=instance_uid or None,
                    sop_code=sop_code or None,
                    sop_description=sop_description or None,
                    procedure_code=procedure_code or None,
                    instance_number=instance_number,
                    description=None,
                )
                results.append(imaging)

    # If no series, return at least one row with common fields
    if not results:
        imaging = SyntheaImagingStudy(
            id=study_id or None,
            date=study_date,
            patient=patient_id or None,
            encounter=encounter_id or None,
            series_uid=None,
            bodysite_code=None,
            bodysite_description=None,
            modality_code=None,
            modality_description=None,
            instance_uid=None,
            sop_code=None,
            sop_description=None,
            procedure_code=procedure_code or None,
            instance_number=None,
            description=None,
        )
        results.append(imaging)

    return results
