#!/usr/bin/env python3
"""
Text Masking - Mask text from schematic images for clean line detection
Reads text bounding boxes from CSV and masks them out with white rectangles
Optionally crops to schematic boundary before processing

Usage:
  python3 create_text_masked_schematic.py \
    --image "extraction_results/system_10/pages/10_page1.png" \
    --csv "extraction_results/system_10/visual_3_final/detections_with_visual_ids.csv" \
    --output "extraction_results/system_10/masked/page_001_text_masked.png" \
    --page-number 1 \
    --boundary "extraction_results/system_10/boundary_dimensions.json"
"""

import cv2
import numpy as np
import csv
import json
import argparse
from pathlib import Path


def load_boundary_dimensions(json_path: str):
    """
    Load schematic boundary dimensions from JSON

    Args:
        json_path: Path to boundary dimensions JSON file

    Returns:
        Dictionary with x, y, width, height or None if file not found
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            return data.get('schematic_boundary')
    except FileNotFoundError:
        print(f"⚠ Boundary file not found: {json_path}")
        return None


def crop_image_to_boundary(image: np.ndarray, boundary: dict):
    """
    Crop image to schematic boundary

    Args:
        image: Input image
        boundary: Dictionary with x, y, width, height

    Returns:
        Cropped image
    """
    x = boundary['x']
    y = boundary['y']
    w = boundary['width']
    h = boundary['height']

    # Ensure bounds are within image
    x = max(0, x)
    y = max(0, y)
    w = min(w, image.shape[1] - x)
    h = min(h, image.shape[0] - y)

    cropped = image[y:y+h, x:x+w]
    return cropped


def adjust_boxes_to_crop(boxes: list, boundary: dict):
    """
    Adjust text box coordinates relative to cropped area

    Args:
        boxes: List of (x, y, width, height, text) tuples
        boundary: Dictionary with x, y, width, height of crop area

    Returns:
        List of adjusted boxes that fall within the crop area
    """
    crop_x = boundary['x']
    crop_y = boundary['y']
    crop_w = boundary['width']
    crop_h = boundary['height']

    adjusted_boxes = []

    for x, y, w, h, text in boxes:
        # Check if box overlaps with crop area
        if (x + w < crop_x or x > crop_x + crop_w or
            y + h < crop_y or y > crop_y + crop_h):
            continue  # Box is outside crop area

        # Adjust coordinates relative to crop
        new_x = x - crop_x
        new_y = y - crop_y

        # Clip to crop boundaries
        new_x = max(0, new_x)
        new_y = max(0, new_y)

        # Adjust width/height if box extends beyond crop
        if new_x + w > crop_w:
            w = crop_w - new_x
        if new_y + h > crop_h:
            h = crop_h - new_y

        if w > 0 and h > 0:
            adjusted_boxes.append((new_x, new_y, w, h, text))

    return adjusted_boxes


def load_text_boxes(csv_path: str, page_number: int = None):
    """
    Load text bounding boxes from CSV

    Args:
        csv_path: Path to CSV with text detections
        page_number: Optional filter for specific page

    Returns:
        List of bounding box tuples (x, y, width, height, text)
    """
    boxes = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter by page if specified
            if page_number is not None and int(row['page_number']) != page_number:
                continue

            x = int(row['x'])
            y = int(row['y'])
            w = int(row['width'])
            h = int(row['height'])
            text = row['text'].strip()

            boxes.append((x, y, w, h, text))

    print(f"Loaded {len(boxes)} text boxes from CSV")
    return boxes


def mask_text_boxes(image: np.ndarray, boxes: list, padding: int = 3):
    """
    Mask text bounding boxes with white rectangles

    Args:
        image: Input image (BGR format)
        boxes: List of (x, y, width, height, text) tuples
        padding: Extra pixels to add around each box

    Returns:
        Masked image
    """
    masked = image.copy()

    for x, y, w, h, text in boxes:
        # Add padding
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(image.shape[1], x + w + padding)
        y2 = min(image.shape[0], y + h + padding)

        # Fill with white
        cv2.rectangle(masked, (x1, y1), (x2, y2), (255, 255, 255), -1)

    return masked


def main():
    parser = argparse.ArgumentParser(description='Mask text from schematic images')
    parser.add_argument('--image', required=True, help='Input schematic image')
    parser.add_argument('--csv', required=True, help='CSV file with text detections')
    parser.add_argument('--output', required=True, help='Output masked image path')
    parser.add_argument('--page-number', type=int, help='Page number to process')
    parser.add_argument('--padding', type=int, default=3,
                       help='Extra pixels to mask around text (default: 3)')
    parser.add_argument('--boundary', help='JSON file with schematic boundary dimensions')

    args = parser.parse_args()

    print("Text Masking with Boundary Cropping")
    print("=" * 60)

    # Load image
    print(f"\n1. Loading image: {args.image}")
    image = cv2.imread(args.image)
    if image is None:
        print(f"✗ Failed to load image")
        return

    print(f"   Original image size: {image.shape[1]}x{image.shape[0]}")

    # Load boundary and crop if specified
    boundary = None
    if args.boundary:
        print(f"\n2. Loading boundary dimensions: {args.boundary}")
        boundary = load_boundary_dimensions(args.boundary)
        if boundary:
            print(f"   Boundary: x={boundary['x']}, y={boundary['y']}, "
                  f"w={boundary['width']}, h={boundary['height']}")
            print(f"\n3. Cropping to schematic boundary...")
            original_image = image
            image = crop_image_to_boundary(image, boundary)
            print(f"   Cropped image size: {image.shape[1]}x{image.shape[0]}")

    # Load text boxes
    step = 3 if boundary is None else 4
    print(f"\n{step}. Loading text boxes: {args.csv}")
    boxes = load_text_boxes(args.csv, args.page_number)

    # Adjust boxes if cropped
    if boundary:
        original_count = len(boxes)
        boxes = adjust_boxes_to_crop(boxes, boundary)
        print(f"   Adjusted {len(boxes)}/{original_count} boxes to crop area")

    if not boxes:
        print(f"\n⚠ No text boxes found in crop area, saving cropped image as-is")
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), image)
        return

    # Mask text
    step += 1
    print(f"\n{step}. Masking {len(boxes)} text boxes (padding={args.padding}px)")
    masked = mask_text_boxes(image, boxes, args.padding)

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
    if boundary:
        print(f"   Crop area: {boundary['width']}x{boundary['height']}")
    print(f"   Total pixels: {total_pixels:,}")
    print(f"   Masked pixels: {masked_pixels:,} ({masked_percent:.2f}%)")
    print(f"   Text boxes masked: {len(boxes)}")


if __name__ == '__main__':
    main()
