"""Synthea ImagingStudy → FHIR R4 ImagingStudy"""

from typing import Any

from fhir.resources.imagingstudy import ImagingStudy
from synthea_pydantic import ImagingStudy as SyntheaImagingStudy

from ..fhir_lib import create_reference, format_datetime
from ..utils import normalize_sop_code_with_prefix, to_str


def convert(src: SyntheaImagingStudy) -> ImagingStudy:
    """Convert Synthea ImagingStudy to FHIR R4 ImagingStudy.

    Args:
        src: Synthea ImagingStudy model

    Returns:
        FHIR R4 ImagingStudy resource
    """
    d = src.model_dump()

    # Extract and process fields (synthea_pydantic uses lowercase/snake_case keys)
    study_id = to_str(d.get("id"))
    date = to_str(d.get("date"))
    patient_id = to_str(d.get("patient"))
    encounter_id = to_str(d.get("encounter"))
    series_uid = to_str(d.get("series_uid"))
    body_site_code = to_str(d.get("bodysite_code"))
    body_site_description = to_str(d.get("bodysite_description"))
    modality_code = to_str(d.get("modality_code"))
    modality_description = to_str(d.get("modality_description"))
    instance_uid = to_str(d.get("instance_uid"))
    sop_code = to_str(d.get("sop_code"))
    sop_description = to_str(d.get("sop_description"))
    procedure_code = to_str(d.get("procedure_code"))

    # Generate deterministic resource ID
    date_clean = date.replace(" ", "-").replace(":", "-") if date else ""
    resource_id = (
        f"imaging-{patient_id}-{date_clean}-{series_uid}-{instance_uid}".replace(
            " ", "-"
        )
    )

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "ImagingStudy",
        "id": resource_id,
        "status": "available",
    }

    # Set identifier (business identifier)
    if study_id:
        resource["identifier"] = [
            {"system": "urn:synthea:imaging_studies", "value": study_id}
        ]

    # Set started datetime
    if date:
        iso_date = format_datetime(date)
        if iso_date:
            resource["started"] = iso_date

    # Set subject (patient) reference
    if patient_id:
        patient_ref = create_reference("Patient", patient_id)
        if patient_ref:
            resource["subject"] = patient_ref

    # Set encounter reference
    if encounter_id:
        encounter_ref = create_reference("Encounter", encounter_id)
        if encounter_ref:
            resource["encounter"] = encounter_ref

    # Set procedureCode (SNOMED CT)
    if procedure_code:
        resource["procedureCode"] = [
            {"coding": [{"system": "http://snomed.info/sct", "code": procedure_code}]}
        ]

    # Build series structure
    series: dict[str, Any] = {}

    # Series UID
    if series_uid:
        series["uid"] = series_uid

    # Body site (SNOMED CT)
    if body_site_code or body_site_description:
        body_site: dict[str, Any] = {}
        if body_site_code:
            coding = {"system": "http://snomed.info/sct", "code": body_site_code}
            if body_site_description:
                coding["display"] = body_site_description
            body_site["coding"] = [coding]
        if body_site_description:
            body_site["text"] = body_site_description
        if body_site:
            series["bodySite"] = body_site

    # Modality (DICOM)
    if modality_code or modality_description:
        modality: dict[str, Any] = {}
        if modality_code:
            coding = {
                "system": "http://dicom.nema.org/resources/ontology/DCM",
                "code": modality_code,
            }
            if modality_description:
                coding["display"] = modality_description
            modality["coding"] = [coding]
        if modality_description:
            modality["text"] = modality_description
        if modality:
            series["modality"] = modality

    # Build instance structure
    instance: dict[str, Any] = {}

    # Instance UID
    if instance_uid:
        instance["uid"] = instance_uid

    # SOP Class
    if sop_code or sop_description:
        normalized_sop = normalize_sop_code_with_prefix(sop_code)
        sop_class: dict[str, Any] = {}
        if normalized_sop:
            coding = {"system": "urn:ietf:rfc:3986", "code": normalized_sop}
            if sop_description:
                coding["display"] = sop_description
            sop_class["coding"] = [coding]
        if sop_description:
            sop_class["text"] = sop_description
        if sop_class:
            instance["sopClass"] = sop_class

    # Add instance to series if instance has content
    if instance:
        series["instance"] = [instance]

    # Add series to resource if series has content
    if series:
        resource["series"] = [series]

    return ImagingStudy(**resource)
