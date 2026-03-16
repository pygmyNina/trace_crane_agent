#!/usr/bin/env python3
"""
Analyze parts list to identify assemblies vs reused components
"""

import json
from collections import defaultdict

def analyze_parts_structure(section_code="10"):
    """Analyze parts to find assemblies and reused components"""

    # Load registry
    with open("schematic_registry.json", 'r') as f:
        registry = json.load(f)

    pdf_name = f"{section_code}_parts.pdf"
    parts = registry["parts_lists"]["electrical"][pdf_name]["parts"]

    print(f"\n{'='*80}")
    print(f"SECTION {section_code} PARTS ANALYSIS")
    print(f"{'='*80}\n")
    print(f"Total parts in list: {len(parts)}\n")

    # Group by symbol
    by_symbol = defaultdict(list)
    for part in parts:
        by_symbol[part["symbol"]].append(part)

    # Analyze each symbol
    assemblies = []
    reused_components = []
    single_components = []

    for symbol, instances in sorted(by_symbol.items()):
        if len(instances) == 1:
            single_components.append({
                "symbol": symbol,
                "description": instances[0]["description"],
                "location": instances[0]["location"],
                "sheet": instances[0]["sheet_section"]
            })
        else:
            # Group by location + sheet to detect assemblies
            by_location_sheet = defaultdict(list)
            for inst in instances:
                key = (inst["location"], inst["sheet_section"])
                by_location_sheet[key].append(inst)

            # Check if assembly or reused
            if len(by_location_sheet) == 1:
                # All parts at same location/sheet = ASSEMBLY
                assemblies.append({
                    "symbol": symbol,
                    "location": instances[0]["location"],
                    "sheet": instances[0]["sheet_section"],
                    "part_count": len(instances),
                    "parts": [{"description": p["description"],
                              "identification": p["identification"]}
                             for p in instances]
                })
            else:
                # Different locations = REUSED COMPONENT
                reused_components.append({
                    "symbol": symbol,
                    "instance_count": len(instances),
                    "locations": [{"location": p["location"],
                                  "sheet": p["sheet_section"],
                                  "description": p["description"]}
                                 for p in instances]
                })

    # Print results
    print(f"{'='*80}")
    print(f"ASSEMBLIES (multiple parts → one schematic symbol)")
    print(f"{'='*80}\n")

    if assemblies:
        for asm in assemblies:
            print(f"🔧 {asm['symbol']}")
            print(f"   Location: {asm['location']}")
            print(f"   Sheet: {asm['sheet']}")
            print(f"   Parts in assembly: {asm['part_count']}")
            for i, part in enumerate(asm['parts'], 1):
                print(f"     {i}. {part['description']}")
                print(f"        ({part['identification']})")
            print()
    else:
        print("   No assemblies found\n")

    print(f"{'='*80}")
    print(f"REUSED COMPONENTS (same part in multiple locations)")
    print(f"{'='*80}\n")

    if reused_components:
        for comp in reused_components:
            print(f"🔄 {comp['symbol']}")
            print(f"   Used in {comp['instance_count']} locations:")
            for i, loc in enumerate(comp['locations'], 1):
                print(f"     {i}. {loc['location']} (sheet {loc['sheet']})")
                print(f"        {loc['description']}")
            print()
    else:
        print("   No reused components found\n")

    print(f"{'='*80}")
    print(f"SINGLE COMPONENTS (one part, one location)")
    print(f"{'='*80}\n")

    if single_components:
        for comp in single_components:
            print(f"⚙️  {comp['symbol']}: {comp['description']}")
            print(f"    Location: {comp['location']} | Sheet: {comp['sheet']}")
            print()
    else:
        print("   No single components found\n")

    # Summary
    print(f"{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")
    print(f"Assemblies:          {len(assemblies)}")
    print(f"Reused components:   {len(reused_components)}")
    print(f"Single components:   {len(single_components)}")
    print(f"Total unique symbols: {len(by_symbol)}")
    print(f"Total parts entries:  {len(parts)}")
    print()

if __name__ == "__main__":
    import sys
    section = sys.argv[1] if len(sys.argv) > 1 else "10"
    analyze_parts_structure(section)
