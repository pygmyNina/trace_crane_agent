"""
Section Manager for TRACE
Manages section-based organization of schematic PDFs and auto-indexing
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from trace.pdf_image_converter import PDFImageConverter
from trace.vision_analyzer import VisionAnalyzer

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None


class SectionManager:
    """Manages schematic sections and PDF indexing"""

    VALID_SECTIONS = ['electrical', 'hydraulic', 'mechanical', 'controls', 'general']

    def __init__(self, base_dir: str = "schematics", registry_file: str = "schematic_registry.json"):
        self.base_dir = base_dir
        self.registry_file = registry_file
        self.converter = PDFImageConverter()
        self.vision = VisionAnalyzer()
        self.registry = self._load_registry()

        # Create section directories
        for section in self.VALID_SECTIONS:
            section_dir = os.path.join(self.base_dir, section)
            if not os.path.exists(section_dir):
                os.makedirs(section_dir)

    def _load_registry(self) -> Dict[str, Any]:
        """Load schematic registry from file"""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        else:
            return {"sections": {}}

    def _save_registry(self):
        """Save schematic registry to file"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def get_pdf_page_count(self, pdf_path: str) -> int:
        """Get number of pages in PDF"""
        if PdfReader is None:
            return 0

        try:
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except:
            return 0

    def load_pdf(self, section: str, pdf_path: str, auto_index: bool = False) -> Dict[str, Any]:
        """
        Load a PDF into a section

        Args:
            section: Section name (electrical, hydraulic, etc.)
            pdf_path: Path to PDF file
            auto_index: Whether to automatically index pages with Vision API

        Returns:
            Dictionary with load results
        """
        if section not in self.VALID_SECTIONS:
            return {
                "success": False,
                "error": f"Invalid section. Must be one of: {', '.join(self.VALID_SECTIONS)}"
            }

        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "error": f"PDF not found: {pdf_path}"
            }

        # Get PDF info
        pdf_name = os.path.basename(pdf_path)
        page_count = self.get_pdf_page_count(pdf_path)

        # Copy to section directory if not already there
        section_dir = os.path.join(self.base_dir, section)
        target_path = os.path.join(section_dir, pdf_name)

        if os.path.abspath(pdf_path) != os.path.abspath(target_path):
            import shutil
            shutil.copy2(pdf_path, target_path)

        # Initialize registry entry
        if section not in self.registry["sections"]:
            self.registry["sections"][section] = {}

        self.registry["sections"][section][pdf_name] = {
            "path": target_path,
            "total_pages": page_count,
            "loaded_at": datetime.now().isoformat(),
            "indexed": False,
            "pages": {}
        }

        self._save_registry()

        result = {
            "success": True,
            "section": section,
            "pdf_name": pdf_name,
            "pages": page_count,
            "indexed": False
        }

        # Auto-index if requested
        if auto_index:
            index_result = self.index_pdf(section, pdf_name)
            result["indexed"] = index_result.get("success", False)
            result["index_result"] = index_result

        return result

    def index_pdf(self, section: str, pdf_name: str, pages: List[int] = None) -> Dict[str, Any]:
        """
        Index PDF pages using Vision API

        Args:
            section: Section name
            pdf_name: PDF filename
            pages: Specific pages to index (None = all pages)

        Returns:
            Dictionary with indexing results
        """
        if not self.vision.check_api_available():
            return {
                "success": False,
                "error": "Vision API not available. Set ANTHROPIC_API_KEY environment variable."
            }

        # Get PDF from registry
        if section not in self.registry["sections"]:
            return {"success": False, "error": f"Section '{section}' not found"}

        if pdf_name not in self.registry["sections"][section]:
            return {"success": False, "error": f"PDF '{pdf_name}' not found in section '{section}'"}

        pdf_info = self.registry["sections"][section][pdf_name]
        pdf_path = pdf_info["path"]

        # Determine pages to index
        if pages is None:
            pages = list(range(1, pdf_info["total_pages"] + 1))

        print(f"\n🔍 Indexing {pdf_name} ({len(pages)} pages)...")

        indexed_count = 0
        errors = []

        for page_num in pages:
            print(f"  Page {page_num}/{pdf_info['total_pages']}: Analyzing...", end=" ")

            # Convert page to image
            image_path = self.converter.convert_page(pdf_path, page_num)
            if not image_path:
                errors.append(f"Page {page_num}: Failed to convert")
                print("✗ Conversion failed")
                continue

            # Index with Vision API
            page_data = self.vision.index_page(image_path, page_num)
            if not page_data:
                errors.append(f"Page {page_num}: Failed to index")
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
        pdf_info["indexed_at"] = datetime.now().isoformat()
        self._save_registry()

        return {
            "success": True,
            "section": section,
            "pdf_name": pdf_name,
            "pages_indexed": indexed_count,
            "total_pages": len(pages),
            "errors": errors
        }

    def search_registry(self, query: str) -> List[Dict[str, Any]]:
        """
        Search indexed pages for query term

        Args:
            query: Search term

        Returns:
            List of matching results
        """
        results = []
        query_lower = query.lower()

        for section, pdfs in self.registry["sections"].items():
            for pdf_name, pdf_info in pdfs.items():
                if not pdf_info.get("indexed"):
                    continue

                for page_num, page_data in pdf_info.get("pages", {}).items():
                    match = False
                    match_details = []

                    # Search in references
                    for ref in page_data.get("references", []):
                        if query_lower in ref.lower():
                            match = True
                            match_details.append(f"Reference: {ref}")

                    # Search in components
                    for comp in page_data.get("components", []):
                        if query_lower in comp.lower():
                            match = True
                            match_details.append(f"Component: {comp}")

                    # Search in cabinets
                    for cab in page_data.get("cabinets", []):
                        if query_lower in cab.lower():
                            match = True
                            match_details.append(f"Cabinet: {cab}")

                    # Search in summary
                    if query_lower in page_data.get("summary", "").lower():
                        match = True

                    if match:
                        results.append({
                            "section": section,
                            "pdf": pdf_name,
                            "page": int(page_num),
                            "summary": page_data.get("summary", ""),
                            "matches": match_details,
                            "references": page_data.get("references", []),
                            "components": page_data.get("components", [])
                        })

        return results

    def get_page_data(self, section: str, pdf_name: str, page_num: int) -> Optional[Dict[str, Any]]:
        """Get indexed data for a specific page"""
        try:
            return self.registry["sections"][section][pdf_name]["pages"][str(page_num)]
        except KeyError:
            return None

    def list_sections(self) -> Dict[str, List[str]]:
        """List all sections and their PDFs"""
        result = {}
        for section in self.VALID_SECTIONS:
            section_pdfs = self.registry["sections"].get(section, {})
            result[section] = list(section_pdfs.keys())
        return result

    def get_section_summary(self, section: str) -> Dict[str, Any]:
        """Get summary of a section"""
        if section not in self.registry["sections"]:
            return {"error": f"Section '{section}' not found"}

        pdfs = self.registry["sections"][section]
        total_pages = sum(pdf["total_pages"] for pdf in pdfs.values())
        indexed_pdfs = sum(1 for pdf in pdfs.values() if pdf.get("indexed"))

        return {
            "section": section,
            "pdf_count": len(pdfs),
            "total_pages": total_pages,
            "indexed_pdfs": indexed_pdfs,
            "pdfs": [
                {
                    "name": name,
                    "pages": pdf["total_pages"],
                    "indexed": pdf.get("indexed", False)
                }
                for name, pdf in pdfs.items()
            ]
        }

    def load_parts_list(self, section: str, pdf_path: str, auto_index: bool = False) -> Dict[str, Any]:
        """
        Load a parts list PDF into a section

        Args:
            section: Section name (electrical, hydraulic, etc.)
            pdf_path: Path to parts list PDF file
            auto_index: Whether to automatically index with Vision API

        Returns:
            Dictionary with load results
        """
        if section not in self.VALID_SECTIONS:
            return {
                "success": False,
                "error": f"Invalid section. Must be one of: {', '.join(self.VALID_SECTIONS)}"
            }

        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "error": f"PDF not found: {pdf_path}"
            }

        # Get PDF info
        pdf_name = os.path.basename(pdf_path)
        page_count = self.get_pdf_page_count(pdf_path)

        # Copy to section directory if not already there
        section_dir = os.path.join(self.base_dir, section)
        target_path = os.path.join(section_dir, pdf_name)

        if os.path.abspath(pdf_path) != os.path.abspath(target_path):
            import shutil
            shutil.copy2(pdf_path, target_path)

        # Initialize parts_lists section in registry
        if "parts_lists" not in self.registry:
            self.registry["parts_lists"] = {}

        if section not in self.registry["parts_lists"]:
            self.registry["parts_lists"][section] = {}

        self.registry["parts_lists"][section][pdf_name] = {
            "path": target_path,
            "total_pages": page_count,
            "loaded_at": datetime.now().isoformat(),
            "indexed": False,
            "parts": []
        }

        self._save_registry()

        result = {
            "success": True,
            "section": section,
            "pdf_name": pdf_name,
            "pages": page_count,
            "indexed": False
        }

        # Auto-index if requested
        if auto_index:
            index_result = self.index_parts_list(section, pdf_name)
            result["indexed"] = index_result.get("success", False)
            result["index_result"] = index_result

        return result

    def index_parts_list(self, section: str, pdf_name: str) -> Dict[str, Any]:
        """
        Index parts list PDF using Vision API

        Args:
            section: Section name
            pdf_name: Parts list PDF filename

        Returns:
            Dictionary with indexing results
        """
        if not self.vision.check_api_available():
            return {
                "success": False,
                "error": "Vision API not available. Set ANTHROPIC_API_KEY environment variable."
            }

        # Get parts list from registry
        if "parts_lists" not in self.registry:
            return {"success": False, "error": "No parts lists loaded"}

        if section not in self.registry["parts_lists"]:
            return {"success": False, "error": f"Section '{section}' has no parts lists"}

        if pdf_name not in self.registry["parts_lists"][section]:
            return {"success": False, "error": f"Parts list '{pdf_name}' not found in section '{section}'"}

        parts_info = self.registry["parts_lists"][section][pdf_name]
        pdf_path = parts_info["path"]
        total_pages = parts_info["total_pages"]

        # Try to extract section code from filename (e.g., "11_parts.pdf" -> "11")
        section_code = None
        import re
        match = re.match(r'^(\d+)[_\-]?parts', pdf_name.lower())
        if match:
            section_code = match.group(1)

        print(f"\n🔍 Indexing parts list {pdf_name} ({total_pages} pages)...")
        if section_code:
            print(f"  Section code detected: {section_code}")

        all_parts = []
        errors = []

        for page_num in range(1, total_pages + 1):
            print(f"  Page {page_num}/{total_pages}: Extracting parts...", end=" ")

            # Convert page to image
            image_path = self.converter.convert_page(pdf_path, page_num)
            if not image_path:
                errors.append(f"Page {page_num}: Failed to convert")
                print("✗ Conversion failed")
                continue

            # Extract parts with Vision API (pass section code for better OCR context)
            page_data = self.vision.extract_parts_list(image_path, page_num, section_code)
            if not page_data:
                errors.append(f"Page {page_num}: Failed to extract")
                print("✗ Extraction failed")
                continue

            # Add parts from this page
            parts_on_page = page_data.get("parts", [])
            all_parts.extend(parts_on_page)
            print(f"✓ ({len(parts_on_page)} parts)")

        # Store all parts in registry
        parts_info["parts"] = all_parts
        parts_info["indexed"] = True
        parts_info["indexed_at"] = datetime.now().isoformat()
        self._save_registry()

        return {
            "success": True,
            "section": section,
            "pdf_name": pdf_name,
            "total_parts": len(all_parts),
            "total_pages": total_pages,
            "errors": errors
        }

    def search_parts(self, query: str = None, symbol: str = None,
                     sheet: str = None, location: str = None) -> List[Dict[str, Any]]:
        """
        Search parts lists

        Args:
            query: Search term for description/identification
            symbol: Component symbol (e.g., -TR1, -CBTP)
            sheet: Sheet reference (e.g., =10/102.2)
            location: Location code (e.g., +HVC1)

        Returns:
            List of matching parts
        """
        results = []

        if "parts_lists" not in self.registry:
            return results

        for section, parts_lists in self.registry["parts_lists"].items():
            for pdf_name, parts_info in parts_lists.items():
                if not parts_info.get("indexed"):
                    continue

                for part in parts_info.get("parts", []):
                    match = True

                    # Filter by query (description or identification)
                    if query:
                        query_lower = query.lower()
                        desc_match = query_lower in part.get("description", "").lower()
                        ident_match = query_lower in part.get("identification", "").lower()
                        if not (desc_match or ident_match):
                            match = False

                    # Filter by symbol (exact match)
                    if symbol and symbol.lower() != part.get("symbol", "").lower():
                        match = False

                    # Filter by sheet
                    if sheet and sheet.lower() not in part.get("sheet_section", "").lower():
                        match = False

                    # Filter by location
                    if location and location.lower() not in part.get("location", "").lower():
                        match = False

                    if match:
                        result = part.copy()
                        result["section"] = section
                        result["parts_list"] = pdf_name
                        results.append(result)

        return results

    def export_index(self, output_file: str = "schematic_index_export.json"):
        """Export the full index to a file"""
        import shutil
        shutil.copy(self.registry_file, output_file)
        print(f"✓ Index exported to {output_file}")
