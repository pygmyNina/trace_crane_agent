#!/usr/bin/env python3
"""
Component Box Detection - Detect component bounding boxes using label-anchored rectangle tracing
Uses component label positions + detected lines to find rectangular component boundaries

Algorithm:
1. Start from component label position (e.g., "-U1")
2. Find closest vertical line to the RIGHT of the label (can be slightly above/below)
3. Trace connected lines to form a rectangle
4. Return component bounding box

Usage:
  python3 detect_component_boxes.py \
    --text-csv "extraction_results/system_10/visual_3_final/detections_with_visual_ids.csv" \
    --line-json "extraction_results/system_10/lines/page_001_all_lines.json" \
    --output "extraction_results/system_10/components/page_001_boxes.json" \
    --page-number 1 \
    --boundary "extraction_results/system_10/boundary_dimensions.json" \
    --visualize \
    --image "extraction_results/system_10/pages/10_page1.png"
"""

import cv2
import numpy as np
import json
import csv
import argparse
import math
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class Component:
    """Component detected from text extraction"""
    symbol: str  # e.g., "-SG1", "-CB1"
    label_x: int
    label_y: int
    label_width: int
    label_height: int
    label_center_x: int
    label_center_y: int
    page_number: int


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
    index: int  # Original index in lines array


@dataclass
class ComponentBox:
    """Detected component bounding box"""
    symbol: str
    label_center_x: int
    label_center_y: int
    box_x1: int
    box_y1: int
    box_x2: int
    box_y2: int
    box_width: int
    box_height: int
    traced_lines: List[int]  # Indices of lines that form the box
    confidence: str  # 'high', 'medium', 'low'
    detection_method: str  # Description of how box was detected


def load_boundary(boundary_file: str) -> Tuple[int, int, int, int]:
    """
    Load green schematic boundary from JSON file

    Returns:
        Tuple of (x, y, width, height) for schematic boundary
    """
    with open(boundary_file, 'r') as f:
        data = json.load(f)

    sb = data['schematic_boundary']
    boundary = (sb['x'], sb['y'], sb['width'], sb['height'])
    return boundary


def is_component(text: str) -> bool:
    """Check if text is a component symbol (starts with - but not -W for wires)"""
    if not text or len(text) < 2:
        return False

    # Starts with - but not -W (wire numbers)
    if text.startswith('-') and not text.startswith('-W'):
        return True

    return False


def filter_components_by_boundary(components: List[Component],
                                  boundary: Tuple[int, int, int, int]) -> List[Component]:
    """
    Filter components to only those within the schematic boundary

    Args:
        components: List of all components
        boundary: (x, y, width, height) of schematic area

    Returns:
        Filtered list of components within boundary
    """
    x, y, w, h = boundary
    filtered = []

    for component in components:
        # Check if component label center is within boundary
        if (x <= component.label_center_x <= x + w and
            y <= component.label_center_y <= y + h):
            filtered.append(component)

    return filtered


def load_components(csv_path: str, page_number: int = None) -> List[Component]:
    """
    Load component positions from text detection CSV

    Args:
        csv_path: Path to CSV with text detections
        page_number: Optional filter for specific page

    Returns:
        List of Component objects
    """
    components = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter by page if specified
            if page_number is not None and int(row['page_number']) != page_number:
                continue

            text = row['text'].strip()

            # Check if it's a component
            if not is_component(text):
                continue

            x = int(row['x'])
            y = int(row['y'])
            w = int(row['width'])
            h = int(row['height'])

            component = Component(
                symbol=text,
                label_x=x,
                label_y=y,
                label_width=w,
                label_height=h,
                label_center_x=x + w // 2,
                label_center_y=y + h // 2,
                page_number=int(row['page_number'])
            )
            components.append(component)

    print(f"Loaded {len(components)} components from CSV")
    return components


def load_lines(json_path: str) -> List[Line]:
    """
    Load detected lines from line detection JSON

    Args:
        json_path: Path to line detection JSON

    Returns:
        List of Line objects
    """
    with open(json_path, 'r') as f:
        data = json.load(f)

    lines = []
    for idx, line_data in enumerate(data['lines']):
        line = Line(
            x1=line_data['x1'],
            y1=line_data['y1'],
            x2=line_data['x2'],
            y2=line_data['y2'],
            length=line_data['length'],
            angle=line_data['angle'],
            orientation=line_data['orientation'],
            index=idx
        )
        lines.append(line)

    print(f"Loaded {len(lines)} lines from JSON")
    return lines


