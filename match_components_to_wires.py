#!/usr/bin/env python3
"""
Component-Wire Matching - Match components to wires based on proximity
Identifies which wires connect to which component pins/terminals

Usage:
  python3 match_components_to_wires.py \
    --components "extraction_results/system_10/components/page_001_boxes.json" \
    --wires "extraction_results/system_10/wires/page_001_wires.json" \
    --output "extraction_results/system_10/connections/page_001_connections.json"
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import math


def load_json(path: str) -> dict:
    """Load JSON file"""
    with open(path, 'r') as f:
        return json.load(f)


def point_to_segment_distance(px: float, py: float,
                               x1: float, y1: float,
                               x2: float, y2: float) -> float:
    """
    Calculate minimum distance from point to line segment

    Args:
        px, py: Point coordinates
        x1, y1, x2, y2: Line segment endpoints

    Returns:
        Minimum distance from point to segment
    """
    # Vector from start to end
    dx = x2 - x1
    dy = y2 - y1

    # Handle degenerate case (zero-length segment)
    if dx == 0 and dy == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2)

    # Calculate parameter t for closest point on infinite line
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)

    # Clamp t to [0, 1] to stay on segment
    t = max(0, min(1, t))

    # Calculate closest point on segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    # Return distance to closest point
    return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)


def get_box_edges(box: dict) -> Dict[str, Tuple[float, float, float, float]]:
    """
    Get the four edges of a component box

    Args:
        box: Component box dictionary with box_x1, box_y1, box_x2, box_y2

    Returns:
        Dictionary of edge name -> (x1, y1, x2, y2)
    """
    x1, y1 = box['box_x1'], box['box_y1']
    x2, y2 = box['box_x2'], box['box_y2']

    return {
        'top': (x1, y1, x2, y1),
        'bottom': (x1, y2, x2, y2),
        'left': (x1, y1, x1, y2),
        'right': (x2, y1, x2, y2)
    }


def segment_to_segment_distance(seg1: Tuple[float, float, float, float],
                                  seg2: Tuple[float, float, float, float]) -> float:
    """
    Calculate minimum distance between two line segments

    Args:
        seg1: First segment (x1, y1, x2, y2)
        seg2: Second segment (x1, y1, x2, y2)

    Returns:
        Minimum distance between segments
    """
    x1a, y1a, x2a, y2a = seg1
    x1b, y1b, x2b, y2b = seg2

    # Check all endpoint-to-segment distances
    distances = [
        point_to_segment_distance(x1a, y1a, x1b, y1b, x2b, y2b),
        point_to_segment_distance(x2a, y2a, x1b, y1b, x2b, y2b),
        point_to_segment_distance(x1b, y1b, x1a, y1a, x2a, y2a),
        point_to_segment_distance(x2b, y2b, x1a, y1a, x2a, y2a)
    ]

    return min(distances)


def find_wire_connections(component: dict, wires: List[dict],
                           proximity_threshold: float = 10.0) -> List[dict]:
    """
    Find wires that connect to a component

    Args:
        component: Component box dictionary
        wires: List of wire dictionaries
        proximity_threshold: Maximum distance for connection (pixels)

    Returns:
        List of connection dictionaries
    """
    connections = []
    edges = get_box_edges(component)

    for wire in wires:
        wire_seg = (wire['x1'], wire['y1'], wire['x2'], wire['y2'])

        # Check distance to each edge
        for edge_name, edge_seg in edges.items():
            distance = segment_to_segment_distance(wire_seg, edge_seg)

            if distance <= proximity_threshold:
                # Find connection point (midpoint of closest approach)
                # For simplicity, use edge midpoint as connection point
                edge_mid_x = (edge_seg[0] + edge_seg[2]) / 2
                edge_mid_y = (edge_seg[1] + edge_seg[3]) / 2

                connection = {
                    'component_id': component.get('component_id', component.get('symbol', 'unknown')),
                    'component_symbol': component.get('symbol', 'unknown'),
                    'component_box': {
                        'x1': component['box_x1'],
                        'y1': component['box_y1'],
                        'x2': component['box_x2'],
                        'y2': component['box_y2']
                    },
                    'wire_id': wire['id'],
                    'wire_segment': {
                        'x1': wire['x1'],
                        'y1': wire['y1'],
                        'x2': wire['x2'],
                        'y2': wire['y2']
                    },
                    'connection_side': edge_name,
                    'connection_point': {
                        'x': edge_mid_x,
                        'y': edge_mid_y
                    },
                    'distance': round(distance, 2),
                    'wire_orientation': wire.get('orientation', 'unknown')
                }

                connections.append(connection)
                break  # Only count each wire once per component

    return connections


def group_connections_by_component(all_connections: List[dict]) -> Dict[str, List[dict]]:
    """
    Group connections by component

    Args:
        all_connections: List of all connection dictionaries

    Returns:
        Dictionary of component_id -> list of connections
    """
    grouped = {}

    for conn in all_connections:
        comp_id = conn['component_id']
        if comp_id not in grouped:
            grouped[comp_id] = []
        grouped[comp_id].append(conn)

    return grouped


def analyze_connections(connections: List[dict]) -> dict:
    """
    Analyze connection statistics

    Args:
        connections: List of all connections

    Returns:
        Dictionary of statistics
    """
    if not connections:
        return {
            'total_connections': 0,
            'unique_components': 0,
            'unique_wires': 0,
            'connections_by_side': {}
        }

    unique_components = set(c['component_id'] for c in connections)
    unique_wires = set(c['wire_id'] for c in connections)

    # Count by side
    by_side = {}
    for conn in connections:
        side = conn['connection_side']
        by_side[side] = by_side.get(side, 0) + 1

    # Count by component
    by_component = {}
    for conn in connections:
        comp_id = conn['component_id']
        by_component[comp_id] = by_component.get(comp_id, 0) + 1

    return {
        'total_connections': len(connections),
        'unique_components': len(unique_components),
        'unique_wires': len(unique_wires),
        'connections_by_side': by_side,
        'connections_per_component': {
            'min': min(by_component.values()) if by_component else 0,
            'max': max(by_component.values()) if by_component else 0,
            'avg': sum(by_component.values()) / len(by_component) if by_component else 0
        }
    }


def main():
    parser = argparse.ArgumentParser(description='Match components to wires')
    parser.add_argument('--components', required=True, help='Component boxes JSON file')
    parser.add_argument('--wires', required=True, help='Wires JSON file')
    parser.add_argument('--output', required=True, help='Output connections JSON file')
    parser.add_argument('--proximity', type=float, default=10.0,
                       help='Maximum distance for wire-component connection (pixels, default: 10.0)')
    parser.add_argument('--verbose', action='store_true',
                       help='Print detailed connection information')

    args = parser.parse_args()

    print("Component-Wire Matching")
    print("=" * 60)

    # Load components
    print(f"\n1. Loading components: {args.components}")
    components_data = load_json(args.components)
    components = components_data.get('boxes', [])
    print(f"   Found {len(components)} components")

    # Load wires
    print(f"\n2. Loading wires: {args.wires}")
    wires_data = load_json(args.wires)
    wires = wires_data.get('lines', [])
    print(f"   Found {len(wires)} wires")

    # Find connections
    print(f"\n3. Matching wires to components (proximity={args.proximity}px)")
    all_connections = []

    for i, component in enumerate(components):
        connections = find_wire_connections(component, wires, args.proximity)
        all_connections.extend(connections)

        if args.verbose and connections:
            symbol = component.get('symbol', 'unknown')
            print(f"   {symbol}: {len(connections)} wire(s)")

    print(f"\n   Total connections found: {len(all_connections)}")

    # Group by component
    grouped = group_connections_by_component(all_connections)

    # Analyze
    print(f"\n4. Analyzing connections")
    stats = analyze_connections(all_connections)

    print(f"\n📊 Statistics:")
    print(f"   Total connections: {stats['total_connections']}")
    print(f"   Unique components: {stats['unique_components']}")
    print(f"   Unique wires: {stats['unique_wires']}")
    print(f"\n   Connections by side:")
    for side, count in sorted(stats['connections_by_side'].items()):
        print(f"     {side}: {count}")

    if stats['connections_per_component']['max'] > 0:
        print(f"\n   Connections per component:")
        print(f"     Min: {stats['connections_per_component']['min']}")
        print(f"     Max: {stats['connections_per_component']['max']}")
        print(f"     Avg: {stats['connections_per_component']['avg']:.1f}")

    # Save output
    output_data = {
        'metadata': {
            'components_file': args.components,
            'wires_file': args.wires,
            'proximity_threshold': args.proximity,
            'total_components': len(components),
            'total_wires': len(wires),
            'total_connections': len(all_connections)
        },
        'statistics': stats,
        'connections': all_connections,
        'grouped_by_component': grouped
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ Saved connections: {output_path}")

    # Print warnings
    if stats['total_connections'] == 0:
        print("\n⚠ Warning: No connections found!")
        print("   Try increasing --proximity threshold or check input data")

    # Find unconnected components
    connected_components = set(c['component_id'] for c in all_connections)
    unconnected = [c for c in components
                   if c.get('component_id', c.get('symbol', 'unknown')) not in connected_components]

    if unconnected:
        print(f"\n⚠ Warning: {len(unconnected)} component(s) have no wire connections:")
        for comp in unconnected[:5]:  # Show first 5
            print(f"   - {comp.get('symbol', 'unknown')}")
        if len(unconnected) > 5:
            print(f"   ... and {len(unconnected) - 5} more")


if __name__ == '__main__':
    main()
