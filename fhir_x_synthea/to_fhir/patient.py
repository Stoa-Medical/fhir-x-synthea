"""
Mapping function for converting Synthea patients.csv rows to FHIR Patient resources.
"""

from typing import Any

from ..fhir_lib import (
    format_date,
    format_datetime,
    map_gender,
    map_marital_status,
)


def map_patient(csv_row: dict[str, Any]) -> dict[str, Any]:
    """
    Map a Synthea patients.csv row to a FHIR R4 Patient resource.

    Args:
        csv_row: Dictionary with keys like Id, BIRTHDATE, DEATHDATE, SSN, DRIVERS,
                PASSPORT, PREFIX, FIRST, LAST, SUFFIX, MAIDEN, MARITAL, RACE,
                ETHNICITY, GENDER, BIRTHPLACE, ADDRESS, CITY, STATE, COUNTY, ZIP, LAT, LON

    Returns:
        Dictionary representing a FHIR Patient resource
    """

    # Extract and process fields
    patient_id = csv_row.get("Id", "").strip() if csv_row.get("Id") else ""
    birthdate = csv_row.get("BIRTHDATE", "").strip() if csv_row.get("BIRTHDATE") else ""
    deathdate = csv_row.get("DEATHDATE", "").strip() if csv_row.get("DEATHDATE") else ""
    ssn = csv_row.get("SSN", "").strip() if csv_row.get("SSN") else ""
    drivers = csv_row.get("DRIVERS", "").strip() if csv_row.get("DRIVERS") else ""
    passport = csv_row.get("PASSPORT", "").strip() if csv_row.get("PASSPORT") else ""
    prefix = csv_row.get("PREFIX", "").strip() if csv_row.get("PREFIX") else ""
    first = csv_row.get("FIRST", "").strip() if csv_row.get("FIRST") else ""
    last = csv_row.get("LAST", "").strip() if csv_row.get("LAST") else ""
    suffix = csv_row.get("SUFFIX", "").strip() if csv_row.get("SUFFIX") else ""
    maiden = csv_row.get("MAIDEN", "").strip() if csv_row.get("MAIDEN") else ""
    marital = csv_row.get("MARITAL", "").strip() if csv_row.get("MARITAL") else ""
    race = csv_row.get("RACE", "").strip() if csv_row.get("RACE") else ""
    ethnicity = csv_row.get("ETHNICITY", "").strip() if csv_row.get("ETHNICITY") else ""
    gender = csv_row.get("GENDER", "").strip() if csv_row.get("GENDER") else ""
    birthplace = (
        csv_row.get("BIRTHPLACE", "").strip() if csv_row.get("BIRTHPLACE") else ""
    )
    address = csv_row.get("ADDRESS", "").strip() if csv_row.get("ADDRESS") else ""
    city = csv_row.get("CITY", "").strip() if csv_row.get("CITY") else ""
    state = csv_row.get("STATE", "").strip() if csv_row.get("STATE") else ""
    county = csv_row.get("COUNTY", "").strip() if csv_row.get("COUNTY") else ""
    zip_code = csv_row.get("ZIP", "").strip() if csv_row.get("ZIP") else ""
    lat_str = csv_row.get("LAT", "").strip() if csv_row.get("LAT") else ""
    lon_str = csv_row.get("LON", "").strip() if csv_row.get("LON") else ""

    # Parse coordinates
    lat = None
    lon = None
    if lat_str:
        try:
            lat = float(lat_str)
        except (ValueError, TypeError):
            pass
    if lon_str:
        try:
            lon = float(lon_str)
        except (ValueError, TypeError):
            pass

    # Build base resource
    resource: dict[str, Any] = {
        "resourceType": "Patient",
        "id": patient_id if patient_id else "",
    }

    # Set identifiers
    identifiers = []

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
                        {"url": "latitude", "valueDecimal": lat},
                        {"url": "longitude", "valueDecimal": lon},
                    ],
                }
            )

        resource["address"] = [address_obj]

    return resource
