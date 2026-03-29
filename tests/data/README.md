# Test data

Core tests use inline fixtures (see `conftest.py`) — no external data needed.

For integration testing against real Synthea output, download from https://synthea.mitre.org/downloads:
- 100 Sample CSV files → `tests/data/synthea_csv/`
- 100 Sample FHIR R4 files → `tests/data/fhir/`
