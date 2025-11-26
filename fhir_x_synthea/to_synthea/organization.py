"""
Mapping function for converting FHIR Organization resources to Synthea organizations.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import extract_nested_extension


def map_fhir_organization_to_csv(fhir_resource: dict[str, Any]) -> dict[str, Any]:
    """
    Map a FHIR R4 Organization resource to a Synthea organizations.csv row.

    Args:
        fhir_resource: Dictionary representing a FHIR Organization resource

    Returns:
        Dictionary with CSV column names as keys (Id, Name, Address, etc.)
    """

    # Helper to extract geolocation from address extension
    def extract_geolocation(address: dict[str, Any] | None) -> tuple[str, str]:
        if not address:
            return ("", "")

        extensions = address.get("extension", [])
        for ext in extensions:
            if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/geolocation":
                sub_extensions = ext.get("extension", [])
                lat = ""
                lon = ""
                for sub_ext in sub_extensions:
                    url = sub_ext.get("url", "")
                    value = sub_ext.get("valueDecimal")
                    if value is not None:
                        if url == "latitude":
                            lat = str(value)
                        elif url == "longitude":
                            lon = str(value)
                return (lat, lon)
        return ("", "")

    # Initialize CSV row
    csv_row: dict[str, str] = {
        "Id": "",
        "Name": "",
        "Address": "",
        "City": "",
        "State": "",
        "Zip": "",
        "Lat": "",
        "Lon": "",
        "Phone": "",
        "Revenue": "",
        "Utilization": "",
    }

    # Extract Id
    resource_id = fhir_resource.get("id", "")
    if resource_id:
        csv_row["Id"] = resource_id

    # Extract Name
    name = fhir_resource.get("name", "")
    if name:
        csv_row["Name"] = name

    # Extract Address components
    addresses = fhir_resource.get("address", [])
    if addresses:
        first_address = addresses[0]

        # Address line
        lines = first_address.get("line", [])
        if lines:
            csv_row["Address"] = lines[0]

        csv_row["City"] = first_address.get("city", "")
        csv_row["State"] = first_address.get("state", "")
        csv_row["Zip"] = first_address.get("postalCode", "")

        # Geolocation
        lat, lon = extract_geolocation(first_address)
        csv_row["Lat"] = lat
        csv_row["Lon"] = lon

    # Extract Phone numbers (join with ; )
    telecom = fhir_resource.get("telecom", [])
    phones = []
    for contact in telecom:
        if contact.get("system") == "phone":
            value = contact.get("value", "")
            if value:
                phones.append(value)

    if phones:
        csv_row["Phone"] = "; ".join(phones)

    # Extract organization stats extensions
    csv_row["Revenue"] = extract_nested_extension(
        fhir_resource,
        "http://synthea.mitre.org/fhir/StructureDefinition/organization-stats",
        "revenue",
        "valueDecimal",
    )
    csv_row["Utilization"] = extract_nested_extension(
        fhir_resource,
        "http://synthea.mitre.org/fhir/StructureDefinition/organization-stats",
        "utilization",
        "valueInteger",
    )

    return csv_row
