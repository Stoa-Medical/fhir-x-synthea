"""FHIR R4 Patient → Synthea Patient"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from fhir.resources.patient import Patient
from synthea_pydantic import Patient as SyntheaPatient

from ..synthea_csv_lib import parse_datetime_to_date

logger = logging.getLogger(__name__)


def _extract_identifier_value(identifiers: list[dict[str, Any]], type_code: str) -> str:
    """Extract identifier value by type code (SS, DL, PPN)."""
    if not identifiers:
        return ""
    for ident in identifiers:
        ident_type = ident.get("type", {})
        codings = ident_type.get("coding", [])
        for coding in codings:
            if coding.get("code") == type_code:
                return ident.get("value", "")
    return ""


def _extract_name_part(names: list[dict[str, Any]], use: str, part: str) -> str:
    """Extract name part (given, family, prefix, suffix) by use."""
    if not names:
        return ""
    # Find name with matching use, or fall back to first name
    target_name = None
    for name in names:
        if name.get("use") == use:
            target_name = name
            break
    if not target_name and names:
        target_name = names[0]

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


def _extract_maiden_name(names: list[dict[str, Any]]) -> str:
    """Extract maiden name from name list."""
    if not names:
        return ""
    for name in names:
        if name.get("use") == "maiden":
            return name.get("family", "")
    return ""


def _extract_address_part(addresses: list[dict[str, Any]], part: str) -> str:
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


def _extract_geolocation(
    addresses: list[dict[str, Any]],
) -> tuple[Decimal | None, Decimal | None]:
    """Extract lat/lon from address geolocation extension."""
    if not addresses:
        return None, None
    addr = addresses[0]
    extensions = addr.get("extension", [])
    lat, lon = None, None
    for ext in extensions:
        if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/geolocation":
            nested = ext.get("extension", [])
            for n in nested:
                if n.get("url") == "latitude":
                    lat = n.get("valueDecimal")
                elif n.get("url") == "longitude":
                    lon = n.get("valueDecimal")
    return lat, lon


def _map_fhir_gender(gender: str | None) -> str:
    """Map FHIR gender to Synthea gender code."""
    if not gender:
        return "M"  # Default
    mapping = {"male": "M", "female": "F"}
    return mapping.get(gender.lower(), "M")


def _map_fhir_marital(marital_status: dict[str, Any] | None) -> str | None:
    """Map FHIR marital status to Synthea code."""
    if not marital_status:
        return None
    codings = marital_status.get("coding", [])
    for coding in codings:
        code = coding.get("code", "")
        if code in ("M", "S", "D", "W"):
            return code
    return None


def _extract_extension_text(fhir_resource: dict[str, Any], url: str) -> str:
    """Extract text value from a US Core style extension."""
    extensions = fhir_resource.get("extension", [])
    for ext in extensions:
        if ext.get("url") == url:
            # Check for nested text extension
            nested = ext.get("extension", [])
            for n in nested:
                if n.get("url") == "text":
                    return n.get("valueString", "")
            # Check for direct valueString
            return ext.get("valueString", "")
    return ""


def _extract_birthplace(fhir_resource: dict[str, Any]) -> str:
    """Extract birthplace from extension."""
    extensions = fhir_resource.get("extension", [])
    for ext in extensions:
        if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/birthPlace":
            addr = ext.get("valueAddress", {})
            return addr.get("text", "")
    return ""


def convert(src: Patient) -> SyntheaPatient:
    """Convert FHIR R4 Patient to Synthea Patient.

    Args:
        src: FHIR R4 Patient resource

    Returns:
        Synthea Patient model

    Note:
        Some FHIR fields may not be representable in Synthea format.
        Required Synthea fields without FHIR equivalents use defaults.
        Check logs for warnings about dropped or defaulted data.
    """
    fhir_resource = src.model_dump(exclude_none=True)

    # Extract ID
    patient_id = fhir_resource.get("id", "")

    # Extract identifiers
    identifiers = fhir_resource.get("identifier", [])
    ssn = _extract_identifier_value(identifiers, "SS")
    drivers = _extract_identifier_value(identifiers, "DL")
    passport = _extract_identifier_value(identifiers, "PPN")

    # Extract names
    names = fhir_resource.get("name", [])
    first = _extract_name_part(names, "official", "given")
    last = _extract_name_part(names, "official", "family")
    prefix = _extract_name_part(names, "official", "prefix")
    suffix = _extract_name_part(names, "official", "suffix")
    maiden = _extract_maiden_name(names)

    # Extract dates
    birthdate_raw = fhir_resource.get("birthDate")
    birthdate = None
    if birthdate_raw:
        if isinstance(birthdate_raw, date):
            birthdate = birthdate_raw
        else:
            parsed = parse_datetime_to_date(str(birthdate_raw))
            if parsed:
                birthdate = date.fromisoformat(parsed)

    deathdate = None
    deceased_dt = fhir_resource.get("deceasedDateTime")
    if deceased_dt:
        if isinstance(deceased_dt, date):
            deathdate = deceased_dt
        else:
            parsed = parse_datetime_to_date(str(deceased_dt))
            if parsed:
                deathdate = date.fromisoformat(parsed)

    # Extract gender
    gender = _map_fhir_gender(fhir_resource.get("gender"))

    # Extract marital status
    marital = _map_fhir_marital(fhir_resource.get("maritalStatus"))

    # Extract race and ethnicity from US Core extensions
    race = _extract_extension_text(
        fhir_resource, "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"
    )
    ethnicity = _extract_extension_text(
        fhir_resource,
        "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
    )

    # Extract birthplace
    birthplace = _extract_birthplace(fhir_resource)

    # Extract address
    addresses = fhir_resource.get("address", [])
    address = _extract_address_part(addresses, "line")
    city = _extract_address_part(addresses, "city")
    state = _extract_address_part(addresses, "state")
    county = _extract_address_part(addresses, "district")
    zip_code = _extract_address_part(addresses, "postalCode")
    lat, lon = _extract_geolocation(addresses)

    # Log lossy conversions
    if len(names) > 2:
        logger.warning(
            "Patient %s has %d names; only official and maiden preserved",
            src.id,
            len(names),
        )
    if len(addresses) > 1:
        logger.warning(
            "Patient %s has %d addresses; only first preserved",
            src.id,
            len(addresses),
        )

    # Build Synthea Patient with required field defaults
    return SyntheaPatient(
        id=patient_id or None,
        birthdate=birthdate,
        deathdate=deathdate,
        ssn=ssn or "000-00-0000",  # Default for required field
        drivers=drivers or None,
        passport=passport or None,
        prefix=prefix or None,
        first=first or "Unknown",  # Default for required field
        last=last or "Unknown",  # Default for required field
        suffix=suffix or None,
        maiden=maiden or None,
        marital=marital,
        race=race or "unknown",  # Default for required field
        ethnicity=ethnicity or "unknown",  # Default for required field
        gender=gender,
        birthplace=birthplace or "Unknown",  # Default for required field
        address=address or "Unknown",  # Default for required field
        city=city or "Unknown",  # Default for required field
        state=state or "Unknown",  # Default for required field
        county=county or None,
        zip=zip_code or None,
        lat=Decimal(str(lat)) if lat is not None else None,
        lon=Decimal(str(lon)) if lon is not None else None,
        healthcare_expenses=Decimal("0"),  # Not in FHIR Patient
        healthcare_coverage=Decimal("0"),  # Not in FHIR Patient
    )
