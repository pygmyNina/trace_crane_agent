#!/usr/bin/env python3
"""
Smart Text Merging - Two-Pass Algorithm
Pass 1: Merge special symbol cells (=, /, .) with tight tolerance (5px)
Pass 2: Merge plain text with looser tolerance (10px Y, 40px X)

Usage:
  python3 smart_merge_detections.py \
    --input extraction_results/system_10_production/metadata/system_10_deduplicated.csv \
    --output extraction_results/system_10_production/metadata/system_10_merged.csv
"""

import csv
import argparse
import re
from typing import List, Dict


class TextDetection:
    def __init__(self, data: Dict):
        self.unique_id = data['unique_id']
        self.page_number = int(data['page_number'])
        self.text = data['text']
        self.x = int(data['x'])
        self.y = int(data['y'])
        self.width = int(data['width'])
        self.height = int(data['height'])
        self.confidence = float(data['confidence'])
        self.orientation = data['orientation']
        self.merged_from = []  # Track what was merged into this

    def has_special_char(self):
        """Check if text contains special characters (=, /, .)"""
        return any(c in self.text for c in ['=', '/', '.'])

    def center_x(self):
        return self.x + self.width / 2

    def center_y(self):
        return self.y + self.height / 2

    def to_dict(self):
        return {
            'unique_id': self.unique_id,
            'page_number': self.page_number,
            'text': self.text,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'confidence': self.confidence,
            'orientation': self.orientation
        }


def similar_size(d1: TextDetection, d2: TextDetection, tolerance=0.5):
    """Check if two detections are similar size (within 50% tolerance)"""
    size1 = (d1.width + d1.height) / 2
    size2 = (d2.width + d2.height) / 2
    ratio = max(size1, size2) / min(size1, size2)
    return ratio <= (1 + tolerance)


def merge_two_detections(d1: TextDetection, d2: TextDetection) -> TextDetection:
    """Merge two detections into one"""
    # Combine text (left to right or top to bottom based on orientation)
    if d1.x < d2.x:  # d1 is to the left
        merged_text = d1.text + d2.text
    else:
        merged_text = d2.text + d1.text

    # Calculate bounding box
    min_x = min(d1.x, d2.x)
    min_y = min(d1.y, d2.y)
    max_x = max(d1.x + d1.width, d2.x + d2.width)
    max_y = max(d1.y + d1.height, d2.y + d2.height)

    merged = TextDetection({
        'unique_id': d1.unique_id,  # Keep first ID
        'page_number': d1.page_number,
        'text': merged_text,
        'x': min_x,
        'y': min_y,
        'width': max_x - min_x,
        'height': max_y - min_y,
        'confidence': min(d1.confidence, d2.confidence),
        'orientation': d1.orientation
    })

    merged.merged_from = d1.merged_from + [d2.unique_id]
    return merged


def merge_special_symbols_pass(detections: List[TextDetection]) -> List[TextDetection]:
    """
    Pass 1: Merge cells with special characters (=, /, .)
    - Vertical: same Y-plane (±5px), same size, gap ≤5px
    - Horizontal: same X-plane (±5px), same size, gap ≤5px
    - Iterative until no more merges possible
    """
    print("\n" + "="*80)
    print("PASS 1: SPECIAL SYMBOL MERGING (=, /, .)")
    print("="*80)
    print("Rules: Same size, same plane (±5px), gap ≤5px")
    print("Iterative merging until complete\n")

    y_tolerance = 5
    gap_tolerance = 5
    merge_count = 0
    iteration = 0

    while True:
        iteration += 1
        merged_this_round = False

        # Group by page
        by_page = {}
        for d in detections:
            if d.page_number not in by_page:
                by_page[d.page_number] = []
            by_page[d.page_number].append(d)

        new_detections = []

        for page_num, page_dets in by_page.items():
            merged_indices = set()

            for i, d1 in enumerate(page_dets):
                if i in merged_indices:
                    continue

                # Only merge if d1 has special character
                if not d1.has_special_char():
                    new_detections.append(d1)
                    continue

                # Look for merge candidate
                best_match = None
                best_gap = float('inf')

                for j, d2 in enumerate(page_dets):
                    if i == j or j in merged_indices:
                        continue

                    # Check if similar size
                    if not similar_size(d1, d2):
                        continue

                    # Check Y-plane (horizontal merging)
                    y_diff = abs(d1.center_y() - d2.center_y())
                    if y_diff <= y_tolerance:
                        # Calculate horizontal gap
                        if d1.x < d2.x:
                            gap = d2.x - (d1.x + d1.width)
                        else:
                            gap = d1.x - (d2.x + d2.width)

                        if 0 <= gap <= gap_tolerance and gap < best_gap:
                            best_match = j
                            best_gap = gap

                if best_match is not None:
                    # Merge d1 and d2
                    d2 = page_dets[best_match]
                    merged = merge_two_detections(d1, d2)
                    new_detections.append(merged)
                    merged_indices.add(i)
                    merged_indices.add(best_match)
                    merge_count += 1
                    merged_this_round = True
                    print(f"  [Page {page_num}] Merged: '{d1.text}' + '{d2.text}' → '{merged.text}' (gap: {best_gap:.1f}px)")
                else:
                    new_detections.append(d1)

        detections = new_detections

        if not merged_this_round:
            print(f"\n✓ Pass 1 complete after {iteration} iterations")
            print(f"  Total special symbol merges: {merge_count}")
            break

    return detections


