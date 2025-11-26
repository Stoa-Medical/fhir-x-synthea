"""FHIR R4 Patient → Synthea Patient"""

import logging
from datetime import date
from decimal import Decimal

from fhir.resources.patient import Patient
from synthea_pydantic import Patient as SyntheaPatient

from ..chidian_ext import (
    grab,
    mapper,
    parse_date,
    to_dict,
)
from ..synthea_lib import default, map_fhir_gender, map_fhir_marital

logger = logging.getLogger(__name__)


def _extract_identifier_value(identifiers: list, type_code: str) -> str:
    """Extract identifier value by type code (SS, DL, PPN)."""
    for ident in identifiers or []:
        codings = (ident.get("type") or {}).get("coding", [])
        for coding in codings:
            if coding.get("code") == type_code:
                return ident.get("value", "")
    return ""


def _extract_name_part(names: list, use: str, part: str) -> str:
    """Extract name part (given, family, prefix, suffix) by use."""
    if not names:
        return ""

    # Find name with matching use, or fall back to first name
    target_name = next(
        (n for n in names if n.get("use") == use), names[0] if names else None
    )
    if not target_name:
        return ""

    if part == "given":
        given = target_name.get("given", [])
        return given[0] if given else ""
    elif part == "family":
        return target_name.get("family", "")
    elif part == "prefix":
        prefix = target_name.get("prefix", [])
        return prefix[0] if prefix else ""
    elif part == "suffix":
        suffix = target_name.get("suffix", [])
        return suffix[0] if suffix else ""
    return ""


def _extract_maiden_name(names: list) -> str:
    """Extract maiden name from name list."""
    for name in names or []:
        if name.get("use") == "maiden":
            return name.get("family", "")
    return ""


def _extract_address_part(addresses: list, part: str) -> str:
    """Extract address part from first address."""
    if not addresses:
        return ""
    addr = addresses[0]

    if part == "line":
        lines = addr.get("line", [])
        return lines[0] if lines else ""
    elif part == "city":
        return addr.get("city", "")
    elif part == "state":
        return addr.get("state", "")
    elif part == "district":
        return addr.get("district", "")
    elif part == "postalCode":
        return addr.get("postalCode", "")
    return ""


def _extract_geolocation(addresses: list) -> tuple[Decimal | None, Decimal | None]:
    """Extract lat/lon from address geolocation extension."""
    if not addresses:
        return None, None
    addr = addresses[0]
    extensions = addr.get("extension", [])
    lat, lon = None, None
    for ext in extensions:
        if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/geolocation":
            for n in ext.get("extension", []):
                if n.get("url") == "latitude" and n.get("valueDecimal") is not None:
                    lat = Decimal(str(n["valueDecimal"]))
                elif n.get("url") == "longitude" and n.get("valueDecimal") is not None:
                    lon = Decimal(str(n["valueDecimal"]))
    return lat, lon


def _extract_extension_text(d: dict, url: str) -> str:
    """Extract text value from a US Core style extension."""
    extensions = grab(d, "extension") or []
    for ext in extensions:
        if ext.get("url") == url:
            # Check for nested text extension
            for n in ext.get("extension", []):
                if n.get("url") == "text":
                    return n.get("valueString", "")
            return ext.get("valueString", "")
    return ""


def _extract_birthplace(d: dict) -> str:
    """Extract birthplace from extension."""
    extensions = grab(d, "extension") or []
    for ext in extensions:
        if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/birthPlace":
            addr = ext.get("valueAddress", {})
            return addr.get("text", "")
    return ""


@mapper(remove_empty=False)
def _to_synthea_patient(d: dict):
    """Core mapping from dict to Synthea Patient structure."""
    identifiers = grab(d, "identifier") or []
    names = grab(d, "name") or []
    addresses = grab(d, "address") or []

    # Parse birthdate
    birthdate_raw = grab(d, "birthDate")
    birthdate = None
    if birthdate_raw:
        if isinstance(birthdate_raw, date):
            birthdate = birthdate_raw
        else:
            parsed = parse_date({"bd": birthdate_raw}, "bd")
            if parsed:
                birthdate = date.fromisoformat(parsed)

    # Parse deathdate
    deathdate = None
    deceased_dt = grab(d, "deceasedDateTime")
    if deceased_dt:
        if isinstance(deceased_dt, date):
            deathdate = deceased_dt
        else:
            parsed = parse_date({"dd": deceased_dt}, "dd")
            if parsed:
                deathdate = date.fromisoformat(parsed)

    lat, lon = _extract_geolocation(addresses)

    # Log lossy conversions
    if len(names) > 2:
        logger.warning(
            "Patient has %d names; only official and maiden preserved", len(names)
        )
    if len(addresses) > 1:
        logger.warning("Patient has %d addresses; only first preserved", len(addresses))

    return {
        "id": grab(d, "id") or None,
        "birthdate": birthdate,
        "deathdate": deathdate,
        "ssn": default(_extract_identifier_value(identifiers, "SS"), "000-00-0000"),
        "drivers": _extract_identifier_value(identifiers, "DL") or None,
        "passport": _extract_identifier_value(identifiers, "PPN") or None,
        "prefix": _extract_name_part(names, "official", "prefix") or None,
        "first": default(_extract_name_part(names, "official", "given"), "Unknown"),
        "last": default(_extract_name_part(names, "official", "family"), "Unknown"),
        "suffix": _extract_name_part(names, "official", "suffix") or None,
        "maiden": _extract_maiden_name(names) or None,
        "marital": map_fhir_marital(grab(d, "maritalStatus")),
        "race": default(
            _extract_extension_text(
                d, "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"
            ),
            "unknown",
        ),
        "ethnicity": default(
            _extract_extension_text(
                d, "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"
            ),
            "unknown",
        ),
        "gender": map_fhir_gender(grab(d, "gender")),
        "birthplace": default(_extract_birthplace(d), "Unknown"),
        "address": default(_extract_address_part(addresses, "line"), "Unknown"),
        "city": default(_extract_address_part(addresses, "city"), "Unknown"),
        "state": default(_extract_address_part(addresses, "state"), "Unknown"),
        "county": _extract_address_part(addresses, "district") or None,
        "zip": _extract_address_part(addresses, "postalCode") or None,
        "lat": lat,
        "lon": lon,
        "healthcare_expenses": Decimal("0"),
        "healthcare_coverage": Decimal("0"),
    }


def convert(src: Patient) -> SyntheaPatient:
    """Convert FHIR R4 Patient to Synthea Patient.

    Args:
        src: FHIR R4 Patient resource

    Returns:
        Synthea Patient model
    """
    return SyntheaPatient(**_to_synthea_patient(to_dict(src)))
