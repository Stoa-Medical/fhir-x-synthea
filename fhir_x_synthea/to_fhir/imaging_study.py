"""
Mapping function for converting Synthea imaging_studies.csv rows to FHIR ImagingStudy resources.
"""

from typing import Any

from ..fhir_lib import create_reference, format_datetime


def map_imaging_study(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea imaging_studies.csv row to a FHIR R4 ImagingStudy resource.

    Args:
        csv_row: Dictionary with keys like Id, Date, Patient, Encounter,
                Series UID, Body Site Code, Body Site Description,
                Modality Code, Modality Description, Instance UID,
                SOP Code, SOP Description, Procedure Code

    Returns:
        Dictionary representing a FHIR ImagingStudy resource
    """

    # Helper to normalize SOP Code (add urn:oid: prefix if needed)
    def normalize_sop_code(sop_code: str | None) -> str | None:
        if not sop_code or sop_code.strip() == "":
            return None
        sop_code = sop_code.strip()
        if sop_code.startswith("urn:oid:"):
            return sop_code
        return f"urn:oid:{sop_code}"

    # Extract and process fields
    study_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    date = csv_row.get("Date", "").strip() if csv_row.get("Date") else ""
    patient_id = csv_row.get("Patient", "").strip() if csv_row.get("Patient") else ""
    encounter_id = (
        csv_row.get("Encounter", "").strip() if csv_row.get("Encounter") else ""
    )
    series_uid = (
        csv_row.get("Series UID", "").strip() if csv_row.get("Series UID") else ""
    )
    body_site_code = (
        csv_row.get("Body Site Code", "").strip()
        if csv_row.get("Body Site Code")
        else ""
    )
    body_site_description = (
        csv_row.get("Body Site Description", "").strip()
        if csv_row.get("Body Site Description")
        else ""
    )
    modality_code = (
        csv_row.get("Modality Code", "").strip() if csv_row.get("Modality Code") else ""
    )
    modality_description = (
        csv_row.get("Modality Description", "").strip()
        if csv_row.get("Modality Description")
        else ""
    )
    instance_uid = (
        csv_row.get("Instance UID", "").strip() if csv_row.get("Instance UID") else ""
    )
    sop_code = csv_row.get("SOP Code", "").strip() if csv_row.get("SOP Code") else ""
    sop_description = (
        csv_row.get("SOP Description", "").strip()
        if csv_row.get("SOP Description")
        else ""
    )
    procedure_code = (
        csv_row.get("Procedure Code", "").strip()
        if csv_row.get("Procedure Code")
        else ""
    )

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
        normalized_sop = normalize_sop_code(sop_code)
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

    return resource