def distance_point_to_line_segment(px: int, py: int, line: Line) -> float:
    """
    Calculate minimum distance from point to line segment

    Args:
        px, py: Point coordinates
        line: Line segment

    Returns:
        Minimum distance in pixels
    """
    x1, y1, x2, y2 = line.x1, line.y1, line.x2, line.y2

    # Vector from line start to point
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        # Line is a point
        return math.sqrt((px - x1)**2 + (py - y1)**2)

    # Parameter t for closest point on infinite line
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))

    # Closest point on line segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    # Distance to closest point
    return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)


def find_closest_vertical_line_to_right(component: Component, lines: List[Line],
                                        max_distance: int = 500,
                                        vertical_tolerance: int = 100) -> Optional[Line]:
    """
    Find the first vertical line to the RIGHT of the component label
    No vertical distance restriction - just the closest line horizontally

    Args:
        component: Component with label position
        lines: All detected lines
        max_distance: Maximum horizontal distance to search (default: 500px)
        vertical_tolerance: Not used, kept for API compatibility

    Returns:
        Closest vertical line to the right, or None
    """
    closest_line = None
    closest_distance = float('inf')

    for line in lines:
        # Only consider vertical lines (angle within 15° of 90°)
        if line.orientation != 'vertical':
            continue

        # Get average x position of the vertical line
        line_x = (line.x1 + line.x2) / 2

        # Only consider lines to the RIGHT of the label
        if line_x <= component.label_x:
            continue

        # Calculate horizontal distance
        horizontal_distance = line_x - component.label_x

        # Check max distance limit
        if horizontal_distance > max_distance:
            continue

        # Track the closest line horizontally
        if horizontal_distance < closest_distance:
            closest_distance = horizontal_distance
            closest_line = line

    return closest_line


def are_lines_connected(line1: Line, line2: Line, tolerance: int = 10) -> Optional[Tuple[int, int]]:
    """
    Check if two lines are connected (share an endpoint)

    Args:
        line1, line2: Lines to check
        tolerance: Pixel tolerance for connection detection

    Returns:
        Connection point (x, y) if connected, None otherwise
    """
    endpoints1 = [(line1.x1, line1.y1), (line1.x2, line1.y2)]
    endpoints2 = [(line2.x1, line2.y1), (line2.x2, line2.y2)]

    for ep1 in endpoints1:
        for ep2 in endpoints2:
            dist = math.sqrt((ep1[0] - ep2[0])**2 + (ep1[1] - ep2[1])**2)
            if dist <= tolerance:
                # Use average of the two endpoints for connection point
                conn_x = (ep1[0] + ep2[0]) // 2
                conn_y = (ep1[1] + ep2[1]) // 2
                return (conn_x, conn_y)

    return None


def are_lines_connected_corner(line1: Line, line2: Line,
                                horizontal_tolerance: int = 48,
                                vertical_tolerance: int = 56) -> Optional[Tuple[int, int]]:
    """
    Check if two lines are connected at a corner with asymmetric tolerances
    for handling incomplete/dashed corners

    Uses different tolerances for horizontal vs vertical gaps to better handle
    typical dashed line patterns at corners.

    Args:
        line1, line2: Lines to check
        horizontal_tolerance: Max horizontal gap for corner connection (default: 48px)
        vertical_tolerance: Max vertical gap for corner connection (default: 56px)

    Returns:
        Connection point (x, y) if connected, None otherwise
    """
    endpoints1 = [(line1.x1, line1.y1), (line1.x2, line1.y2)]
    endpoints2 = [(line2.x1, line2.y1), (line2.x2, line2.y2)]

    for ep1 in endpoints1:
        for ep2 in endpoints2:
            dx = abs(ep1[0] - ep2[0])
            dy = abs(ep1[1] - ep2[1])

            # Check if within asymmetric tolerance
            if dx <= horizontal_tolerance and dy <= vertical_tolerance:
                # Use average of the two endpoints for connection point
                conn_x = (ep1[0] + ep2[0]) // 2
                conn_y = (ep1[1] + ep2[1]) // 2
                return (conn_x, conn_y)

    return None


