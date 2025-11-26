"""
Mapping function for converting FHIR Organization resources (payers) to Synthea payers.csv rows.
"""

from typing import Any

from ..synthea_csv_lib import extract_nested_extension


def map_fhir_payer_to_csv(fhir_resource: dict[str, Any]) -> dict[str, Any]:
    """
    Map a FHIR R4 Organization resource representing a payer to a Synthea payers.csv row.

    Args:
        fhir_resource: Dictionary representing a FHIR Organization resource

    Returns:
        Dictionary with CSV column names as keys
    """

    # Helper to extract extension value
    def extract_extension_code(
        fhir_resource: dict[str, Any], extension_url: str
    ) -> str:
        extensions = fhir_resource.get("extension", [])
        for ext in extensions:
            if ext.get("url") == extension_url:
                value = ext.get("valueCode")
                if value:
                    return value
        return ""

    # Initialize CSV row
    csv_row: dict[str, str] = {
        "Id": "",
        "Name": "",
        "Ownership": "",
        "Address": "",
        "City": "",
        "State_Headquartered": "",
        "Zip": "",
        "Phone": "",
        "Amount_Covered": "",
        "Amount_Uncovered": "",
        "Revenue": "",
        "Covered_Encounters": "",
        "Uncovered_Encounters": "",
        "Covered_Medications": "",
        "Uncovered_Medications": "",
        "Covered_Procedures": "",
        "Uncovered_Procedures": "",
        "Covered_Immunizations": "",
        "Uncovered_Immunizations": "",
        "Unique_Customers": "",
        "QOLS_Avg": "",
        "Member_Months": "",
    }

    # Extract Id
    resource_id = fhir_resource.get("id", "")
    if resource_id:
        csv_row["Id"] = resource_id

    # Extract Name
    name = fhir_resource.get("name", "")
    if name:
        csv_row["Name"] = name

    # Extract Ownership from extension
    csv_row["Ownership"] = extract_extension_code(
        fhir_resource,
        "http://synthea.mitre.org/fhir/StructureDefinition/payer-ownership",
    )

    # Extract Address components
    addresses = fhir_resource.get("address", [])
    if addresses:
        first_address = addresses[0]

        lines = first_address.get("line", [])
        if lines:
            csv_row["Address"] = lines[0]

        csv_row["City"] = first_address.get("city", "")
        csv_row["State_Headquartered"] = first_address.get("state", "")
        csv_row["Zip"] = first_address.get("postalCode", "")

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

    # Extract payer-stats extension nested values
    stats_extension_url = (
        "http://synthea.mitre.org/fhir/StructureDefinition/payer-stats"
    )

    csv_row["Amount_Covered"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "amountCovered", "valueDecimal"
    )
    csv_row["Amount_Uncovered"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "amountUncovered", "valueDecimal"
    )
    csv_row["Revenue"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "revenue", "valueDecimal"
    )
    csv_row["Covered_Encounters"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "coveredEncounters", "valueInteger"
    )
    csv_row["Uncovered_Encounters"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "uncoveredEncounters", "valueInteger"
    )
    csv_row["Covered_Medications"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "coveredMedications", "valueInteger"
    )
    csv_row["Uncovered_Medications"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "uncoveredMedications", "valueInteger"
    )
    csv_row["Covered_Procedures"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "coveredProcedures", "valueInteger"
    )
    csv_row["Uncovered_Procedures"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "uncoveredProcedures", "valueInteger"
    )
    csv_row["Covered_Immunizations"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "coveredImmunizations", "valueInteger"
    )
    csv_row["Uncovered_Immunizations"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "uncoveredImmunizations", "valueInteger"
    )
    csv_row["Unique_Customers"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "uniqueCustomers", "valueInteger"
    )
    csv_row["QOLS_Avg"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "qolsAvg", "valueDecimal"
    )
    csv_row["Member_Months"] = extract_nested_extension(
        fhir_resource, stats_extension_url, "memberMonths", "valueInteger"
    )

    return csv_row
