import json
import os
from pathlib import Path

from chidian import Table

# Setup paths
data_dir = Path("./fhir")
output_dir = Path("./fhir/by_resource")
output_dir.mkdir(parents=True, exist_ok=True)

# Process each JSON file
for json_file in data_dir.glob("*.json"):
    # Load bundle as Table
    with open(json_file) as f:
        bundle = json.load(f)

    # Extract all resources from entries
    t = Table([bundle])
    resources = t.extract("entry[*].resource")

    # Group by resourceType
    grouped = resources.group_by("resourceType")

    # Append to respective JSONL files
    for resource_type, table in grouped.items():
        output_file = output_dir / f"{resource_type}.jsonl"

        # Append each resource as a JSON line
        with open(output_file, "a") as fo:
            for row in table:
                fo.write(json.dumps(row))
                fo.write(os.linesep)
