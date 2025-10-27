#!/usr/bin/env python3
"""
Deep Connection Mapper - Extract detailed terminal-level connections for components
Uses Vision API to analyze schematics and extract precise wiring information
"""

import json
import os
import sys
from datetime import datetime
from trace.vision_analyzer import VisionAnalyzer
from trace.pdf_image_converter import PDFImageConverter


def load_registry():
    """Load schematic registry"""
    with open('schematic_registry.json', 'r') as f:
        return json.load(f)


def save_registry(registry):
    """Save registry to file"""
    with open('schematic_registry.json', 'w') as f:
        json.dump(registry, f, indent=2)


def get_parts_for_section(registry, section_code):
    """Get all parts for a section"""
    parts_file = f"{section_code}_parts.pdf"
    if 'parts_lists' not in registry:
        return []
    if 'electrical' not in registry['parts_lists']:
        return []
    if parts_file not in registry['parts_lists']['electrical']:
        return []

    return registry['parts_lists']['electrical'][parts_file].get('parts', [])


def extract_sheet_number(sheet_ref):
    """Extract sheet number from reference (=10/101.2 -> 101)"""
    if not sheet_ref or '/' not in sheet_ref:
        return None
    parts = sheet_ref.split('/')
    if len(parts) >= 2:
        return parts[1].split('.')[0]
    return None


def find_page_for_sheet(registry, section_code, sheet_number):
    """Find which page number corresponds to a sheet number"""
    pdf_name = f"{section_code}.pdf"
    if 'sections' not in registry:
        return None
    if 'electrical' not in registry['sections']:
        return None
    if pdf_name not in registry['sections']['electrical']:
        return None

    pdf_info = registry['sections']['electrical'][pdf_name]
    pages = pdf_info.get('pages', {})

    # Check for sheet_number field (if re-indexed with newer system)
    for page_num, page_data in pages.items():
        if page_data.get('sheet_number') == sheet_number:
            return page_num

    # Fallback: For section 10, assume page 1 = sheet 101, page 2 = 102, page 3 = 103
    # This works for most sections with simple numbering
    try:
        page_num = str(int(sheet_number) - (int(section_code) * 100))
        if page_num in pages:
            return page_num
    except:
        pass

    return None


def extract_deep_connections(vision, converter, component_symbol, pdf_path, page_num):
    """
    Extract detailed terminal-level connections for a specific component

    Args:
        vision: VisionAnalyzer instance
        converter: PDFImageConverter instance
        component_symbol: Component to focus on (e.g., "-FDS1")
        pdf_path: Path to schematic PDF
        page_num: Page number to analyze

    Returns:
        Dictionary with detailed connection data
    """
    print(f"  Analyzing {component_symbol} on page {page_num}...")

    # Convert page to image
    image_path = converter.convert_page(pdf_path, int(page_num))
    if not image_path:
        print(f"    ✗ Failed to convert page")
        return None

    # Prepare detailed prompt for Vision API
    prompt = f"""Analyze this crane electrical schematic and extract DETAILED connection information for component {component_symbol}.

FOCUS ON: {component_symbol}

SCHEMATIC CONVENTIONS YOU MUST FOLLOW:
1. COMPONENTS are shown with a box or dotted box around them, labeled with format: SYMBOL +LOCATION
   Example: -FDS1 +GDW, -PB1 +ERI, -SG1 +MHI

2. CABLE BUNDLES are shown as DOTTED LINES crossing multiple wires and labeled with format: -WXXXX
   Example: -W2061 (not W2035, W2037 - those are individual conductors within the bundle)
   Cables contain 2-40 conductors

3. PHYSICAL PROXIMITY ≠ ELECTRICAL CONNECTION
   Components may be housed in the same cabinet but NOT electrically connected
   Example: -HTR1 is physically in +GDW cabinet but NOT connected to -FDS1
   Only mark as "connected" if wires actually link them

4. TERMINAL DESTINATIONS must be SPECIFIC in format: "SYMBOL +LOCATION Terminal X"
   Example: "-SG1 +MHI Terminal 5" NOT "upstream control wiring"

5. CROSS-REFERENCES are shown in format: =XX/YYY.Y (points to another sheet)
   Example: =41/109.3 means section 41, sheet 109, subsection 3
   Include ALL cross-references found on traced wires

Extract the following information in JSON format:

{{
  "component_symbol": "{component_symbol}",
  "location": "location code (e.g., +GDW, +ERI)",
  "terminals": [
    {{
      "terminal_number": "terminal designation (1, 2, 13, 14, T1, T2, etc.)",
      "terminal_type": "type (power, control, signal, ground)",
      "cable_bundle": "cable bundle designation if visible (format: -WXXXX)",
      "conductor_in_bundle": "specific conductor within bundle if visible",
      "connects_to_component": "destination component with location (format: SYMBOL +LOCATION)",
      "connects_to_terminal": "destination terminal number",
      "cross_references": ["list of sheet cross-references in format =XX/YYY.Y"],
      "signal_type": "power/control/signal/ground",
      "voltage": "voltage level if visible",
      "wire_spec": "wire specification (AWG, conductor count, insulation type)"
    }}
  ],
  "cable_bundles": [
    {{
      "cable_designation": "cable bundle label (format: -WXXXX)",
      "conductor_count": "number of conductors if visible",
      "terminals_connected": ["list of terminal numbers using this cable"]
    }}
  ],
  "physically_adjacent_components": [
    "components in same cabinet/location but NOT electrically connected"
  ],
  "electrically_connected_components": [
    "components with actual wire connections (format: SYMBOL +LOCATION Terminal X)"
  ],
  "notes": "any additional important details"
}}

CRITICAL RULES:
- Look for DOTTED LINES across wires = cable bundles (format: -WXXXX)
- Trace each wire from {component_symbol} terminal to its DESTINATION component and terminal
- Include cross-references (=XX/YYY.Y) found along wire paths
- Do NOT assume electrical connection just because components share a cabinet
- Be specific: "SYMBOL +LOCATION Terminal X" not "upstream wiring"
- If you cannot clearly see where a wire goes, state "trace unclear" rather than guessing
"""

    # Call Vision API
    try:
        response = vision.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": vision._encode_image(image_path)
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Try to find JSON in response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            connection_data = json.loads(json_match.group(0))
            print(f"    ✓ Extracted detailed connections")
            return connection_data
        else:
            print(f"    ⚠ No JSON found in response")
            return {"raw_response": response_text}

    except Exception as e:
        print(f"    ✗ Error: {e}")
        return None


