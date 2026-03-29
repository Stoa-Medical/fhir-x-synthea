"""FHIR R4 ImagingStudy → Synthea ImagingStudy"""

import logging
from datetime import datetime

from fhir.resources.imagingstudy import ImagingStudy
from synthea_pydantic import ImagingStudy as SyntheaImagingStudy

from ..chidian_ext import extract_code, extract_display, extract_ref_id, grab, to_dict
from ..synthea_csv_lib import normalize_sop_code

logger = logging.getLogger(__name__)


def _extract_modality(modality: dict | None) -> tuple[str, str]:
    """Extract modality code and description."""
    if not modality:
        return "", ""

    codings = modality.get("coding", [])
    # Prefer DICOM-DCM system
    for coding in codings:
        if "dicom.nema.org" in coding.get("system", ""):
            return coding.get("code", ""), coding.get("display", "")

    # Fallback to first coding
    if codings:
        return codings[0].get("code", ""), codings[0].get("display", "")

    return "", ""


def _extract_sop_class(sop_class: dict | None) -> tuple[str, str]:
    """Extract SOP class code and description."""
    if not sop_class:
        return "", ""

    codings = sop_class.get("coding", [])
    if codings:
        raw_code = codings[0].get("code", "")
        return normalize_sop_code(raw_code), codings[0].get("display", "")

    # Try text field
    text = sop_class.get("text", "")
    if text:
        return normalize_sop_code(text), ""

    return "", ""


def convert(src: ImagingStudy) -> list[SyntheaImagingStudy]:
    """Convert FHIR R4 ImagingStudy to Synthea ImagingStudy(s).

    Returns one row per series-instance pair.

    Args:
        src: FHIR R4 ImagingStudy resource

    Returns:
        List of Synthea ImagingStudy models
    """
    d = to_dict(src)
    results = []

    # Extract common fields
    identifiers = grab(d, "identifier") or []
    study_id = identifiers[0].get("value", "") if identifiers else ""

    # Parse started datetime
    started = grab(d, "started")
    study_date = None
    if started:
        try:
            dt_str = str(started).replace("Z", "+00:00")
            study_date = datetime.fromisoformat(dt_str)
        except ValueError:
            pass

    patient_id = extract_ref_id(d, "subject")
    encounter_id = extract_ref_id(d, "encounter")

    # Extract procedure code
    procedure_codes = grab(d, "procedureCode") or []
    procedure_code = ""
    if procedure_codes:
        procedure_code = extract_code(
            {"p": procedure_codes[0]}, "p", system="http://snomed.info/sct"
        )

    # Generate rows for each series-instance pair
    series_list = grab(d, "series") or []

    for series in series_list:
        series_uid = series.get("uid", "")

        # Extract body site
        body_site = series.get("bodySite")
        body_site_code = (
            extract_code({"b": body_site}, "b", system="http://snomed.info/sct")
            if body_site
            else ""
        )
        body_site_description = (
            extract_display({"b": body_site}, "b") if body_site else ""
        )

        # Extract modality
        modality = series.get("modality")
        modality_code, modality_description = _extract_modality(modality)

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
            for instance in instances:
                instance_uid = instance.get("uid", "")
                sop_class = instance.get("sopClass")
                sop_code, sop_description = _extract_sop_class(sop_class)
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