def find_connected_lines(line: Line, all_lines: List[Line],
                        orientation: str = None, tolerance: int = 10,
                        use_corner_merge: bool = True,
                        corner_h_tolerance: int = 48,
                        corner_v_tolerance: int = 56) -> List[Tuple[Line, Tuple[int, int]]]:
    """
    Find all lines connected to the given line

    Args:
        line: Line to find connections for
        all_lines: All available lines
        orientation: Optional filter for orientation ('horizontal', 'vertical')
        tolerance: Pixel tolerance for connection detection
        use_corner_merge: Enable corner merge for incomplete corners
        corner_h_tolerance: Horizontal tolerance for corner merge (default: 48px)
        corner_v_tolerance: Vertical tolerance for corner merge (default: 56px)

    Returns:
        List of (connected_line, connection_point) tuples
    """
    connected = []

    for other_line in all_lines:
        if other_line.index == line.index:
            continue

        if orientation and other_line.orientation != orientation:
            continue

        # Try standard connection first
        connection_point = are_lines_connected(line, other_line, tolerance)
        if connection_point:
            connected.append((other_line, connection_point))
        elif use_corner_merge:
            # If standard connection fails, try corner merge for incomplete corners
            connection_point = are_lines_connected_corner(line, other_line,
                                                          corner_h_tolerance,
                                                          corner_v_tolerance)
            if connection_point:
                connected.append((other_line, connection_point))

    return connected


def trace_rectangle(start_line: Line, all_lines: List[Line],
                   component: Component, tolerance: int = 10,
                   use_corner_merge: bool = True,
                   corner_h_tolerance: int = 48,
                   corner_v_tolerance: int = 56) -> Optional[ComponentBox]:
    """
    Trace a rectangle starting from a vertical line (assumed to be left edge)

    Algorithm:
    1. Start with left vertical edge (closest to right of label)
    2. Find horizontal lines connected to top/bottom
    3. Follow horizontal lines to find right vertical edge
    4. Verify rectangle closure

    Args:
        start_line: Starting vertical line (left edge)
        all_lines: All available lines
        component: Component label information
        tolerance: Pixel tolerance for connections
        use_corner_merge: Enable corner merge for incomplete corners
        corner_h_tolerance: Horizontal tolerance for corner merge (default: 48px)
        corner_v_tolerance: Vertical tolerance for corner merge (default: 56px)

    Returns:
        ComponentBox if rectangle found, None otherwise
    """
    # Start line should be vertical (left edge)
    if start_line.orientation != 'vertical':
        return None

    left_edge = start_line
    traced_lines = [left_edge.index]

    # Find horizontal lines connected to the left edge
    horizontal_connected = find_connected_lines(left_edge, all_lines,
                                                orientation='horizontal',
                                                tolerance=tolerance,
                                                use_corner_merge=use_corner_merge,
                                                corner_h_tolerance=corner_h_tolerance,
                                                corner_v_tolerance=corner_v_tolerance)

    if len(horizontal_connected) < 2:
        # Need at least top and bottom edges
        return None

    # Separate into top and bottom edges (by y position)
    horizontal_connected.sort(key=lambda x: x[1][1])  # Sort by y coordinate

    top_edge = horizontal_connected[0][0]
    bottom_edge = horizontal_connected[-1][0]

    traced_lines.extend([top_edge.index, bottom_edge.index])

    # Find right vertical edge connected to both top and bottom
    top_verticals = find_connected_lines(top_edge, all_lines,
                                         orientation='vertical',
                                         tolerance=tolerance,
                                         use_corner_merge=use_corner_merge,
                                         corner_h_tolerance=corner_h_tolerance,
                                         corner_v_tolerance=corner_v_tolerance)
    bottom_verticals = find_connected_lines(bottom_edge, all_lines,
                                           orientation='vertical',
                                           tolerance=tolerance,
                                           use_corner_merge=use_corner_merge,
                                           corner_h_tolerance=corner_h_tolerance,
                                           corner_v_tolerance=corner_v_tolerance)

    # Find common vertical line (right edge)
    right_edge = None
    for top_v, _ in top_verticals:
        for bottom_v, _ in bottom_verticals:
            if top_v.index == bottom_v.index and top_v.index != left_edge.index:
                right_edge = top_v
                break
        if right_edge:
            break

    if not right_edge:
        # No complete rectangle found
        return None

    traced_lines.append(right_edge.index)

    # Calculate bounding box from the four edges
    x_coords = [right_edge.x1, right_edge.x2, left_edge.x1, left_edge.x2,
                top_edge.x1, top_edge.x2, bottom_edge.x1, bottom_edge.x2]
    y_coords = [right_edge.y1, right_edge.y2, left_edge.y1, left_edge.y2,
                top_edge.y1, top_edge.y2, bottom_edge.y1, bottom_edge.y2]

    box_x1 = min(x_coords)
    box_y1 = min(y_coords)
    box_x2 = max(x_coords)
    box_y2 = max(y_coords)

    box = ComponentBox(
        symbol=component.symbol,
        label_center_x=component.label_center_x,
        label_center_y=component.label_center_y,
        box_x1=box_x1,
        box_y1=box_y1,
        box_x2=box_x2,
        box_y2=box_y2,
        box_width=box_x2 - box_x1,
        box_height=box_y2 - box_y1,
        traced_lines=traced_lines,
        confidence='high',
        detection_method='label-anchored rectangle tracing'
    )

    return box


