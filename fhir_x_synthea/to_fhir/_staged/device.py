"""Synthea Device → FHIR R4 Device"""

from fhir.resources.device import Device
from synthea_pydantic import Device as SyntheaDevice

from ..chidian_ext import grab, mapper, to_dict
from ..fhir_lib import format_datetime, period


def _resource_id(d: dict) -> str:
    """Generate deterministic resource ID."""
    patient_id = grab(d, "patient") or ""
    start = grab(d, "start") or ""
    code = grab(d, "code") or ""
    return f"{patient_id}-{start}-{code}".replace(" ", "-").replace(":", "-")


def _device_period_extension(d: dict):
    """Build device-use-period extension."""
    start = grab(d, "start", apply=format_datetime)
    stop = grab(d, "stop", apply=format_datetime)
    p = period(start, stop)
    if not p:
        return None
    return {
        "url": "http://synthea.tools/fhir/StructureDefinition/device-use-period",
        "valuePeriod": p,
    }


def _encounter_extension(encounter_id: str | None):
    """Build encounter reference extension."""
    if not encounter_id:
        return None
    return {
        "url": "http://hl7.org/fhir/StructureDefinition/resource-encounter",
        "valueReference": {"reference": f"Encounter/{encounter_id}"},
    }


def _patient_extension(patient_ref: str | None):
    """Build patient reference extension."""
    if not patient_ref:
        return None
    return {
        "url": "http://hl7.org/fhir/StructureDefinition/resource-patient",
        "valueReference": {"reference": patient_ref},
    }


def _device_type(code: str | None, description: str | None) -> list | None:
    """Build device type CodeableConcept."""
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
    return [result] if result else None


def _udi_carrier(udi: str | None):
    """Build UDI carrier."""
    if not udi:
        return None
    return [{"deviceIdentifier": udi, "carrierHRF": udi}]


@mapper
def _to_fhir_device(d: dict, patient_ref: str | None = None):
    """Core mapping from dict to FHIR Device structure."""
    patient_id = grab(d, "patient")
    stop = grab(d, "stop")

    # Build extensions list
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )
    extensions = [
        e
        for e in [
            _device_period_extension(d),
            _encounter_extension(grab(d, "encounter")),
            _patient_extension(effective_patient_ref),
        ]
        if e
    ]

    return {
        "resourceType": "Device",
        "id": _resource_id(d),
        "status": "inactive" if stop else "active",
        "extension": extensions if extensions else None,
        "type": _device_type(grab(d, "code"), grab(d, "description")),
        "udiCarrier": _udi_carrier(grab(d, "udi")),
    }


def convert(src: SyntheaDevice, *, patient_ref: str | None = None) -> Device:
    """Convert Synthea Device to FHIR R4 Device.

    Args:
        src: Synthea Device model
        patient_ref: Optional patient reference (e.g., "Patient/123")

    Returns:
        FHIR R4 Device resource
    """
    return Device(**_to_fhir_device(to_dict(src), patient_ref))
