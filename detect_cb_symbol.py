#!/usr/bin/env python3
"""
Detect Circuit Breaker (CB) Symbols in Schematics

CB symbols consist of:
- Text label "-CB1", "-CB2", etc.
- Symbol with circles (2 per pole) to the right of the label
- Diagonal lines representing breaker contacts
- 1-pole = 2 circles, 2-pole = 4 circles, 3-pole = 6 circles

This script:
1. Finds "-CB" labels from text CSV
2. Detects circles near each label using HoughCircles
3. Creates bounding box around the detected symbol

Usage:
  python3 detect_cb_symbol.py \
    --text-csv "extraction_results/system_10/visual_3_final/detections_with_visual_ids.csv" \
    --image "extraction_results/system_10/pages/10_page1.png" \
    --output "extraction_results/system_10/components/cb_components.json" \
    --page-number 1 \
    --boundary "extraction_results/system_10/boundary_dimensions.json" \
    --visualize
"""

import cv2
import numpy as np
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class CBLabel:
    """CB label from text detection"""
    symbol: str           # e.g., "-CB1"
    x: int
    y: int
    width: int
    height: int
    center_x: int
    center_y: int
    page_number: int


@dataclass
class CBComponent:
    """Detected CB component with symbol"""
    symbol: str
    label_x: int
    label_y: int
    label_width: int
    label_height: int
    box_x1: int
    box_y1: int
    box_x2: int
    box_y2: int
    box_width: int
    box_height: int
    num_circles: int
    num_poles: int        # 1, 2, or 3 based on circle count
    circles: List[Tuple[int, int, int]]  # [(x, y, radius), ...]
    confidence: str
    source: str


def load_boundary(boundary_file: str) -> Tuple[int, int, int, int]:
    """Load schematic boundary from JSON file"""
    with open(boundary_file, 'r') as f:
        data = json.load(f)
    sb = data['schematic_boundary']
    return (sb['x'], sb['y'], sb['width'], sb['height'])


def load_cb_labels(csv_path: str, page_number: int = None,
                   boundary: Tuple[int, int, int, int] = None) -> List[CBLabel]:
    """
    Load CB labels from text detection CSV

    Args:
        csv_path: Path to text detection CSV
        page_number: Optional filter for specific page
        boundary: Optional (x, y, w, h) to filter and adjust coordinates

    Returns:
        List of CBLabel objects
    """
    labels = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter by page if specified
            if page_number is not None and int(row['page_number']) != page_number:
                continue

            text = row['text'].strip()

            # Check if it's a CB component
            if not text.startswith('-CB'):
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

            label = CBLabel(
                symbol=text,
                x=x,
                y=y,
                width=w,
                height=h,
                center_x=center_x,
                center_y=center_y,
                page_number=int(row['page_number'])
            )
            labels.append(label)

    return labels


