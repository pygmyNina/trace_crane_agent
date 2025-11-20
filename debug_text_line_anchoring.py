#!/usr/bin/env python3
"""
Debug script to verify text-to-line anchoring
Checks if component labels are correctly finding their starting lines
"""

import json
import csv
import argparse
from pathlib import Path


def load_components_from_csv(csv_path: str, page_number: int = None):
    """Load component positions from CSV"""
    components = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if page_number is not None and int(row['page_number']) != page_number:
                continue

            text = row['text'].strip()

            # Check if it's a component (starts with - but not -W)
            if not text.startswith('-') or text.startswith('-W'):
                continue

            x = int(row['x'])
            y = int(row['y'])
            w = int(row['width'])
            h = int(row['height'])

            components.append({
                'symbol': text,
                'label_x': x,
                'label_y': y,
                'label_width': w,
                'label_height': h,
                'label_center_x': x + w // 2,
                'label_center_y': y + h // 2,
                'page_number': int(row['page_number'])
            })

    return components


def load_lines_from_json(json_path: str):
    """Load lines from JSON"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data['lines']


def load_boundary(boundary_file: str):
    """Load boundary from JSON"""
    with open(boundary_file, 'r') as f:
        data = json.load(f)
    sb = data['schematic_boundary']
    return sb['x'], sb['y'], sb['width'], sb['height']


def adjust_component_to_crop(component, boundary_x, boundary_y):
    """Adjust component coordinates to cropped space"""
    adjusted = component.copy()
    adjusted['label_x'] = component['label_x'] - boundary_x
    adjusted['label_y'] = component['label_y'] - boundary_y
    adjusted['label_center_x'] = component['label_center_x'] - boundary_x
    adjusted['label_center_y'] = component['label_center_y'] - boundary_y
    return adjusted


def find_vertical_lines_to_right(component, lines, max_distance=500):
    """Find all vertical lines to the right of component"""
    vertical_lines = []

    for idx, line in enumerate(lines):
        if line['orientation'] != 'vertical':
            continue

        line_x = (line['x1'] + line['x2']) / 2

        # Only lines to the right
        if line_x <= component['label_x']:
            continue

        horizontal_distance = line_x - component['label_x']

        if horizontal_distance > max_distance:
            continue

        vertical_lines.append({
            'index': idx,
            'line': line,
            'line_x': line_x,
            'horizontal_distance': horizontal_distance,
            'vertical_range': (min(line['y1'], line['y2']), max(line['y1'], line['y2']))
        })

    # Sort by horizontal distance
    vertical_lines.sort(key=lambda x: x['horizontal_distance'])

    return vertical_lines


def main():
    parser = argparse.ArgumentParser(description='Debug text-to-line anchoring')
    parser.add_argument('--text-csv', required=True, help='Text detection CSV')
    parser.add_argument('--line-json', required=True, help='Line detection JSON')
    parser.add_argument('--boundary', help='Boundary dimensions JSON')
    parser.add_argument('--page-number', type=int, default=1, help='Page number')
    parser.add_argument('--component', help='Specific component to check (e.g., -FDS1)')
    parser.add_argument('--show-top', type=int, default=5, help='Show top N closest lines')
    parser.add_argument('--check-lines', help='Comma-separated line indices to check (e.g., 124,134,171)')

    args = parser.parse_args()

    print("Text-to-Line Anchoring Debug")
    print("=" * 80)

    # Load components
    print(f"\n1. Loading components from CSV...")
    components = load_components_from_csv(args.text_csv, args.page_number)
    print(f"   Found {len(components)} components")

    # Load lines
    print(f"\n2. Loading lines from JSON...")
    lines = load_lines_from_json(args.line_json)
    print(f"   Found {len(lines)} lines")

    # Load boundary if provided
    boundary_x, boundary_y = 0, 0
    if args.boundary:
        print(f"\n3. Loading boundary...")
        boundary_x, boundary_y, boundary_w, boundary_h = load_boundary(args.boundary)
        print(f"   Boundary: ({boundary_x}, {boundary_y}) size {boundary_w}x{boundary_h}")
        print(f"   Adjusting component coordinates to cropped space...")

        # Adjust components
        adjusted_components = []
        for comp in components:
            # Check if in boundary
            if (boundary_x <= comp['label_center_x'] <= boundary_x + boundary_w and
                boundary_y <= comp['label_center_y'] <= boundary_y + boundary_h):
                adjusted_components.append(adjust_component_to_crop(comp, boundary_x, boundary_y))

        components = adjusted_components
        print(f"   {len(components)} components within boundary after adjustment")

    # Filter components
    if args.component:
        components = [c for c in components if c['symbol'] == args.component]
        if not components:
            print(f"\n✗ Component {args.component} not found")
            return

    # Check specific lines if requested
    if args.check_lines:
        check_line_indices = [int(x.strip()) for x in args.check_lines.split(',')]
        print(f"\n{'='*80}")
        print(f"SPECIFIC LINE INSPECTION")
        print(f"{'='*80}")

        for idx in check_line_indices:
            if idx >= len(lines):
                print(f"\n✗ Line {idx} doesn't exist (only {len(lines)} lines total)")
                continue

            line = lines[idx]
            line_x = (line['x1'] + line['x2']) / 2
            line_y_min = min(line['y1'], line['y2'])
            line_y_max = max(line['y1'], line['y2'])

            print(f"\nLine {idx}:")
            print(f"  Orientation: {line['orientation']}")
            print(f"  Endpoints: ({line['x1']}, {line['y1']}) to ({line['x2']}, {line['y2']})")
            print(f"  Average X: {line_x:.1f}")
            print(f"  Y range: {line_y_min} to {line_y_max}")
            print(f"  Length: {line['length']:.1f}px")

            # If we have a specific component, show distance
            if args.component and components:
                comp = components[0]
                h_dist = line_x - comp['label_x']
                print(f"\n  Distance from {comp['symbol']} label (x={comp['label_x']}):")
                print(f"    Horizontal: {h_dist:.1f}px {'(to the right)' if h_dist > 0 else '(to the left)'}")

                if line_y_min <= comp['label_center_y'] <= line_y_max:
                    print(f"    ✓ Label center Y ({comp['label_center_y']}) is within line's vertical range")
                else:
                    v_offset = min(abs(comp['label_center_y'] - line_y_min),
                                 abs(comp['label_center_y'] - line_y_max))
                    print(f"    Label center Y ({comp['label_center_y']}) is {v_offset:.1f}px outside vertical range")

        print(f"\n{'='*80}")

    # Analyze each component
    print(f"\n{'='*80}")
    print(f"COMPONENT ANCHORING ANALYSIS")
    print(f"{'='*80}")

    for component in components:
        print(f"\n{'─'*80}")
        print(f"Component: {component['symbol']}")
        print(f"{'─'*80}")

        # Show original coordinates (before boundary adjustment)
        if args.boundary:
            orig_x = component['label_x'] + boundary_x
            orig_y = component['label_y'] + boundary_y
            orig_center_x = component['label_center_x'] + boundary_x
            orig_center_y = component['label_center_y'] + boundary_y
            print(f"\nOriginal coordinates (full image):")
            print(f"  Label box: ({orig_x}, {orig_y}) size {component['label_width']}x{component['label_height']}")
            print(f"  Label center: ({orig_center_x}, {orig_center_y})")

        # Show adjusted coordinates
        print(f"\nAdjusted coordinates (cropped image):")
        print(f"  Label box: ({component['label_x']}, {component['label_y']}) size {component['label_width']}x{component['label_height']}")
        print(f"  Label center: ({component['label_center_x']}, {component['label_center_y']})")

        # Find vertical lines to the right
        vertical_lines = find_vertical_lines_to_right(component, lines)

        print(f"\nVertical lines to the right: {len(vertical_lines)} found")

        if not vertical_lines:
            print("  ✗ NO VERTICAL LINES FOUND TO THE RIGHT!")
            print(f"  This means no lines exist between x={component['label_x']} and x={component['label_x']+500}")
            continue

        print(f"\nTop {min(args.show_top, len(vertical_lines))} closest vertical lines:")
        for i, vline in enumerate(vertical_lines[:args.show_top]):
            line = vline['line']
            print(f"\n  #{i+1}: Line {vline['index']}")
            print(f"      Position: x={vline['line_x']:.1f}, y_range=({vline['vertical_range'][0]}, {vline['vertical_range'][1]})")
            print(f"      Endpoints: ({line['x1']}, {line['y1']}) to ({line['x2']}, {line['y2']})")
            print(f"      Horizontal distance from label: {vline['horizontal_distance']:.1f}px")
            print(f"      Length: {line['length']:.1f}px")

            # Check if label center is within vertical range of line
            if vline['vertical_range'][0] <= component['label_center_y'] <= vline['vertical_range'][1]:
                print(f"      ✓ Label center Y is within line's vertical range")
            else:
                offset = min(abs(component['label_center_y'] - vline['vertical_range'][0]),
                           abs(component['label_center_y'] - vline['vertical_range'][1]))
                print(f"      ✗ Label center Y is {offset:.1f}px outside line's vertical range")

        # Show which line would be selected
        if vertical_lines:
            selected = vertical_lines[0]
            print(f"\n  → SELECTED: Line {selected['index']} at x={selected['line_x']:.1f}, distance={selected['horizontal_distance']:.1f}px")

    print(f"\n{'='*80}")


if __name__ == '__main__':
    main()
