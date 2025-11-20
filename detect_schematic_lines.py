#!/usr/bin/env python3
"""
Schematic Line Detection - Detect all line segments in schematic images
Uses Line Segment Detector (LSD) optimized for engineering drawings

This script is used in two contexts:
1. Step 2: Detect ALL lines (including component boundaries) for component box tracing
2. Step 5: Detect wire lines only (after components are masked)

Usage:
  # Step 2: Detect all lines
  python3 detect_schematic_lines.py \
    --image "extraction_results/system_10/masked/page_001_text_masked.png" \
    --output "extraction_results/system_10/lines/page_001_all_lines.json" \
    --visualize

  # Step 5: Detect wire lines only
  python3 detect_schematic_lines.py \
    --image "extraction_results/system_10/masked/page_001_full_masked.png" \
    --output "extraction_results/system_10/wires/page_001_wires.json" \
    --visualize
"""

import cv2
import numpy as np
import json
import argparse
import math
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Line:
    """Detected line segment"""
    x1: int
    y1: int
    x2: int
    y2: int
    length: float
    angle: float
    orientation: str  # 'horizontal', 'vertical', 'diagonal', 'other'


def detect_lines(image: np.ndarray,
                 min_length: int = 12,
                 lsd_scale: float = 0.8,
                 lsd_sigma_scale: float = 0.6) -> List[Line]:
    """
    Detect line segments using Line Segment Detector (LSD)

    LSD is specifically designed for line detection in images and works
    very well for engineering drawings and schematics.

    Args:
        image: Input image (BGR or grayscale)
        min_length: Minimum line length in pixels
        lsd_scale: Scale factor for LSD (default 0.8)
        lsd_sigma_scale: Gaussian filter sigma for LSD (default 0.6)

    Returns:
        List of detected Line objects
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Create LSD detector
    lsd = cv2.createLineSegmentDetector(
        refine=cv2.LSD_REFINE_STD,
        scale=lsd_scale,
        sigma_scale=lsd_sigma_scale
    )

    # Detect lines
    detected_lines, width, prec, nfa = lsd.detect(gray)

    if detected_lines is None:
        print("  No lines detected")
        return []

    lines = []
    for line_data in detected_lines:
        x1, y1, x2, y2 = line_data[0]

        # Convert to integers
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # Calculate length
        length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        # Filter by minimum length
        if length < min_length:
            continue

        # Calculate angle (in degrees, 0 = horizontal right, 90 = vertical up)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))

        # Normalize angle to [0, 180)
        if angle < 0:
            angle += 180

        # Classify orientation
        orientation = classify_orientation(angle)

        line = Line(
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            length=length,
            angle=angle,
            orientation=orientation
        )
        lines.append(line)

    return lines


def classify_orientation(angle: float, tolerance: float = 15.0) -> str:
    """
    Classify line orientation based on angle

    Args:
        angle: Angle in degrees [0, 180)
        tolerance: Tolerance in degrees for horizontal/vertical classification

    Returns:
        'horizontal', 'vertical', 'diagonal', or 'other'
    """
    # Horizontal: ~0° or ~180°
    if angle < tolerance or angle > (180 - tolerance):
        return 'horizontal'

    # Vertical: ~90°
    if abs(angle - 90) < tolerance:
        return 'vertical'

    # Diagonal: ~45° or ~135°
    if abs(angle - 45) < tolerance or abs(angle - 135) < tolerance:
        return 'diagonal'

    return 'other'


def filter_duplicate_lines(lines: List[Line],
                           position_threshold: int = 5,
                           angle_threshold: float = 5.0) -> List[Line]:
    """
    Remove duplicate or nearly-duplicate lines

    Two lines are considered duplicates if they have:
    - Similar positions (endpoints within threshold)
    - Similar angles

    Args:
        lines: List of detected lines
        position_threshold: Maximum pixel distance for duplicate detection
        angle_threshold: Maximum angle difference in degrees

    Returns:
        Filtered list of unique lines
    """
    if not lines:
        return []

    unique_lines = []

    for line in lines:
        is_duplicate = False

        for existing in unique_lines:
            # Check if lines are similar
            pos_dist = (
                abs(line.x1 - existing.x1) +
                abs(line.y1 - existing.y1) +
                abs(line.x2 - existing.x2) +
                abs(line.y2 - existing.y2)
            ) / 4.0

            angle_diff = min(
                abs(line.angle - existing.angle),
                180 - abs(line.angle - existing.angle)
            )

            if pos_dist < position_threshold and angle_diff < angle_threshold:
                # Keep the longer line
                if line.length > existing.length:
                    unique_lines.remove(existing)
                    unique_lines.append(line)
                is_duplicate = True
                break

        if not is_duplicate:
            unique_lines.append(line)

    return unique_lines


def point_to_line_distance(px: float, py: float, line: Line) -> float:
    """
    Calculate perpendicular distance from point to infinite line

    Args:
        px, py: Point coordinates
        line: Line segment (treated as infinite line)

    Returns:
        Perpendicular distance
    """
    x1, y1, x2, y2 = line.x1, line.y1, line.x2, line.y2

    # Line direction vector
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2)

    # Perpendicular distance formula
    num = abs(dy * px - dx * py + x2 * y1 - y2 * x1)
    den = math.sqrt(dx * dx + dy * dy)

    return num / den


def are_lines_collinear(line1: Line, line2: Line,
                        angle_threshold: float = 5.0,
                        distance_threshold: float = 10.0) -> bool:
    """
    Check if two lines are collinear (on the same infinite line)

    Args:
        line1, line2: Lines to check
        angle_threshold: Maximum angle difference in degrees
        distance_threshold: Maximum perpendicular distance in pixels

    Returns:
        True if lines are collinear
    """
    # Check angle similarity
    angle_diff = min(
        abs(line1.angle - line2.angle),
        180 - abs(line1.angle - line2.angle)
    )

    if angle_diff > angle_threshold:
        return False

    # Check if endpoints of line2 are close to the infinite line of line1
    dist1 = point_to_line_distance(line2.x1, line2.y1, line1)
    dist2 = point_to_line_distance(line2.x2, line2.y2, line1)

    if dist1 > distance_threshold or dist2 > distance_threshold:
        return False

    return True


def lines_gap_distance(line1: Line, line2: Line) -> float:
    """
    Calculate the gap distance between two line segments

    Returns the minimum distance between the endpoints of the two lines.
    If lines overlap or touch, returns 0.

    Args:
        line1, line2: Line segments

    Returns:
        Gap distance in pixels
    """
    # Get all endpoints
    p1_start = (line1.x1, line1.y1)
    p1_end = (line1.x2, line1.y2)
    p2_start = (line2.x1, line2.y1)
    p2_end = (line2.x2, line2.y2)

    # Calculate all endpoint-to-endpoint distances
    distances = [
        math.sqrt((p1_end[0] - p2_start[0])**2 + (p1_end[1] - p2_start[1])**2),
        math.sqrt((p1_end[0] - p2_end[0])**2 + (p1_end[1] - p2_end[1])**2),
        math.sqrt((p1_start[0] - p2_start[0])**2 + (p1_start[1] - p2_start[1])**2),
        math.sqrt((p1_start[0] - p2_end[0])**2 + (p1_start[1] - p2_end[1])**2),
    ]

    return min(distances)


def merge_two_lines(line1: Line, line2: Line) -> Line:
    """
    Merge two collinear line segments into one

    Args:
        line1, line2: Lines to merge

    Returns:
        Merged line spanning both input lines
    """
    # Get all endpoints
    points = [
        (line1.x1, line1.y1),
        (line1.x2, line1.y2),
        (line2.x1, line2.y1),
        (line2.x2, line2.y2)
    ]

    # For horizontal/vertical lines, find extremes
    if line1.orientation == 'horizontal':
        # Find leftmost and rightmost points
        points.sort(key=lambda p: p[0])
        x1, y1 = points[0]
        x2, y2 = points[-1]
    elif line1.orientation == 'vertical':
        # Find topmost and bottommost points
        points.sort(key=lambda p: p[1])
        x1, y1 = points[0]
        x2, y2 = points[-1]
    else:
        # For diagonal/other, find most distant points
        max_dist = 0
        best_pair = (points[0], points[1])
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                dist = math.sqrt(
                    (points[i][0] - points[j][0])**2 +
                    (points[i][1] - points[j][1])**2
                )
                if dist > max_dist:
                    max_dist = dist
                    best_pair = (points[i], points[j])
        (x1, y1), (x2, y2) = best_pair

    # Calculate new length and angle
    length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    if angle < 0:
        angle += 180

    return Line(
        x1=int(x1),
        y1=int(y1),
        x2=int(x2),
        y2=int(y2),
        length=length,
        angle=angle,
        orientation=line1.orientation
    )


def merge_collinear_lines(lines: List[Line],
                          gap_threshold: int = 55,
                          angle_threshold: float = 5.0,
                          distance_threshold: float = 10.0) -> List[Line]:
    """
    Merge collinear line segments that are close together

    This is essential for converting dashed lines into solid lines.

    Args:
        lines: List of detected lines
        gap_threshold: Maximum gap between lines to merge (pixels)
        angle_threshold: Maximum angle difference for collinearity (degrees)
        distance_threshold: Maximum perpendicular distance for collinearity (pixels)

    Returns:
        List of merged lines
    """
    if not lines:
        return []

    # Group lines by orientation for efficiency
    groups = {
        'horizontal': [],
        'vertical': [],
        'diagonal': [],
        'other': []
    }

    for line in lines:
        groups[line.orientation].append(line)

    merged_lines = []

    # Process each orientation group separately
    for orientation, group_lines in groups.items():
        if not group_lines:
            continue

        # Track which lines have been merged
        used = [False] * len(group_lines)

        for i in range(len(group_lines)):
            if used[i]:
                continue

            # Start with this line
            current_line = group_lines[i]
            used[i] = True
            merged_any = True

            # Keep trying to merge until no more merges possible
            while merged_any:
                merged_any = False

                for j in range(len(group_lines)):
                    if used[j]:
                        continue

                    candidate = group_lines[j]

                    # Check if lines are collinear
                    if not are_lines_collinear(current_line, candidate,
                                              angle_threshold, distance_threshold):
                        continue

                    # Check gap distance
                    gap = lines_gap_distance(current_line, candidate)
                    if gap > gap_threshold:
                        continue

                    # Merge the lines
                    current_line = merge_two_lines(current_line, candidate)
                    used[j] = True
                    merged_any = True

            merged_lines.append(current_line)

    return merged_lines


def visualize_lines(image_path: str, lines: List[Line], output_path: str):
    """
    Create visualization of detected lines

    Colors:
    - Blue: Horizontal lines
    - Red: Vertical lines
    - Green: Diagonal lines
    - Gray: Other orientations

    Args:
        image_path: Path to original image
        lines: Detected lines
        output_path: Path to save visualization
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to load image: {image_path}")
        return

    overlay = image.copy()

    # Define colors for different orientations
    orientation_colors = {
        'horizontal': (255, 0, 0),    # Blue
        'vertical': (0, 0, 255),      # Red
        'diagonal': (0, 255, 0),      # Green
        'other': (128, 128, 128)      # Gray
    }

    # Draw lines
    for idx, line in enumerate(lines):
        color = orientation_colors.get(line.orientation, (128, 128, 128))
        cv2.line(overlay, (line.x1, line.y1), (line.x2, line.y2), color, 2)

        # Add line index label at midpoint
        mid_x = (line.x1 + line.x2) // 2
        mid_y = (line.y1 + line.y2) // 2

        # Draw text with background for readability
        label = f"{idx}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1

        (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        # Background rectangle
        cv2.rectangle(overlay,
                     (mid_x - 2, mid_y - text_height - 2),
                     (mid_x + text_width + 2, mid_y + 2),
                     (255, 255, 255), -1)

        # Text
        cv2.putText(overlay, label, (mid_x, mid_y),
                   font, font_scale, (0, 0, 0), thickness)

    # Add legend
    legend_y = 30
    legend_x = 10
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6

    cv2.putText(overlay, "Line Orientations:", (legend_x, legend_y),
               font, font_scale, (0, 0, 0), 2)

    legend_items = [
        ("Horizontal", (255, 0, 0)),
        ("Vertical", (0, 0, 255)),
        ("Diagonal", (0, 255, 0)),
        ("Other", (128, 128, 128))
    ]

    for i, (label, color) in enumerate(legend_items):
        y = legend_y + 30 + i * 25
        cv2.line(overlay, (legend_x, y), (legend_x + 30, y), color, 3)
        cv2.putText(overlay, label, (legend_x + 40, y + 5),
                   font, 0.5, (0, 0, 0), 1)

    # Save visualization
    cv2.imwrite(output_path, overlay)
    print(f"✓ Saved visualization: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Detect line segments in schematic images using LSD'
    )
    parser.add_argument('--image', required=True,
                       help='Input image (text-masked or fully-masked schematic)')
    parser.add_argument('--output', required=True,
                       help='Output JSON file for detected lines')
    parser.add_argument('--min-length', type=int, default=12,
                       help='Minimum line length in pixels (default: 12)')
    parser.add_argument('--lsd-scale', type=float, default=0.8,
                       help='LSD scale parameter (default: 0.8)')
    parser.add_argument('--lsd-sigma', type=float, default=0.6,
                       help='LSD sigma scale parameter (default: 0.6)')
    parser.add_argument('--angle-tolerance', type=float, default=15.0,
                       help='Angle tolerance for orientation classification (default: 15°)')
    parser.add_argument('--filter-duplicates', action='store_true',
                       help='Remove duplicate lines')
    parser.add_argument('--merge-lines', action='store_true', default=True,
                       help='Merge collinear lines (dashed lines → solid lines) (default: True)')
    parser.add_argument('--no-merge-lines', dest='merge_lines', action='store_false',
                       help='Disable line merging')
    parser.add_argument('--merge-gap', type=int, default=55,
                       help='Maximum gap for merging dashed lines (default: 55px)')
    parser.add_argument('--visualize', action='store_true',
                       help='Create visualization image')

    args = parser.parse_args()

    print("Schematic Line Detection")
    print("=" * 60)

    # Load image
    print(f"\n1. Loading image: {args.image}")
    image = cv2.imread(args.image)
    if image is None:
        print(f"✗ Failed to load image")
        return

    print(f"   Image size: {image.shape[1]}x{image.shape[0]}")

    # Detect lines
    print(f"\n2. Detecting lines (min_length={args.min_length}px)")
    lines = detect_lines(image, args.min_length, args.lsd_scale, args.lsd_sigma)
    print(f"   Detected: {len(lines)} raw line segments")

    step_num = 3

    # Merge collinear lines (dashed → solid)
    if args.merge_lines:
        print(f"\n{step_num}. Merging collinear lines (dashed → solid, gap≤{args.merge_gap}px)")
        before = len(lines)
        lines = merge_collinear_lines(lines, gap_threshold=args.merge_gap)
        print(f"   Before: {before} segments")
        print(f"   After:  {len(lines)} merged lines")
        print(f"   Merged: {before - len(lines)} segments into continuous lines")
        step_num += 1

    # Filter duplicates if requested
    if args.filter_duplicates:
        print(f"\n{step_num}. Filtering duplicate lines")
        before = len(lines)
        lines = filter_duplicate_lines(lines)
        print(f"   Removed {before - len(lines)} duplicates")
        print(f"   Remaining: {len(lines)} unique lines")
        step_num += 1

    # Count by orientation
    orientation_counts = {
        'horizontal': 0,
        'vertical': 0,
        'diagonal': 0,
        'other': 0
    }

    for line in lines:
        orientation_counts[line.orientation] += 1

    print(f"\n📊 Line Statistics:")
    print(f"   Total lines: {len(lines)}")
    print(f"   Horizontal: {orientation_counts['horizontal']}")
    print(f"   Vertical: {orientation_counts['vertical']}")
    print(f"   Diagonal: {orientation_counts['diagonal']}")
    print(f"   Other: {orientation_counts['other']}")

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert lines to list of dicts (with index)
    lines_data = []
    for idx, line in enumerate(lines):
        line_dict = asdict(line)
        line_dict['index'] = idx
        lines_data.append(line_dict)

    data = {
        'image': args.image,
        'min_length': args.min_length,
        'lsd_scale': args.lsd_scale,
        'lsd_sigma_scale': args.lsd_sigma,
        'angle_tolerance': args.angle_tolerance,
        'merge_lines': args.merge_lines,
        'merge_gap': args.merge_gap if args.merge_lines else None,
        'total_lines': len(lines),
        'orientation_counts': orientation_counts,
        'lines': lines_data
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Saved line data: {output_path}")

    # Visualize
    if args.visualize:
        print(f"\n{step_num}. Creating visualization")
        vis_path = str(output_path).replace('.json', '_visualization.png')
        visualize_lines(args.image, lines, vis_path)


if __name__ == '__main__':
    main()