def deep_map_section(section_code, component_symbols=None):
    """
    Perform deep connection mapping for components in a section

    Args:
        section_code: Section code (e.g., "10")
        component_symbols: List of specific components to map, or None for all
    """
    print(f"\n{'='*80}")
    print(f"DEEP CONNECTION MAPPING - SECTION {section_code}")
    print(f"{'='*80}\n")

    # Initialize
    vision = VisionAnalyzer()
    converter = PDFImageConverter()
    registry = load_registry()

    # Check API
    if not vision.check_api_available():
        print("✗ Vision API not available. Set ANTHROPIC_API_KEY environment variable.")
        return

    # Get parts for section
    parts = get_parts_for_section(registry, section_code)
    if not parts:
        print(f"✗ No parts found for section {section_code}")
        return

    print(f"Found {len(parts)} parts in section {section_code}")

    # Filter to specific components if requested
    if component_symbols:
        parts = [p for p in parts if p.get('symbol') in component_symbols]
        print(f"Filtering to {len(parts)} specified components: {component_symbols}")

    # Get schematic PDF path
    pdf_name = f"{section_code}.pdf"
    if pdf_name not in registry['sections']['electrical']:
        print(f"✗ Schematic {pdf_name} not found in registry")
        return

    pdf_info = registry['sections']['electrical'][pdf_name]
    pdf_path = pdf_info['path']

    # Group parts by sheet number
    parts_by_sheet = {}
    for part in parts:
        sheet_ref = part.get('sheet_section', '')
        sheet_num = extract_sheet_number(sheet_ref)
        if sheet_num:
            if sheet_num not in parts_by_sheet:
                parts_by_sheet[sheet_num] = []
            parts_by_sheet[sheet_num].append(part)

    print(f"\nParts organized across {len(parts_by_sheet)} sheets")
    print()

    # Track results
    total_mapped = 0
    total_cost = 0.0

    # Process each sheet
    for sheet_num in sorted(parts_by_sheet.keys()):
        sheet_parts = parts_by_sheet[sheet_num]
        unique_symbols = list(set([p.get('symbol') for p in sheet_parts if p.get('symbol')]))

        print(f"Sheet {sheet_num}: {len(unique_symbols)} components to map")

        # Find page number
        page_num = find_page_for_sheet(registry, section_code, sheet_num)
        if not page_num:
            print(f"  ⚠ Could not find page for sheet {sheet_num}")
            continue

        # Process each unique component symbol
        for symbol in unique_symbols:
            connection_data = extract_deep_connections(
                vision, converter, symbol, pdf_path, page_num
            )

            if connection_data:
                # Store in registry under page data
                page_data = pdf_info['pages'][page_num]
                if 'deep_connections' not in page_data:
                    page_data['deep_connections'] = {}

                page_data['deep_connections'][symbol] = {
                    'data': connection_data,
                    'extracted_at': datetime.now().isoformat()
                }

                total_mapped += 1
                # Rough cost estimate: ~$0.02 per image analysis
                total_cost += 0.02

        print()

    # Save registry
    if total_mapped > 0:
        save_registry(registry)
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Components mapped: {total_mapped}")
        print(f"Estimated cost: ${total_cost:.2f}")
        print(f"\n✓ Deep connection data saved to schematic_registry.json")
    else:
        print(f"\n⚠ No connections extracted")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 deep_connection_mapper.py <section_code> [component1 component2 ...]")
        print("\nExamples:")
        print("  python3 deep_connection_mapper.py 10                    # Map all section 10 components")
        print("  python3 deep_connection_mapper.py 10 -FDS1 -PB1        # Map only FDS1 and PB1")
        sys.exit(1)

    section = sys.argv[1]
    components = sys.argv[2:] if len(sys.argv) > 2 else None

    deep_map_section(section, components)
