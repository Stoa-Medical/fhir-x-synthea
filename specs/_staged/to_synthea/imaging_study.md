# ImagingStudy (FHIR R4 ➜ Synthea imaging_studies.csv)

## Semantic Context
Maps a FHIR R4 `ImagingStudy` resource to a Synthea `imaging_studies.csv` row. Each output row corresponds to one series-instance pair in the FHIR resource.

## Field Mappings
```python
# FHIR ImagingStudy → Synthea CSV imaging_studies mapping
# (source_field, target_field, semantic_concept, transform, notes)
imaging_studies_reverse_mapping = [
    ("ImagingStudy.identifier[0].value", "imaging_studies.Id", "Business identifier of study", "Prefer first identifier value", "FHIR id is not used here; empty if none"),
    ("ImagingStudy.started", "imaging_studies.Date", "Study start datetime", "Pass through/normalize", "iso8601 UTC; if absent, empty"),
    ("ImagingStudy.subject.reference", "imaging_studies.Patient", "Patient reference", "Extract Patient/{id} → {id}", ""),
    ("ImagingStudy.encounter.reference", "imaging_studies.Encounter", "Encounter reference", "Extract Encounter/{id} → {id}", ""),
    ("ImagingStudy.series[n].uid", "imaging_studies.Series UID", "DICOM Series UID", "Per series", "One row per series-instance"),
    ("ImagingStudy.series[n].bodySite.coding[0].code", "imaging_studies.Body Site Code", "Body site (SNOMED)", "Prefer SNOMED coding; else first coding", ""),
    ("ImagingStudy.series[n].bodySite", "imaging_studies.Body Site Description", "Human-readable body site", "Prefer coding.display, else bodySite.text", "As available"),
    ("ImagingStudy.series[n].modality.code", "imaging_studies.Modality Code", "Imaging modality (DICOM)", "Prefer DICOM-DCM system; else use .code", ""),
    ("ImagingStudy.series[n].modality.display", "imaging_studies.Modality Description", "Modality display", "Direct copy", "As available"),
    ("ImagingStudy.series[n].instance[m].uid", "imaging_studies.Instance UID", "DICOM SOP Instance UID", "Per instance", ""),
    ("ImagingStudy.series[n].instance[m].sopClass.code", "imaging_studies.SOP Code", "SOP Class UID", "Strip urn:oid: prefix if present", "Else use as is"),
    ("ImagingStudy.series[n].instance[m].sopClass.display", "imaging_studies.SOP Description", "SOP class display", "Direct copy", "As available"),
    ("ImagingStudy.procedureCode[0].coding", "imaging_studies.Procedure Code", "Procedure Code (SNOMED)", "Prefer SNOMED coding; else first coding .code", ""),
]
```

## Accepted FHIR Variants
- If `bodySite.coding` has multiple entries, prefer SNOMED (`http://snomed.info/sct`).
- If `modality` includes system, prefer DICOM-DCM (`http://dicom.nema.org/resources/ontology/DCM`).
- `sopClass.code` may be a full URN (e.g., `urn:oid:1.2.840...`) or just an OID fragment; CSV expects the OID only.

## Implementation Notes
- Multiple output rows are produced by iterating `series` and their `instance` arrays.
- Implementation in `fhir_x_synthea_csv/to_synthea_csv/imaging_study.py`.
