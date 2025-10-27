#!/usr/bin/env python3
"""
Export parts list to CSV for manual review in Google Sheets

Usage:
  python3 export_parts_to_csv.py [section_code]

Examples:
  python3 export_parts_to_csv.py 10      # Export section 10
  python3 export_parts_to_csv.py 11      # Export section 11
  python3 export_parts_to_csv.py         # Export section 11 (default)
"""

import json
import csv
import sys

def export_parts_to_csv(section_code="11"):
    """Export parts list data to CSV"""

    # Construct filenames based on section code
    section = "electrical"
    pdf_name = f"{section_code}_parts.pdf"
    output_file = f"section_{section_code}_parts_review.csv"

    # Load registry
    print(f"Loading schematic_registry.json...")
    with open("schematic_registry.json", 'r') as f:
        registry = json.load(f)

    if "parts_lists" not in registry:
        print("✗ No parts lists found in registry")
        return

    if section not in registry["parts_lists"]:
        print(f"✗ Section '{section}' not found in parts lists")
        return

    if pdf_name not in registry["parts_lists"][section]:
        print(f"✗ Parts list '{pdf_name}' not found in section '{section}'")
        print(f"\nAvailable parts lists in {section}:")
        for name in registry["parts_lists"][section].keys():
            print(f"  - {name}")
        return

    parts = registry["parts_lists"][section][pdf_name].get("parts", [])

    if not parts:
        print("✗ No parts found")
        return

    print(f"Found {len(parts)} parts in section {section_code}")

    # Write to CSV
    print(f"Exporting to {output_file}...")

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['symbol', 'quantity', 'description', 'identification',
                     'sheet_section', 'location', 'remarks']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for part in parts:
            writer.writerow({
                'symbol': part.get('symbol', ''),
                'quantity': part.get('quantity', ''),
                'description': part.get('description', ''),
                'identification': part.get('identification', ''),
                'sheet_section': part.get('sheet_section', ''),
                'location': part.get('location', ''),
                'remarks': part.get('remarks', '')
            })

    print(f"✓ Exported {len(parts)} parts to {output_file}")
    print(f"\nNext steps:")
    print(f"1. Upload {output_file} to Google Sheets")
    print(f"2. Review and correct any errors")
    print(f"3. Download corrected sheet as CSV")
    print(f"4. Run: python3 import_parts_from_csv.py <corrected.csv>")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        section_code = sys.argv[1]
        export_parts_to_csv(section_code=section_code)
    else:
        export_parts_to_csv()
