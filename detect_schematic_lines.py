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
                 min_length: int = 20,
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
    parser.add_argument('--min-length', type=int, default=20,
                       help='Minimum line length in pixels (default: 20)')
    parser.add_argument('--lsd-scale', type=float, default=0.8,
                       help='LSD scale parameter (default: 0.8)')
    parser.add_argument('--lsd-sigma', type=float, default=0.6,
                       help='LSD sigma scale parameter (default: 0.6)')
    parser.add_argument('--angle-tolerance', type=float, default=15.0,
                       help='Angle tolerance for orientation classification (default: 15°)')
    parser.add_argument('--filter-duplicates', action='store_true',
                       help='Remove duplicate lines')
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
    print(f"   Detected: {len(lines)} lines")

    # Filter duplicates if requested
    if args.filter_duplicates:
        print(f"\n3. Filtering duplicate lines")
        before = len(lines)
        lines = filter_duplicate_lines(lines)
        print(f"   Removed {before - len(lines)} duplicates")
        print(f"   Remaining: {len(lines)} unique lines")

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
        'total_lines': len(lines),
        'orientation_counts': orientation_counts,
        'lines': lines_data
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Saved line data: {output_path}")

    # Visualize
    if args.visualize:
        print(f"\n4. Creating visualization")
        vis_path = str(output_path).replace('.json', '_visualization.png')
        visualize_lines(args.image, lines, vis_path)


if __name__ == '__main__':
    main()
