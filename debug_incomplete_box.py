#!/usr/bin/env python3
"""
Debug script to investigate why a component box rectangle is incomplete
Finds horizontal lines near a given Y coordinate to see if merging failed
"""

import json
import argparse


def load_lines(json_path: str):
    """Load lines from JSON"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data['lines']


def main():
    parser = argparse.ArgumentParser(description='Debug incomplete box rectangles')
    parser.add_argument('--line-json', required=True, help='Line detection JSON')
    parser.add_argument('--line-index', type=int, help='Specific line to investigate')
    parser.add_argument('--y-coord', type=int, help='Y coordinate to search around')
    parser.add_argument('--y-tolerance', type=int, default=50, help='Y tolerance for search')
    parser.add_argument('--x-range-start', type=int, help='Starting X coordinate of interest')
    parser.add_argument('--x-range-end', type=int, help='Ending X coordinate of interest')

    args = parser.parse_args()

    lines = load_lines(args.line_json)
    print(f"Loaded {len(lines)} lines\n")

    if args.line_index is not None:
        # Show specific line details
        line = lines[args.line_index]
        print(f"Line {args.line_index}:")
        print(f"  Orientation: {line['orientation']}")
        print(f"  Endpoints: ({line['x1']}, {line['y1']}) to ({line['x2']}, {line['y2']})")
        print(f"  Length: {line['length']:.1f}px")
        print(f"  Angle: {line['angle']:.1f}°")

        if line['orientation'] == 'horizontal':
            x_min = min(line['x1'], line['x2'])
            x_max = max(line['x1'], line['x2'])
            y_avg = (line['y1'] + line['y2']) / 2
            print(f"  X range: {x_min} to {x_max}")
            print(f"  Y average: {y_avg:.1f}")
        elif line['orientation'] == 'vertical':
            x_avg = (line['x1'] + line['x2']) / 2
            y_min = min(line['y1'], line['y2'])
            y_max = max(line['y1'], line['y2'])
            print(f"  X average: {x_avg:.1f}")
            print(f"  Y range: {y_min} to {y_max}")

    if args.y_coord is not None:
        # Find horizontal lines near this Y coordinate
        print(f"\nHorizontal lines near Y={args.y_coord} (±{args.y_tolerance}px):")

        target_y = args.y_coord
        tolerance = args.y_tolerance

        candidates = []
        for idx, line in enumerate(lines):
            if line['orientation'] != 'horizontal':
                continue

            y_avg = (line['y1'] + line['y2']) / 2
            if abs(y_avg - target_y) > tolerance:
                continue

            x_min = min(line['x1'], line['x2'])
            x_max = max(line['x1'], line['x2'])

            # Filter by X range if specified
            if args.x_range_start is not None or args.x_range_end is not None:
                if args.x_range_start and x_max < args.x_range_start:
                    continue
                if args.x_range_end and x_min > args.x_range_end:
                    continue

            candidates.append({
                'index': idx,
                'line': line,
                'x_min': x_min,
                'x_max': x_max,
                'y_avg': y_avg,
                'y_offset': abs(y_avg - target_y)
            })

        # Sort by X position
        candidates.sort(key=lambda x: x['x_min'])

        print(f"  Found {len(candidates)} candidate lines:")
        for c in candidates:
            line = c['line']
            print(f"\n    Line {c['index']}:")
            print(f"      Endpoints: ({line['x1']}, {line['y1']}) to ({line['x2']}, {line['y2']})")
            print(f"      X range: {c['x_min']} to {c['x_max']} (length: {c['x_max'] - c['x_min']}px)")
            print(f"      Y average: {c['y_avg']:.1f} (offset from {target_y}: {c['y_offset']:.1f}px)")
            print(f"      Line length: {line['length']:.1f}px")

        # Check for gaps between consecutive lines
        if len(candidates) > 1:
            print(f"\n  Gaps between consecutive lines:")
            for i in range(len(candidates) - 1):
                curr = candidates[i]
                next_line = candidates[i + 1]
                gap = next_line['x_min'] - curr['x_max']
                print(f"    Between Line {curr['index']} and Line {next_line['index']}: {gap}px gap")
                if gap > 75:
                    print(f"      ⚠ Gap exceeds merge threshold (75px)")
                elif gap > 55:
                    print(f"      ⚠ Gap exceeds default threshold (55px)")


if __name__ == '__main__':
    main()
