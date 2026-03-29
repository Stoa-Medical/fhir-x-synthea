# fhir-x-synthea-csv

Bidirectional mapping between FHIR R4 and Synthea CSV, built with [chidian](https://github.com/ericpan64/chidian).

Part of the broader **fhir-x-omop** project — this repo tackles the simpler case where FHIR and Synthea CSV represent equivalent data content, establishing patterns for the harder FHIR↔OMOP mapping.

## Quick start

```bash
uv sync
uv run python examples/roundtrip.py   # see the throughline
uv run pytest                          # run tests (no external data needed)
```

## Core throughline

The focused workflow covers 4 resource types end-to-end:

```
Synthea CSV (Patient, Encounter, Condition, Allergy)
    ↓  to_fhir converters
FHIR R4 Bundle
    ↓  extract_tables()
Synthea CSV (roundtripped)
```

**Key modules:**
- `fhir_x_synthea.to_fhir.{patient,encounter,condition,allergy}` — Synthea → FHIR
- `fhir_x_synthea.to_synthea.{patient,encounter,condition,allergy}` — FHIR → Synthea
- `fhir_x_synthea.bundle.patient_bundle()` — build a FHIR Bundle from Synthea data
- `fhir_x_synthea.extract.extract_tables()` — extract Synthea tables from a FHIR Bundle

## Usage

```python
from synthea_pydantic import Patient, Encounter, Condition

from fhir_x_synthea import patient_bundle, extract_tables
from fhir_x_synthea.to_fhir import patient as patient_to_fhir

# Convert a single resource
fhir_patient = patient_to_fhir.convert(synthea_patient)

# Build a full bundle with auto-wired references
bundle = patient_bundle(patient, encounters=encounters, conditions=conditions)

# Extract back to Synthea tables
tables = extract_tables(bundle)
```

## Project structure

```
fhir_x_synthea/
├── to_fhir/           # Synthea → FHIR converters (core 4)
│   └── _staged/       # Additional converters (not yet wired into orchestration)
├── to_synthea/        # FHIR → Synthea converters (core 4)
│   └── _staged/       # Additional converters
├── bundle.py          # Build FHIR Bundles from Synthea data
├── extract.py         # Extract Synthea tables from FHIR Bundles
├── chidian_ext.py     # chidian framework extensions
├── fhir_lib.py        # FHIR builder helpers (ref, coding, period, etc.)
├── synthea_lib.py     # Synthea field mapping helpers
└── types.py           # Shared types and reference helpers
examples/
├── roundtrip.py       # Complete throughline example
specs/
├── to_fhir/           # Mapping specifications (core)
├── to_synthea/        # Mapping specifications (core)
└── _staged/           # Specs for staged converters
tests/
├── test_core_conversions.py   # Unit tests for converters
└── test_roundtrip_bundle.py   # Integration tests for bundle roundtrip
```

## Staged converters

The `_staged/` directories contain converters for additional Synthea resource types (claims, medication, immunization, device, etc.). These are structurally complete but not yet wired into the `bundle`/`extract` orchestration layer. They'll be integrated as the throughline expands.

## Dependencies

- [chidian](https://github.com/ericpan64/chidian) — mapping framework
- [fhir.resources](https://pypi.org/project/fhir.resources/) — FHIR R4 Pydantic models
- [synthea-pydantic](https://pypi.org/project/synthea-pydantic/) — Synthea CSV Pydantic models

## Citations

FHIR is a registered trademark of Health Level Seven International.

> HL7 International. FHIR. 2025. https://www.hl7.org/fhir/

Synthea is a registered trademark of The MITRE Corporation.

> Jason Walonoski, Mark Kramer, Joseph Nichols, Andre Quina, Chris Moesel, Dylan Hall, Carlton Duffett, Kudakwashe Dube, Thomas Gallagher, Scott McLachlan, Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record, Journal of the American Medical Informatics Association, Volume 25, Issue 3, March 2018, Pages 230–238, https://doi.org/10.1093/jamia/ocx079
