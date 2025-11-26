"""Synthea Patient → FHIR R4 Patient"""

from typing import Any

from fhir.resources.patient import Patient
from synthea_pydantic import Patient as SyntheaPatient

from ..fhir_lib import (
    format_date,
    format_datetime,
    map_gender,
    map_marital_status,
)
from ..utils import to_str


def convert(src: SyntheaPatient) -> Patient:
    """Convert Synthea Patient to FHIR R4 Patient.

    Args:
        src: Synthea Patient model

    Returns:
        FHIR R4 Patient resource
    """
    d = src.model_dump()

    # Extract and process fields (synthea_pydantic uses lowercase keys)
    patient_id = to_str(d.get("id"))
    birthdate = to_str(d.get("birthdate"))
    deathdate = to_str(d.get("deathdate"))
    ssn = to_str(d.get("ssn"))
    drivers = to_str(d.get("drivers"))
    passport = to_str(d.get("passport"))
    prefix = to_str(d.get("prefix"))
    first = to_str(d.get("first"))
    last = to_str(d.get("last"))
    suffix = to_str(d.get("suffix"))
    maiden = to_str(d.get("maiden"))
    marital = to_str(d.get("marital"))
    race = to_str(d.get("race"))
    ethnicity = to_str(d.get("ethnicity"))
    gender = to_str(d.get("gender"))
    birthplace = to_str(d.get("birthplace"))
    address = to_str(d.get("address"))
    city = to_str(d.get("city"))
    state = to_str(d.get("state"))
    county = to_str(d.get("county"))
    zip_code = to_str(d.get("zip"))
    lat = d.get("lat")
    lon = d.get("lon")

    # Build base resource
    resource: dict[str, Any] = {"resourceType": "Patient"}

    # Only set id if present
    if patient_id:
        resource["id"] = patient_id

    # Set identifiers
    identifiers: list[dict[str, Any]] = []

    # Medical Record Number (Id)
    if patient_id:
        identifiers.append(
            {"system": "urn:oid:2.16.840.1.113883.19.5", "value": patient_id}
        )

    # SSN
    if ssn:
        identifiers.append(
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "SS",
                            "display": "Social Security Number",
                        }
                    ]
                },
                "value": ssn,
            }
        )

    # Driver's License
    if drivers:
        identifiers.append(
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "DL",
                            "display": "Driver's License",
                        }
                    ]
                },
                "value": drivers,
            }
        )

    # Passport
    if passport:
        identifiers.append(
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PPN",
                            "display": "Passport Number",
                        }
                    ]
                },
                "value": passport,
            }
        )

    if identifiers:
        resource["identifier"] = identifiers

    # Set birthDate
    if birthdate:
        birth_date = format_date(birthdate)
        if birth_date:
            resource["birthDate"] = birth_date

    # Set deceased
    if deathdate:
        death_date = format_datetime(deathdate)
        if death_date:
            resource["deceasedDateTime"] = death_date
    else:
        resource["deceasedBoolean"] = False

    # Set name
    names = []

    # Primary name (official)
    if first or last or prefix or suffix:
        name: dict[str, Any] = {"use": "official"}
        if prefix:
            name["prefix"] = [prefix]
        if first:
            name["given"] = [first]
        if last:
            name["family"] = last
        if suffix:
            name["suffix"] = [suffix]
        names.append(name)

    # Maiden name (if present)
    if maiden:
        maiden_name: dict[str, Any] = {"use": "maiden", "family": maiden}
        names.append(maiden_name)

    if names:
        resource["name"] = names

    # Set gender
    mapped_gender = map_gender(gender)
    if mapped_gender:
        resource["gender"] = mapped_gender

    # Set maritalStatus
    marital_status = map_marital_status(marital)
    if marital_status:
        resource["maritalStatus"] = marital_status

    # Set extensions (Race, Ethnicity, Birthplace)
    extensions: list[dict[str, Any]] = []

    # Race extension (US Core)
    if race:
        extensions.append(
            {
                "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                "extension": [{"url": "text", "valueString": race}],
            }
        )

    # Ethnicity extension (US Core)
    if ethnicity:
        extensions.append(
            {
                "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
                "extension": [{"url": "text", "valueString": ethnicity}],
            }
        )

    # Birthplace extension
    if birthplace:
        extensions.append(
            {
                "url": "http://hl7.org/fhir/StructureDefinition/birthPlace",
                "valueAddress": {"text": birthplace},
            }
        )

    if extensions:
        resource["extension"] = extensions

    # Set address
    if (
        address
        or city
        or state
        or county
        or zip_code
        or (lat is not None and lon is not None)
    ):
        address_obj: dict[str, Any] = {"use": "home"}

        if address:
            address_obj["line"] = [address]
        if city:
            address_obj["city"] = city
        if state:
            address_obj["state"] = state
        if county:
            address_obj["district"] = county
        if zip_code:
            address_obj["postalCode"] = zip_code

        # Geolocation extension
        if lat is not None and lon is not None:
            address_obj.setdefault("extension", []).append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                    "extension": [
                        {"url": "latitude", "valueDecimal": float(lat)},
                        {"url": "longitude", "valueDecimal": float(lon)},
                    ],
                }
            )

        resource["address"] = [address_obj]

    return Patient(**resource)
