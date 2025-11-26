"""Synthea ImagingStudy → FHIR R4 ImagingStudy"""

from fhir.resources.imagingstudy import ImagingStudy
from synthea_pydantic import ImagingStudy as SyntheaImagingStudy

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import format_datetime, identifier, ref
from ..utils import normalize_sop_code_with_prefix


def _resource_id(d: dict) -> str:
    """Generate deterministic resource ID."""
    patient_id = grab(d, "patient") or ""
    date = (grab(d, "date") or "").replace(" ", "-").replace(":", "-")
    series_uid = grab(d, "series_uid") or ""
    instance_uid = grab(d, "instance_uid") or ""
    return f"imaging-{patient_id}-{date}-{series_uid}-{instance_uid}".replace(" ", "-")


def _body_site(code: str | None, description: str | None) -> dict | None:
    """Build body site CodeableConcept."""
    if not code and not description:
        return None
    result: dict = {}
    if code:
        coding = {"system": "http://snomed.info/sct", "code": code}
        if description:
            coding["display"] = description
        result["coding"] = [coding]
    if description:
        result["text"] = description
    return result if result else None


def _modality(code: str | None, description: str | None) -> dict | None:
    """Build modality Coding."""
    if not code and not description:
        return None
    result: dict = {}
    if code:
        coding = {
            "system": "http://dicom.nema.org/resources/ontology/DCM",
            "code": code,
        }
        if description:
            coding["display"] = description
        result["coding"] = [coding]
    if description:
        result["text"] = description
    return result if result else None


def _sop_class(code: str | None, description: str | None) -> dict | None:
    """Build SOP class Coding."""
    normalized_code = normalize_sop_code_with_prefix(code)
    if not normalized_code and not description:
        return None
    result: dict = {}
    if normalized_code:
        coding = {"system": "urn:ietf:rfc:3986", "code": normalized_code}
        if description:
            coding["display"] = description
        result["coding"] = [coding]
    if description:
        result["text"] = description
    return result if result else None


def _build_instance(d: dict):
    """Build instance structure."""
    instance_uid = grab(d, "instance_uid")
    sop_code = grab(d, "sop_code")
    sop_description = grab(d, "sop_description")

    if not instance_uid and not sop_code and not sop_description:
        return None

    result = {}
    if instance_uid:
        result["uid"] = instance_uid

    sop = _sop_class(sop_code, sop_description)
    if sop:
        result["sopClass"] = sop

    return result if result else None


def _build_series(d: dict):
    """Build series structure."""
    series_uid = grab(d, "series_uid")
    body_site_code = grab(d, "bodysite_code")
    body_site_description = grab(d, "bodysite_description")
    modality_code = grab(d, "modality_code")
    modality_description = grab(d, "modality_description")

    instance = _build_instance(d)

    if not any(
        [
            series_uid,
            body_site_code,
            body_site_description,
            modality_code,
            modality_description,
            instance,
        ]
    ):
        return None

    result = {}
    if series_uid:
        result["uid"] = series_uid

    body_site = _body_site(body_site_code, body_site_description)
    if body_site:
        result["bodySite"] = body_site

    modality = _modality(modality_code, modality_description)
    if modality:
        result["modality"] = modality

    if instance:
        result["instance"] = [instance]

    return [result] if result else None


def _procedure_code(code: str | None):
    """Build procedureCode CodeableConcept."""
    if not code:
        return None
    return [{"coding": [{"system": "http://snomed.info/sct", "code": code}]}]


@mapper
def _to_fhir_imaging_study(d: dict):
    """Core mapping from dict to FHIR ImagingStudy structure."""
    study_id = grab(d, "id")

    return {
        "resourceType": "ImagingStudy",
        "id": _resource_id(d),
        "status": "available",
        "identifier": [identifier(system="urn:synthea:imaging_studies", value=study_id)]
        if study_id
        else None,
        "started": grab(d, "date", apply=format_datetime),
        "subject": ref("Patient", grab(d, "patient")),
        "encounter": ref("Encounter", grab(d, "encounter")),
        "procedureCode": _procedure_code(grab(d, "procedure_code")),
        "series": _build_series(d),
    }


def convert(src: SyntheaImagingStudy) -> ImagingStudy:
    """Convert Synthea ImagingStudy to FHIR R4 ImagingStudy.

    Args:
        src: Synthea ImagingStudy model

    Returns:
        FHIR R4 ImagingStudy resource
    """
    return ImagingStudy(**_to_fhir_imaging_study(to_dict(src)))
