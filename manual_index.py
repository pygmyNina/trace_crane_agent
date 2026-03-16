#!/usr/bin/env python3
"""
Manual indexing helper for PDFs that have page count issues
"""

import sys
import os

# Load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from trace.section_manager import SectionManager
from trace.pdf_image_converter import PDFImageConverter
from trace.vision_analyzer import VisionAnalyzer


def manual_index(pdf_path, section, num_pages):
    """Manually index a PDF by specifying the number of pages"""

    print(f"\nManual Indexing Tool")
    print("="*60)
    print(f"PDF: {pdf_path}")
    print(f"Section: {section}")
    print(f"Pages: {num_pages}")
    print("="*60 + "\n")

    if not os.path.exists(pdf_path):
        print(f"✗ PDF not found: {pdf_path}")
        return

    # Initialize components
    mgr = SectionManager()
    converter = PDFImageConverter()
    vision = VisionAnalyzer()

    if not vision.check_api_available():
        print("✗ Vision API not configured. Set ANTHROPIC_API_KEY.")
        return

    pdf_name = os.path.basename(pdf_path)

    # Check if PDF is already loaded in section
    if section not in mgr.registry["sections"]:
        mgr.registry["sections"][section] = {}

    if pdf_name not in mgr.registry["sections"][section]:
        # Load PDF first
        print(f"Loading PDF into section '{section}'...")
        import shutil
        section_dir = os.path.join(mgr.base_dir, section)
        target_path = os.path.join(section_dir, pdf_name)
        shutil.copy2(pdf_path, target_path)

        mgr.registry["sections"][section][pdf_name] = {
            "path": target_path,
            "total_pages": num_pages,
            "loaded_at": __import__('datetime').datetime.now().isoformat(),
            "indexed": False,
            "pages": {}
        }
        mgr._save_registry()
        print(f"✓ Loaded: {pdf_name}")

    pdf_info = mgr.registry["sections"][section][pdf_name]
    pdf_info["total_pages"] = num_pages  # Override page count

    # Index each page
    print(f"\n🔍 Indexing {num_pages} pages...\n")

    indexed_count = 0
    for page_num in range(1, num_pages + 1):
        print(f"  Page {page_num}/{num_pages}: Analyzing...", end=" ", flush=True)

        # Convert page to image
        image_path = converter.convert_page(pdf_info["path"], page_num)
        if not image_path:
            print("✗ Conversion failed")
            continue

        # Index with Vision API
        page_data = vision.index_page(image_path, page_num)
        if not page_data:
            print("✗ Indexing failed")
            continue

        # Store in registry
        pdf_info["pages"][str(page_num)] = page_data
        indexed_count += 1

        # Show summary
        ref_count = len(page_data.get("references", []))
        comp_count = len(page_data.get("components", []))
        print(f"✓ ({ref_count} refs, {comp_count} components)")

    # Update registry
    pdf_info["indexed"] = True
    pdf_info["indexed_at"] = __import__('datetime').datetime.now().isoformat()
    mgr._save_registry()

    print(f"\n✓ Indexed {indexed_count}/{num_pages} pages")
    print(f"\nNow you can query this PDF in TRACE:")
    print(f"  TRACE> query {pdf_name}")
    print(f"  TRACE> ask <question about this schematic>")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("\nUsage: python3 manual_index.py <pdf_path> <section> <num_pages>")
        print("\nExample:")
        print('  python3 manual_index.py "/path/to/10.pdf" electrical 3')
        print("\nValid sections: electrical, hydraulic, mechanical, controls, general")
        print()
        sys.exit(1)

    pdf_path = sys.argv[1]
    section = sys.argv[2]
    num_pages = int(sys.argv[3])

    manual_index(pdf_path, section, num_pages)