def detect_component_boxes(components: List[Component], lines: List[Line],
                          tolerance: int = 10, max_search_distance: int = 500,
                          vertical_search_tolerance: int = 100,
                          use_corner_merge: bool = True,
                          corner_h_tolerance: int = 48,
                          corner_v_tolerance: int = 56) -> List[ComponentBox]:
    """
    Detect component bounding boxes using label-anchored rectangle tracing

    Args:
        components: List of components with label positions
        lines: List of detected lines
        tolerance: Pixel tolerance for line connections
        max_search_distance: Maximum horizontal distance to search for vertical line
        vertical_search_tolerance: Maximum vertical distance for line search (default: 100px)
        use_corner_merge: Enable corner merge for incomplete corners
        corner_h_tolerance: Horizontal tolerance for corner merge (default: 48px)
        corner_v_tolerance: Vertical tolerance for corner merge (default: 56px)

    Returns:
        List of detected component boxes
    """
    detected_boxes = []

    for component in components:
        # Find closest vertical line to the right
        closest_vertical = find_closest_vertical_line_to_right(component, lines,
                                                               max_search_distance,
                                                               vertical_search_tolerance)

        if not closest_vertical:
            print(f"  {component.symbol}: No vertical line found to right")
            continue

        # Try to trace a rectangle from this vertical line
        box = trace_rectangle(closest_vertical, lines, component, tolerance,
                             use_corner_merge, corner_h_tolerance, corner_v_tolerance)

        if box:
            detected_boxes.append(box)
            print(f"  {component.symbol}: ✓ Box detected {box.box_width}x{box.box_height} at ({box.box_x1}, {box.box_y1})")
        else:
            print(f"  {component.symbol}: ✗ Could not trace complete rectangle")

    return detected_boxes


