# For each csv file in ./synthea_csv
# For each row in the csv file
# Identify the patient id
# Lookup the patient id in ./fhir directory by finding the json file with the same id stringmatch
# If not found, return an error and log to console in red (but keep going)
# If found, add row to a CSV file in ./synthea_csv/by_patient/{same_file_name_as_json_file}.csv

import json
import os
from pathlib import Path

from chidian import Table


def organize_csv_by_patient():
    synthea_csv_dir = Path("./synthea_csv")
    fhir_dir = Path("./fhir")
    output_dir = synthea_csv_dir / "by_patient"

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each CSV file in synthea_csv
    for csv_file in synthea_csv_dir.glob("*.csv"):
        print(f"Processing {csv_file.name}...")

        # Load CSV into Table
        table = Table.from_csv(csv_file)

        # Group rows by patient_id
        patient_groups = {}
        no_match_rows = []

        for row in table:
            # Add the csv file name in the row
            row["csv_file"] = csv_file.name

            # Identify patient id (assuming column name is 'PATIENT' or 'patient_id')
            patient_id = (
                row.get("PATIENT") or row.get("patient_id") or row.get("Patient")
            )

            if not patient_id:
                print(f"⚠️ Warning: Row without patient ID in {csv_file.name}")
                no_match_rows.append(row)
                continue

            # Search for JSON file containing the patient ID in filename
            matching_files = list(fhir_dir.glob(f"*{patient_id}*.json"))

            if not matching_files:
                print(f"❌ Error: No FHIR file found for patient {patient_id}")
                no_match_rows.append(row)
                continue

            # Use first matching file
            json_file = matching_files[0]

            # Add row to appropriate patient group (use json filename without extension as key)
            key = json_file.stem
            if key not in patient_groups:
                patient_groups[key] = []
            patient_groups[key].append(row)

        # Write grouped data to JSONL files
        for json_filename, rows in patient_groups.items():
            output_file = output_dir / f"{json_filename}.jsonl"

            # Append rows as JSONL
            with open(output_file, "a", encoding="utf-8") as f:
                for row in rows:
                    f.write(json.dumps(row))
                    f.write(os.linesep)

            if output_file.exists():
                print(f"  📝 Appended {len(rows)} rows to {output_file.name}")

        # Write unmatched rows to _noidmatch.jsonl
        if no_match_rows:
            no_match_file = output_dir / "_noidmatch.jsonl"
            with open(no_match_file, "a", encoding="utf-8") as fo:
                for row in no_match_rows:
                    fo.write(json.dumps(row))
                    fo.write(os.linesep)

            print(
                f"  ⚠️ Appended {len(no_match_rows)} unmatched rows to {no_match_file.name}"
            )


if __name__ == "__main__":
    organize_csv_by_patient()
