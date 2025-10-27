#!/usr/bin/env python3
"""
Validate parts list against schematic index
Cross-checks if parts appear on their claimed sheets
"""

import json
import sys

def validate_parts(section_code=None):
    """Validate parts against schematic index"""

    # Load registry
    print(f"Loading schematic_registry.json...")
    with open("schematic_registry.json", 'r') as f:
        registry = json.load(f)

    if "parts_lists" not in registry:
        print("✗ No parts lists found")
        return

    if "sections" not in registry:
        print("✗ No schematic sections found")
        return

    # Get all parts lists or specific section
    sections_to_check = []
    if section_code:
        sections_to_check = [section_code]
    else:
        # Check all sections
        for section in registry["parts_lists"].get("electrical", {}).keys():
            code = section.replace("_parts.pdf", "")
            sections_to_check.append(code)

    total_parts = 0
    found_on_sheet = 0
    missing_from_sheet = 0
    sheet_not_indexed = 0
    has_connections = 0

    print(f"\n{'='*80}")
    print(f"PARTS VALIDATION REPORT")
    print(f"{'='*80}\n")

    for section_code in sections_to_check:
        pdf_name = f"{section_code}_parts.pdf"
        schematic_name = f"{section_code}.pdf"

        if pdf_name not in registry["parts_lists"].get("electrical", {}):
            print(f"⚠ No parts list for section {section_code}")
            continue

        parts = registry["parts_lists"]["electrical"][pdf_name].get("parts", [])

        if not parts:
            continue

        print(f"\n{'='*80}")
        print(f"SECTION {section_code}: {len(parts)} parts")
        print(f"{'='*80}\n")

        # Build schematic page index
        schematic_pages = {}
        if schematic_name in registry["sections"].get("electrical", {}):
            schematic_info = registry["sections"]["electrical"][schematic_name]
            if schematic_info.get("indexed"):
                for page_num, page_data in schematic_info.get("pages", {}).items():
                    sheet_num = page_data.get("sheet_number", "")
                    if sheet_num:
                        schematic_pages[sheet_num] = {
                            "page": page_num,
                            "components": [c.lower() for c in page_data.get("components", [])],
                            "connections": page_data.get("connections", []),
                            "summary": page_data.get("summary", "")
                        }

        for part in parts:
            total_parts += 1
            symbol = part.get("symbol", "")
            sheet_ref = part.get("sheet_section", "")
            location = part.get("location", "")
            description = part.get("description", "")

            # Extract sheet number from reference (=11/7.7 -> 7)
            if "/" in sheet_ref:
                sheet_num = sheet_ref.split("/")[1].split(".")[0]
            else:
                sheet_num = ""

            # Check if sheet exists in schematic index
            if not sheet_num:
                print(f"⚠ {symbol:12} - No sheet reference")
                continue

            if sheet_num not in schematic_pages:
                print(f"✗ {symbol:12} - Sheet {sheet_num} NOT INDEXED")
                print(f"   Expected: {sheet_ref} | {location} | {description[:50]}")
                sheet_not_indexed += 1
                continue

            # Check if component appears on that sheet
            page_info = schematic_pages[sheet_num]
            symbol_lower = symbol.lower()

            # Try to find component (various formats: -TR1, TR1, etc.)
            found = False
            for comp in page_info["components"]:
                if symbol_lower in comp or symbol_lower.replace("-", "") in comp:
                    found = True
                    break

            if found:
                found_on_sheet += 1
                # Check if connections were extracted
                conn_count = len([c for c in page_info["connections"] if symbol in c])
                if conn_count > 0:
                    has_connections += 1
                    print(f"✓ {symbol:12} - Found on sheet {sheet_num} ({conn_count} connections)")
                    for conn in page_info["connections"]:
                        if symbol in conn:
                            print(f"   → {conn}")
                else:
                    print(f"✓ {symbol:12} - Found on sheet {sheet_num} (no connections extracted)")
            else:
                missing_from_sheet += 1
                print(f"✗ {symbol:12} - NOT FOUND on sheet {sheet_num}")
                print(f"   Expected: {sheet_ref} | {location} | {description[:50]}")
                print(f"   Sheet summary: {page_info['summary'][:80]}...")

    # Summary
    print(f"\n{'='*80}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*80}\n")
    print(f"Total parts checked:           {total_parts}")
    print(f"✓ Found on expected sheet:     {found_on_sheet} ({found_on_sheet/total_parts*100:.1f}%)")
    print(f"  With connections extracted:  {has_connections}")
    print(f"✗ Missing from expected sheet: {missing_from_sheet}")
    print(f"⚠ Sheet not indexed yet:       {sheet_not_indexed}")

    if missing_from_sheet > 0:
        print(f"\n⚠ {missing_from_sheet} parts are in parts list but not found on their sheets.")
        print(f"  Possible reasons:")
        print(f"  - Vision API missed component during indexing")
        print(f"  - Different naming in schematic vs parts list")
        print(f"  - Parts list error")

    if has_connections > 0:
        print(f"\n✓ {has_connections} parts already have connection data from schematic indexing!")
        print(f"  No additional Vision API cost needed for these.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        section_code = sys.argv[1]
        validate_parts(section_code=section_code)
    else:
        validate_parts()