def visualize_component_boxes(image_path: str, components: List[Component],
                              boxes: List[ComponentBox], lines: List[Line],
                              output_path: str):
    """
    Create visualization of detected component boxes

    Args:
        image_path: Path to original schematic image
        components: All components
        boxes: Detected component boxes
        lines: All detected lines
        output_path: Path to save visualization
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to load image: {image_path}")
        return

    # Create overlay
    overlay = image.copy()

    # Draw all lines in light gray with ID labels
    for line in lines:
        color = (200, 200, 200)  # Light gray
        cv2.line(overlay, (line.x1, line.y1), (line.x2, line.y2), color, 1)

        # Add line ID label at midpoint
        mid_x = (line.x1 + line.x2) // 2
        mid_y = (line.y1 + line.y2) // 2

        # Draw ID with background for readability
        label = f"{line.index}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.3
        thickness = 1

        # Get text size for background
        (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        # Draw background rectangle
        cv2.rectangle(overlay,
                     (mid_x - 2, mid_y - text_height - 2),
                     (mid_x + text_width + 2, mid_y + 2),
                     (255, 255, 255), -1)  # White background

        # Draw text
        cv2.putText(overlay, label, (mid_x, mid_y),
                   font, font_scale, (128, 128, 128), thickness)  # Gray text

    # Draw detected boxes
    for box in boxes:
        # Draw bounding box
        cv2.rectangle(overlay, (box.box_x1, box.box_y1), (box.box_x2, box.box_y2),
                     (0, 255, 0), 2)  # Green box

        # Draw label position
        cv2.circle(overlay, (box.label_center_x, box.label_center_y), 3, (255, 0, 0), -1)  # Blue dot

        # Draw label
        label_text = f"{box.symbol}"
        cv2.putText(overlay, label_text, (box.box_x1, box.box_y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Save visualization
    cv2.imwrite(output_path, overlay)
    print(f"\n✓ Saved visualization: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Detect component boxes using label-anchored rectangle tracing')
    parser.add_argument('--text-csv', required=True, help='Path to text detection CSV')
    parser.add_argument('--line-json', required=True, help='Path to line detection JSON')
    parser.add_argument('--output', required=True, help='Output JSON path for component boxes')
    parser.add_argument('--page-number', type=int, help='Page number to process')
    parser.add_argument('--boundary', help='Path to boundary_dimensions.json to limit detection to schematic area')
    parser.add_argument('--tolerance', type=int, default=10, help='Pixel tolerance for line connections')
    parser.add_argument('--max-search-distance', type=int, default=500,
                       help='Maximum horizontal distance to search for vertical line (default: 500px)')
    parser.add_argument('--vertical-search-tolerance', type=int, default=100,
                       help='Maximum vertical distance for line search (default: 100px)')
    parser.add_argument('--corner-merge', action='store_true', default=True,
                       help='Enable corner merge for incomplete/dashed corners (default: True)')
    parser.add_argument('--no-corner-merge', dest='corner_merge', action='store_false',
                       help='Disable corner merge feature')
    parser.add_argument('--corner-h-tolerance', type=int, default=48,
                       help='Horizontal tolerance for corner merge (default: 48px)')
    parser.add_argument('--corner-v-tolerance', type=int, default=56,
                       help='Vertical tolerance for corner merge (default: 56px)')
    parser.add_argument('--visualize', action='store_true', help='Create visualization image')
    parser.add_argument('--image', help='Original schematic image (required for visualization)')

    args = parser.parse_args()

    print("Component Box Detection")
    print("=" * 60)

    # Load data
    print("\n1. Loading components and lines")
    components = load_components(args.text_csv, args.page_number)
    lines = load_lines(args.line_json)

    # Filter by boundary if provided
    if args.boundary:
        print(f"\n2. Applying schematic boundary filter")
        boundary = load_boundary(args.boundary)
        print(f"   Boundary: {boundary[2]}x{boundary[3]} at ({boundary[0]}, {boundary[1]})")
        components_before = len(components)
        components = filter_components_by_boundary(components, boundary)
        print(f"   Filtered: {len(components)} / {components_before} components within boundary")
        step_num = 3
    else:
        step_num = 2

    # Detect boxes
    corner_status = "enabled" if args.corner_merge else "disabled"
    print(f"\n{step_num}. Detecting component boxes (tolerance={args.tolerance}px, corner_merge={corner_status})")
    print(f"   Search window: {args.max_search_distance}px (H) x {args.vertical_search_tolerance}px (V)")
    if args.corner_merge:
        print(f"   Corner merge tolerances: {args.corner_h_tolerance}px (H) x {args.corner_v_tolerance}px (V)")
    boxes = detect_component_boxes(components, lines, args.tolerance, args.max_search_distance,
                                   args.vertical_search_tolerance,
                                   args.corner_merge, args.corner_h_tolerance, args.corner_v_tolerance)

    print(f"\n✓ Detected {len(boxes)} / {len(components)} component boxes")

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'text_csv': args.text_csv,
        'line_json': args.line_json,
        'page_number': args.page_number,
        'boundary': args.boundary,
        'total_components': len(components),
        'detected_boxes': len(boxes),
        'boxes': [asdict(box) for box in boxes]
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Saved component boxes: {output_path}")

    # Visualize
    if args.visualize:
        if not args.image:
            print("\n✗ --image required for visualization")
            return

        step_num += 1
        print(f"\n{step_num}. Creating visualization")
        vis_path = str(output_path).replace('.json', '_visualization.png')
        visualize_component_boxes(args.image, components, boxes, lines, vis_path)


if __name__ == '__main__':
    main()
