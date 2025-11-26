"""Synthea Patient → FHIR R4 Patient"""

from fhir.resources.patient import Patient
from synthea_pydantic import Patient as SyntheaPatient

from ..chidian_ext import KEEP, grab, mapper, to_dict
from ..fhir_lib import (
    format_date,
    format_datetime,
    identifier,
    map_gender,
    map_marital_status,
)


def _mrn_identifier(patient_id: str | None):
    """Create Medical Record Number identifier."""
    return identifier(system="urn:oid:2.16.840.1.113883.19.5", value=patient_id)


def _ssn_identifier(ssn: str | None):
    """Create SSN identifier."""
    return identifier(
        system=None,
        value=ssn,
        type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
        type_code="SS",
        type_display="Social Security Number",
    )


def _drivers_identifier(drivers: str | None):
    """Create Driver's License identifier."""
    return identifier(
        system=None,
        value=drivers,
        type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
        type_code="DL",
        type_display="Driver's License",
    )


def _passport_identifier(passport: str | None):
    """Create Passport identifier."""
    return identifier(
        system=None,
        value=passport,
        type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
        type_code="PPN",
        type_display="Passport Number",
    )


def _official_name(d: dict):
    """Build official HumanName."""
    first = grab(d, "first")
    last = grab(d, "last")
    prefix = grab(d, "prefix")
    suffix = grab(d, "suffix")

    if not any([first, last, prefix, suffix]):
        return None

    return {
        "use": "official",
        "family": last,
        "given": [first] if first else None,
        "prefix": [prefix] if prefix else None,
        "suffix": [suffix] if suffix else None,
    }


def _maiden_name(maiden: str | None):
    """Build maiden HumanName."""
    if not maiden:
        return None
    return {"use": "maiden", "family": maiden}


def _race_extension(race: str | None):
    """Build US Core race extension."""
    if not race:
        return None
    return {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
        "extension": [{"url": "text", "valueString": race}],
    }


def _ethnicity_extension(ethnicity: str | None):
    """Build US Core ethnicity extension."""
    if not ethnicity:
        return None
    return {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
        "extension": [{"url": "text", "valueString": ethnicity}],
    }


def _birthplace_extension(birthplace: str | None):
    """Build birthplace extension."""
    if not birthplace:
        return None
    return {
        "url": "http://hl7.org/fhir/StructureDefinition/birthPlace",
        "valueAddress": {"text": birthplace},
    }


def _geolocation_extension(lat, lon):
    """Build geolocation extension."""
    if lat is None or lon is None:
        return None
    return {
        "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
        "extension": [
            {"url": "latitude", "valueDecimal": float(lat)},
            {"url": "longitude", "valueDecimal": float(lon)},
        ],
    }


def _address(d: dict):
    """Build FHIR Address."""
    address = grab(d, "address")
    city = grab(d, "city")
    state = grab(d, "state")
    county = grab(d, "county")
    zip_code = grab(d, "zip")
    lat = grab(d, "lat")
    lon = grab(d, "lon")

    if not any(
        [address, city, state, county, zip_code, lat is not None and lon is not None]
    ):
        return None

    geo = _geolocation_extension(lat, lon)
    return {
        "use": "home",
        "line": [address] if address else None,
        "city": city,
        "state": state,
        "district": county,
        "postalCode": zip_code,
        "extension": [geo] if geo else None,
    }


@mapper
def _to_fhir_patient(d: dict):
    """Core mapping from dict to FHIR Patient structure."""
    patient_id = grab(d, "id")
    deathdate = grab(d, "deathdate")

    # Build identifiers list, filtering out None values
    identifiers = [
        i
        for i in [
            _mrn_identifier(patient_id),
            _ssn_identifier(grab(d, "ssn")),
            _drivers_identifier(grab(d, "drivers")),
            _passport_identifier(grab(d, "passport")),
        ]
        if i is not None
    ]

    # Build names list
    names = [n for n in [_official_name(d), _maiden_name(grab(d, "maiden"))] if n]

    # Build extensions list
    extensions = [
        e
        for e in [
            _race_extension(grab(d, "race")),
            _ethnicity_extension(grab(d, "ethnicity")),
            _birthplace_extension(grab(d, "birthplace")),
        ]
        if e
    ]

    # Build address
    addr = _address(d)

    return {
        "resourceType": "Patient",
        "id": patient_id,
        "identifier": identifiers if identifiers else None,
        "name": names if names else None,
        "gender": grab(d, "gender", apply=map_gender),
        "birthDate": grab(d, "birthdate", apply=format_date),
        "deceasedDateTime": format_datetime(deathdate) if deathdate else None,
        "deceasedBoolean": KEEP(False) if not deathdate else None,
        "maritalStatus": grab(d, "marital", apply=map_marital_status),
        "address": [addr] if addr else None,
        "extension": extensions if extensions else None,
    }


def convert(src: SyntheaPatient) -> Patient:
    """Convert Synthea Patient to FHIR R4 Patient.

    Args:
        src: Synthea Patient model

    Returns:
        FHIR R4 Patient resource
    """
    return Patient(**_to_fhir_patient(to_dict(src)))