def merge_plain_text_pass(detections: List[TextDetection]) -> List[TextDetection]:
    """
    Pass 2: Merge plain text (without special symbols)
    - Y-axis tolerance: 10px
    - X-axis gap tolerance: 40px
    """
    print("\n" + "="*80)
    print("PASS 2: PLAIN TEXT MERGING")
    print("="*80)
    print("Rules: Y-axis ±10px, X-gap ≤40px\n")

    y_tolerance = 10
    gap_tolerance = 40
    merge_count = 0

    # Group by page
    by_page = {}
    for d in detections:
        if d.page_number not in by_page:
            by_page[d.page_number] = []
        by_page[d.page_number].append(d)

    new_detections = []

    for page_num, page_dets in by_page.items():
        # Sort by Y, then X for left-to-right merging
        page_dets.sort(key=lambda d: (d.y, d.x))
        merged_indices = set()

        for i, d1 in enumerate(page_dets):
            if i in merged_indices:
                continue

            # Skip if has special character (already handled in Pass 1)
            if d1.has_special_char():
                new_detections.append(d1)
                continue

            # Look for merge candidates (left to right on same line)
            candidates = []
            for j, d2 in enumerate(page_dets):
                if i == j or j in merged_indices:
                    continue

                # Skip if has special character
                if d2.has_special_char():
                    continue

                # Check Y-plane
                y_diff = abs(d1.center_y() - d2.center_y())
                if y_diff <= y_tolerance:
                    # Calculate horizontal gap
                    if d1.x < d2.x:
                        gap = d2.x - (d1.x + d1.width)
                    else:
                        gap = d1.x - (d2.x + d2.width)

                    if 0 <= gap <= gap_tolerance:
                        candidates.append((j, d2, gap))

            if candidates:
                # Sort by X position (left to right)
                candidates.sort(key=lambda c: c[1].x)

                # Merge with closest neighbor
                best_j, best_d2, best_gap = candidates[0]
                merged = merge_two_detections(d1, best_d2)
                new_detections.append(merged)
                merged_indices.add(i)
                merged_indices.add(best_j)
                merge_count += 1
                print(f"  [Page {page_num}] Merged: '{d1.text}' + '{best_d2.text}' → '{merged.text}' (gap: {best_gap:.1f}px)")
            else:
                new_detections.append(d1)

    print(f"\n✓ Pass 2 complete")
    print(f"  Total plain text merges: {merge_count}")

    return new_detections


def smart_merge(input_csv: str, output_csv: str):
    """Run two-pass merging algorithm"""
    print("\n" + "="*80)
    print("SMART TEXT MERGING - TWO-PASS ALGORITHM")
    print("="*80)
    print(f"Input: {input_csv}")
    print(f"Output: {output_csv}")

    # Read detections
    detections = []
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            detections.append(TextDetection(row))

    print(f"\nStarting detections: {len(detections)}")

    # Pass 1: Special symbols
    detections = merge_special_symbols_pass(detections)

    # Pass 2: Plain text
    detections = merge_plain_text_pass(detections)

    # Write results
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for det in detections:
            writer.writerow(det.to_dict())

    print("\n" + "="*80)
    print("MERGING COMPLETE")
    print("="*80)
    print(f"Starting detections: {len(detections) + sum(len(d.merged_from) for d in detections)}")
    print(f"Final detections: {len(detections)}")
    print(f"Total merged: {sum(len(d.merged_from) for d in detections)}")
    print(f"\n✓ Saved: {output_csv}")


def main():
    parser = argparse.ArgumentParser(
        description='Smart text merging with two-pass algorithm',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output CSV file')

    args = parser.parse_args()

    smart_merge(args.input, args.output)


if __name__ == '__main__':
    main()
