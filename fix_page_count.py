#!/usr/bin/env python3
"""
Quick fix to add page count to existing PDF in registry
"""

import sys
import json
from datetime import datetime

def fix_page_count(section, pdf_name, num_pages):
    """Update page count for existing PDF in registry"""

    registry_file = "schematic_registry.json"

    # Load registry
    try:
        with open(registry_file, 'r') as f:
            registry = json.load(f)
    except FileNotFoundError:
        print(f"Registry file not found: {registry_file}")
        return

    # Check if PDF exists in registry
    if section not in registry.get("sections", {}):
        print(f"Section '{section}' not found in registry")
        return

    if pdf_name not in registry["sections"][section]:
        print(f"PDF '{pdf_name}' not found in section '{section}'")
        return

    # Update page count
    registry["sections"][section][pdf_name]["total_pages"] = num_pages

    # Save registry
    with open(registry_file, 'w') as f:
        json.dump(registry, f, indent=2)

    print(f"✓ Updated {pdf_name}: {num_pages} pages")
    print(f"\nNow you can index it:")
    print(f"  python3 trace_cli.py")
    print(f"  TRACE> index {section} {pdf_name}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 fix_page_count.py <section> <pdf_name> <num_pages>")
        print("Example: python3 fix_page_count.py electrical 61.pdf 76")
        sys.exit(1)

    fix_page_count(sys.argv[1], sys.argv[2], int(sys.argv[3]))
