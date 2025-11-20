#!/usr/bin/env python3
"""
Text Masking - Mask text from schematic images for clean line detection
Reads text bounding boxes from CSV and masks them out with white rectangles

Usage:
  python3 create_text_masked_schematic.py \
    --image "extraction_results/system_10/pages/10_page1.png" \
    --csv "extraction_results/system_10/visual_3_final/detections_with_visual_ids.csv" \
    --output "extraction_results/system_10/masked/page_001_text_masked.png" \
    --page-number 1
"""

import cv2
import numpy as np
import csv
import argparse
from pathlib import Path


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

    args = parser.parse_args()

    print("Text Masking")
    print("=" * 60)

    # Load image
    print(f"\n1. Loading image: {args.image}")
    image = cv2.imread(args.image)
    if image is None:
        print(f"✗ Failed to load image")
        return

    print(f"   Image size: {image.shape[1]}x{image.shape[0]}")

    # Load text boxes
    print(f"\n2. Loading text boxes: {args.csv}")
    boxes = load_text_boxes(args.csv, args.page_number)

    if not boxes:
        print(f"\n⚠ No text boxes found, copying image as-is")
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), image)
        return

    # Mask text
    print(f"\n3. Masking {len(boxes)} text boxes (padding={args.padding}px)")
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
    print(f"   Total pixels: {total_pixels:,}")
    print(f"   Masked pixels: {masked_pixels:,} ({masked_percent:.2f}%)")
    print(f"   Text boxes: {len(boxes)}")


if __name__ == '__main__':
    main()
