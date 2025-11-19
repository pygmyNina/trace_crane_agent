#!/usr/bin/env python3
"""
Component Box Masking - Mask out detected component boxes from schematic images
Prepares clean images for wire detection by removing component boundaries

Usage:
  python3 mask_component_boxes.py \
    --image "extraction_results/system_10/masked/page_001_text_masked.png" \
    --boxes "extraction_results/system_10/components/page_001_boxes.json" \
    --output "extraction_results/system_10/masked/page_001_full_masked.png" \
    --padding 5
"""

import cv2
import numpy as np
import json
import argparse
from pathlib import Path
from typing import List, Tuple


def load_component_boxes(json_path: str) -> List[dict]:
    """
    Load component boxes from JSON

    Args:
        json_path: Path to component boxes JSON

    Returns:
        List of component box dictionaries
    """
    with open(json_path, 'r') as f:
        data = json.load(f)

    boxes = data.get('boxes', [])
    print(f"Loaded {len(boxes)} component boxes from JSON")
    return boxes


def mask_component_boxes(image: np.ndarray, boxes: List[dict],
                         padding: int = 5, fill_color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """
    Mask out component boxes from image

    Args:
        image: Input image (BGR format)
        boxes: List of component box dictionaries
        padding: Extra pixels to add around each box
        fill_color: Color to fill masked regions (default white)

    Returns:
        Masked image
    """
    masked = image.copy()

    for box in boxes:
        x1 = max(0, box['box_x1'] - padding)
        y1 = max(0, box['box_y1'] - padding)
        x2 = min(image.shape[1], box['box_x2'] + padding)
        y2 = min(image.shape[0], box['box_y2'] + padding)

        # Fill the rectangle
        cv2.rectangle(masked, (x1, y1), (x2, y2), fill_color, -1)  # -1 = filled

        print(f"  Masked {box['symbol']}: [{x1}, {y1}, {x2}, {y2}]")

    return masked


def create_mask_visualization(original: np.ndarray, masked: np.ndarray,
                              boxes: List[dict], output_path: str):
    """
    Create side-by-side visualization of masking

    Args:
        original: Original image
        masked: Masked image
        boxes: Component boxes
        output_path: Path to save visualization
    """
    # Resize images if too large
    max_height = 1200
    if original.shape[0] > max_height:
        scale = max_height / original.shape[0]
        new_width = int(original.shape[1] * scale)
        new_height = int(original.shape[0] * scale)
        original = cv2.resize(original, (new_width, new_height))
        masked = cv2.resize(masked, (new_width, new_height))

    # Create side-by-side comparison
    vis = np.hstack([original, masked])

    # Draw component boxes on original side
    for box in boxes:
        x1 = box['box_x1']
        y1 = box['box_y1']
        x2 = box['box_x2']
        y2 = box['box_y2']

        # Scale if needed
        if original.shape[0] != masked.shape[0]:
            scale = masked.shape[0] / original.shape[0]
            x1, y1, x2, y2 = int(x1*scale), int(y1*scale), int(x2*scale), int(y2*scale)

        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(vis, box['symbol'], (x1, y1-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Add labels
    cv2.putText(vis, "Before (Text Masked)", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(vis, "After (Text + Components Masked)", (original.shape[1] + 10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imwrite(output_path, vis)
    print(f"\n✓ Saved visualization: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Mask component boxes from schematic images')
    parser.add_argument('--image', required=True, help='Input image (text-masked schematic)')
    parser.add_argument('--boxes', required=True, help='Component boxes JSON file')
    parser.add_argument('--output', required=True, help='Output masked image path')
    parser.add_argument('--padding', type=int, default=5,
                       help='Extra pixels to mask around each box (default: 5)')
    parser.add_argument('--fill-color', type=int, nargs=3, default=[255, 255, 255],
                       help='Fill color as R G B (default: 255 255 255 = white)')
    parser.add_argument('--visualize', action='store_true',
                       help='Create before/after visualization')

    args = parser.parse_args()

    print("Component Box Masking")
    print("=" * 60)

    # Load image
    print(f"\n1. Loading image: {args.image}")
    image = cv2.imread(args.image)
    if image is None:
        print(f"✗ Failed to load image")
        return

    print(f"   Image size: {image.shape[1]}x{image.shape[0]}")

    # Load boxes
    print(f"\n2. Loading component boxes: {args.boxes}")
    boxes = load_component_boxes(args.boxes)

    if not boxes:
        print(f"\n⚠ No component boxes found, copying image as-is")
        cv2.imwrite(args.output, image)
        return

    # Mask boxes
    print(f"\n3. Masking {len(boxes)} component boxes (padding={args.padding}px)")
    fill_color = tuple(args.fill_color[::-1])  # RGB -> BGR
    masked = mask_component_boxes(image, boxes, args.padding, fill_color)

    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), masked)

    print(f"\n✓ Saved masked image: {output_path}")

    # Calculate statistics
    total_pixels = image.shape[0] * image.shape[1]
    diff = cv2.absdiff(image, masked)
    masked_pixels = np.count_nonzero(diff)
    masked_percent = (masked_pixels / total_pixels) * 100

    print(f"\n📊 Statistics:")
    print(f"   Total pixels: {total_pixels:,}")
    print(f"   Masked pixels: {masked_pixels:,} ({masked_percent:.2f}%)")
    print(f"   Component boxes: {len(boxes)}")

    # Visualize
    if args.visualize:
        print("\n4. Creating visualization")
        vis_path = str(output_path).replace('.png', '_comparison.png')
        create_mask_visualization(image, masked, boxes, vis_path)


if __name__ == '__main__':
    main()
