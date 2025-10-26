#!/usr/bin/env python3
"""
Fix OCR errors in parts list sheet references
Converts =t1/ to =11/ (and other common OCR errors)
"""

import json
import sys

def fix_sheet_references(registry_file="schematic_registry.json"):
    """Fix OCR errors in sheet references"""

    # Load registry
    print(f"Loading {registry_file}...")
    with open(registry_file, 'r') as f:
        registry = json.load(f)

    if "parts_lists" not in registry:
        print("No parts_lists found in registry")
        return

    fixes = {
        "=t1/": "=11/",   # t1 -> 11 (most common)
        "=l1/": "=11/",   # l1 -> 11
        "=1t/": "=11/",   # 1t -> 11
        "=II/": "=11/",   # II -> 11
    }

    total_fixed = 0

    # Process each section's parts lists
    for section, parts_lists in registry["parts_lists"].items():
        for pdf_name, parts_info in parts_lists.items():
            parts = parts_info.get("parts", [])

            for part in parts:
                sheet_ref = part.get("sheet_section", "")

                # Try each fix pattern
                for old, new in fixes.items():
                    if sheet_ref.startswith(old):
                        part["sheet_section"] = sheet_ref.replace(old, new, 1)
                        total_fixed += 1
                        print(f"  Fixed: {sheet_ref} -> {part['sheet_section']} ({part.get('symbol', 'N/A')})")
                        break

    if total_fixed > 0:
        # Save updated registry
        print(f"\nSaving changes...")
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        print(f"✓ Fixed {total_fixed} sheet references in {registry_file}")
    else:
        print("No fixes needed - all sheet references look good!")

if __name__ == "__main__":
    fix_sheet_references()
