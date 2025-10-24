#!/usr/bin/env python3
"""
PDF diagnostic tool - checks if PDF can be read
"""

import sys

def check_pdf(pdf_path):
    """Check if PDF can be read by various libraries"""

    print(f"\n{'='*60}")
    print(f"PDF Diagnostic: {pdf_path}")
    print('='*60)

    # Try pypdf
    print("\n1. Testing with pypdf...")
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        print(f"   ✓ pypdf can read the file")
        print(f"   Pages detected: {len(reader.pages)}")
    except Exception as e:
        print(f"   ✗ pypdf error: {e}")

    # Try PyPDF2
    print("\n2. Testing with PyPDF2...")
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        print(f"   ✓ PyPDF2 can read the file")
        print(f"   Pages detected: {len(reader.pages)}")
    except Exception as e:
        print(f"   ✗ PyPDF2 error: {e}")

    # Try pdf2image
    print("\n3. Testing with pdf2image...")
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        print(f"   ✓ pdf2image can convert the file")
        print(f"   Successfully converted page 1")
    except Exception as e:
        print(f"   ✗ pdf2image error: {e}")

    # File info
    print("\n4. File information...")
    import os
    if os.path.exists(pdf_path):
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        print(f"   File exists: Yes")
        print(f"   File size: {size_mb:.2f} MB")
    else:
        print(f"   File exists: No")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_pdf.py <path-to-pdf>")
        sys.exit(1)

    check_pdf(sys.argv[1])