def detect_circles_for_cb(image: np.ndarray,
                          label: CBLabel,
                          search_width: int = 250,
                          search_up: int = 50,
                          search_down: int = 25,
                          min_radius: int = 3,
                          max_radius: int = 20,
                          debug: bool = False) -> List[Tuple[int, int, int]]:
    """
    Detect circles to the right of a CB label

    Args:
        image: Input image (BGR or grayscale)
        label: CB label with position
        search_width: How far right to search from label (default: 250px)
        search_up: How far above label to search (default: 50px)
        search_down: How far below label to search (default: 25px)
        min_radius: Minimum circle radius (default: 3px)
        max_radius: Maximum circle radius (default: 20px)
        debug: Print debug info

    Returns:
        List of (x, y, radius) tuples for detected circles
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    h, w = gray.shape[:2]

    # Define search region to the RIGHT of the label
    # Extend more downward than upward (CB symbols typically extend below)
    roi_x1 = label.x + label.width
    roi_y1 = max(0, label.y - search_up)
    roi_x2 = min(w, roi_x1 + search_width)
    roi_y2 = min(h, label.y + label.height + search_down)

    if debug:
        print(f"    Search region: ({roi_x1}, {roi_y1}) to ({roi_x2}, {roi_y2})")

    # Extract ROI
    roi = gray[roi_y1:roi_y2, roi_x1:roi_x2]

    if roi.size == 0:
        if debug:
            print(f"    Empty ROI")
        return []

    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(roi, (5, 5), 0)

    # Detect circles
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=15,
        param1=50,
        param2=25,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    detected = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            # Convert ROI coordinates back to image coordinates
            cx = int(circle[0]) + roi_x1
            cy = int(circle[1]) + roi_y1
            radius = int(circle[2])
            detected.append((cx, cy, radius))

    if debug:
        print(f"    Found {len(detected)} circles")
        for cx, cy, r in detected:
            print(f"      Circle at ({cx}, {cy}) radius={r}")

    return detected


def detect_cb_components(labels: List[CBLabel],
                         image: np.ndarray,
                         search_width: int = 250,
                         search_up: int = 50,
                         search_down: int = 25,
                         debug: bool = False) -> List[CBComponent]:
    """
    Detect CB components by finding circles near labels

    Args:
        labels: List of CB labels
        image: Schematic image
        search_width: How far right to search (default: 250px)
        search_up: How far above label to search (default: 50px)
        search_down: How far below label to search (default: 25px)
        debug: Print debug info

    Returns:
        List of CBComponent objects
    """
    components = []

    for label in labels:
        if debug:
            print(f"\n  {label.symbol}:")
            print(f"    Label at ({label.x}, {label.y}) size {label.width}x{label.height}")

        # Detect circles
        circles = detect_circles_for_cb(
            image, label,
            search_width=search_width,
            search_up=search_up,
            search_down=search_down,
            debug=debug
        )

        if len(circles) == 0:
            print(f"  {label.symbol}: ✗ No circles found")
            continue

        # Determine number of poles from circle count
        # 2 circles = 1 pole, 4 circles = 2 poles, 6 circles = 3 poles
        num_circles = len(circles)
        num_poles = max(1, num_circles // 2)

        # Create bounding box around label + circles
        all_x = [label.x, label.x + label.width]
        all_y = [label.y, label.y + label.height]

        for cx, cy, r in circles:
            all_x.extend([cx - r, cx + r])
            all_y.extend([cy - r, cy + r])

        padding = 10
        box_x1 = min(all_x) - padding
        box_y1 = min(all_y) - padding
        box_x2 = max(all_x) + padding
        box_y2 = max(all_y) + padding

        # Determine confidence
        if num_circles >= 2 and num_circles <= 6 and num_circles % 2 == 0:
            confidence = 'high'
        else:
            confidence = 'medium'

        component = CBComponent(
            symbol=label.symbol,
            label_x=label.x,
            label_y=label.y,
            label_width=label.width,
            label_height=label.height,
            box_x1=box_x1,
            box_y1=box_y1,
            box_x2=box_x2,
            box_y2=box_y2,
            box_width=box_x2 - box_x1,
            box_height=box_y2 - box_y1,
            num_circles=num_circles,
            num_poles=num_poles,
            circles=circles,
            confidence=confidence,
            source='circle_detection'
        )
        components.append(component)

        print(f"  {label.symbol}: ✓ Detected {num_poles}-pole CB ({num_circles} circles) "
              f"box {component.box_width}x{component.box_height} at ({box_x1}, {box_y1})")

    return components


def visualize_cb_detection(image_path: str,
                           components: List[CBComponent],
                           output_path: str,
                           boundary: Tuple[int, int, int, int] = None):
    """
    Create visualization of detected CB components
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to load image: {image_path}")
        return

    # Crop to boundary if provided
    if boundary is not None:
        bx, by, bw, bh = boundary
        image = image[by:by+bh, bx:bx+bw]

    overlay = image.copy()

    for comp in components:
        # Draw bounding box
        cv2.rectangle(overlay,
                     (comp.box_x1, comp.box_y1),
                     (comp.box_x2, comp.box_y2),
                     (0, 255, 0), 2)

        # Draw detected circles
        for cx, cy, r in comp.circles:
            cv2.circle(overlay, (cx, cy), r, (0, 0, 255), 2)
            cv2.circle(overlay, (cx, cy), 2, (0, 0, 255), -1)

        # Draw label
        label_text = f"{comp.symbol} ({comp.num_poles}-pole)"
        cv2.putText(overlay, label_text,
                   (comp.box_x1, comp.box_y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    cv2.imwrite(output_path, overlay)
    print(f"\n✓ Saved visualization: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Detect Circuit Breaker (CB) symbols using circle detection'
    )
    parser.add_argument('--text-csv', required=True, help='Path to text detection CSV')
    parser.add_argument('--image', required=True, help='Path to schematic image')
    parser.add_argument('--output', required=True, help='Output JSON path')
    parser.add_argument('--page-number', type=int, help='Page number to process')
    parser.add_argument('--boundary', help='Path to boundary_dimensions.json')
    parser.add_argument('--search-width', type=int, default=250,
                       help='How far right to search for circles (default: 250px)')
    parser.add_argument('--search-up', type=int, default=50,
                       help='How far above label to search (default: 50px)')
    parser.add_argument('--search-down', type=int, default=25,
                       help='How far below label to search (default: 25px)')
    parser.add_argument('--debug', action='store_true', help='Print debug info')
    parser.add_argument('--visualize', action='store_true', help='Create visualization')

    args = parser.parse_args()

    print("CB Symbol Detection")
    print("=" * 60)

    # Load boundary if provided
    boundary = None
    if args.boundary:
        boundary = load_boundary(args.boundary)
        print(f"Using boundary: {boundary[2]}x{boundary[3]} at ({boundary[0]}, {boundary[1]})")

    # Load CB labels from CSV
    print(f"\n1. Loading CB labels from: {args.text_csv}")
    labels = load_cb_labels(args.text_csv, args.page_number, boundary)
    print(f"   Found {len(labels)} CB labels")

    if len(labels) == 0:
        print("\n✗ No CB labels found")
        return

    # Load image
    print(f"\n2. Loading image: {args.image}")
    image = cv2.imread(args.image)
    if image is None:
        print(f"   ✗ Failed to load image")
        return
    print(f"   Image size: {image.shape[1]}x{image.shape[0]}")

    # Crop to boundary if provided
    if boundary is not None:
        bx, by, bw, bh = boundary
        image = image[by:by+bh, bx:bx+bw]
        print(f"   Cropped to boundary: {image.shape[1]}x{image.shape[0]}")

    # Detect CB components
    print(f"\n3. Detecting CB symbols (search: {args.search_width}px right, {args.search_up}px up, {args.search_down}px down)")
    components = detect_cb_components(
        labels, image,
        search_width=args.search_width,
        search_up=args.search_up,
        search_down=args.search_down,
        debug=args.debug
    )

    print(f"\n✓ Detected {len(components)} / {len(labels)} CB components")

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'source_csv': args.text_csv,
        'source_image': args.image,
        'page_number': args.page_number,
        'boundary': args.boundary,
        'search_width': args.search_width,
        'search_up': args.search_up,
        'search_down': args.search_down,
        'total_labels': len(labels),
        'detected_components': len(components),
        'components': [asdict(c) for c in components]
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Saved CB components: {output_path}")

    # Visualize
    if args.visualize:
        print(f"\n4. Creating visualization")
        vis_path = str(output_path).replace('.json', '_visualization.png')
        visualize_cb_detection(args.image, components, vis_path, boundary)


if __name__ == '__main__':
    main()
