#!/usr/bin/env python3
"""
Extract Symbol-Based Components from Text Detection CSV

Symbol-based components (PB, CT, CB) don't have rectangular borders -
they're identified directly from text detection. This script extracts
them from the text CSV for later compilation with rectangle-traced components.

Usage:
  python3 extract_symbol_components.py \
    --text-csv "extraction_results/system_10/visual_3_final/detections_with_visual_ids.csv" \
    --output "extraction_results/system_10/components/symbol_components.json" \
    --page-number 1 \
    --boundary "extraction_results/system_10/boundary_dimensions.json"
"""

import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict


@dataclass
class SymbolComponent:
    """Symbol-based component extracted from text detection"""
    symbol: str           # e.g., "-PB1", "-CT1"
    component_type: str   # e.g., "PB", "CT", "CB"
    x: int
    y: int
    width: int
    height: int
    center_x: int
    center_y: int
    page_number: int
    source: str           # Always "text_detection" for these


# Symbol-based component prefixes
SYMBOL_COMPONENT_PREFIXES = ['PB', 'CT', 'CB']


def get_component_type(text: str) -> str:
    """
    Get component type from text if it's a symbol-based component

    Args:
        text: Text string (e.g., "-PB1", "-CT2")

    Returns:
        Component type (e.g., "PB") or empty string if not a symbol component
    """
    if not text or len(text) < 3:
        return ""

    # Must start with dash
    if not text.startswith('-'):
        return ""

    # Extract prefix after dash, before numbers
    prefix = text[1:].rstrip('0123456789')

    if prefix in SYMBOL_COMPONENT_PREFIXES:
        return prefix

    return ""


def load_boundary(boundary_file: str) -> Tuple[int, int, int, int]:
    """Load schematic boundary from JSON file"""
    with open(boundary_file, 'r') as f:
        data = json.load(f)

    sb = data['schematic_boundary']
    return (sb['x'], sb['y'], sb['width'], sb['height'])


def extract_symbol_components(csv_path: str,
                               page_number: int = None,
                               boundary: Tuple[int, int, int, int] = None) -> List[SymbolComponent]:
    """
    Extract symbol-based components from text detection CSV

    Args:
        csv_path: Path to text detection CSV
        page_number: Optional filter for specific page
        boundary: Optional (x, y, w, h) to filter and adjust coordinates

    Returns:
        List of SymbolComponent objects
    """
    components = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter by page if specified
            if page_number is not None and int(row['page_number']) != page_number:
                continue

            text = row['text'].strip()
            component_type = get_component_type(text)

            # Skip if not a symbol-based component
            if not component_type:
                continue

            x = int(row['x'])
            y = int(row['y'])
            w = int(row['width'])
            h = int(row['height'])
            center_x = x + w // 2
            center_y = y + h // 2

            # Filter by boundary if provided
            if boundary is not None:
                bx, by, bw, bh = boundary
                if not (bx <= center_x <= bx + bw and by <= center_y <= by + bh):
                    continue
                # Adjust coordinates relative to boundary
                x -= bx
                y -= by
                center_x -= bx
                center_y -= by

            component = SymbolComponent(
                symbol=text,
                component_type=component_type,
                x=x,
                y=y,
                width=w,
                height=h,
                center_x=center_x,
                center_y=center_y,
                page_number=int(row['page_number']),
                source="text_detection"
            )
            components.append(component)

    return components


def main():
    parser = argparse.ArgumentParser(
        description='Extract symbol-based components (PB, CT, CB) from text detection CSV'
    )
    parser.add_argument('--text-csv', required=True, help='Path to text detection CSV')
    parser.add_argument('--output', required=True, help='Output JSON path')
    parser.add_argument('--page-number', type=int, help='Page number to process')
    parser.add_argument('--boundary', help='Path to boundary_dimensions.json')

    args = parser.parse_args()

    print("Extract Symbol Components")
    print("=" * 60)

    # Load boundary if provided
    boundary = None
    if args.boundary:
        boundary = load_boundary(args.boundary)
        print(f"Using boundary: {boundary[2]}x{boundary[3]} at ({boundary[0]}, {boundary[1]})")

    # Extract components
    print(f"\nExtracting symbol components from: {args.text_csv}")
    components = extract_symbol_components(args.text_csv, args.page_number, boundary)

    # Group by type for display
    by_type = {}
    for comp in components:
        if comp.component_type not in by_type:
            by_type[comp.component_type] = []
        by_type[comp.component_type].append(comp)

    print(f"\nFound {len(components)} symbol-based components:")
    for comp_type, comps in sorted(by_type.items()):
        print(f"  {comp_type}: {len(comps)}")
        for c in comps:
            print(f"    {c.symbol} at ({c.x}, {c.y}) size {c.width}x{c.height}")

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'source_csv': args.text_csv,
        'page_number': args.page_number,
        'boundary': args.boundary,
        'total_components': len(components),
        'by_type': {k: len(v) for k, v in by_type.items()},
        'components': [asdict(c) for c in components]
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Saved symbol components: {output_path}")


if __name__ == '__main__':
    main()
