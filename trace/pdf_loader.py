"""
PDF Schematic Loader for TRACE
Loads and extracts information from crane schematic PDFs
"""

import os
from typing import List, Dict, Any, Optional
try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None


class PDFSchematicLoader:
    """Handles loading and parsing of crane schematic PDFs"""

    def __init__(self, schematics_dir: str = "schematics"):
        self.schematics_dir = schematics_dir
        if not os.path.exists(schematics_dir):
            os.makedirs(schematics_dir)

    def load_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Load a PDF and extract text content"""
        if PdfReader is None:
            return {
                "error": "PDF library not installed. Run: pip install pypdf",
                "path": pdf_path
            }

        if not os.path.exists(pdf_path):
            return {
                "error": f"PDF file not found: {pdf_path}",
                "path": pdf_path
            }

        try:
            reader = PdfReader(pdf_path)
            pages_text = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                pages_text.append({
                    "page_number": i + 1,
                    "text": text
                })

            return {
                "success": True,
                "path": pdf_path,
                "filename": os.path.basename(pdf_path),
                "num_pages": len(reader.pages),
                "pages": pages_text
            }

        except Exception as e:
            return {
                "error": f"Failed to load PDF: {str(e)}",
                "path": pdf_path
            }

    def list_schematics(self) -> List[str]:
        """List all PDF files in the schematics directory"""
        if not os.path.exists(self.schematics_dir):
            return []

        return [f for f in os.listdir(self.schematics_dir) if f.endswith('.pdf')]

    def extract_references(self, text: str) -> List[str]:
        """Extract schematic references in =XX/YY.Y.Z format"""
        import re
        # Pattern for =XX/YY.Y.Z format
        pattern = r'=\d+/\d+\.\d+\.\d+'
        return re.findall(pattern, text)

    def extract_component_info(self, pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract component information from PDF text"""
        components = {
            "slaves": [],
            "modules": [],
            "cabinets": [],
            "references": []
        }

        if not pdf_data.get("success"):
            return components

        for page in pdf_data.get("pages", []):
            text = page.get("text", "")

            # Extract references
            refs = self.extract_references(text)
            components["references"].extend(refs)

            # Look for slave mentions (this is a simple pattern, can be improved)
            import re
            slave_matches = re.findall(r'[Ss]lave\s+(\d+)', text)
            components["slaves"].extend(slave_matches)

            # Look for cabinet mentions
            cabinet_matches = re.findall(r'[Cc]abinet\s+([A-Z]\d+)', text)
            components["cabinets"].extend(cabinet_matches)

        # Remove duplicates
        components["slaves"] = list(set(components["slaves"]))
        components["cabinets"] = list(set(components["cabinets"]))
        components["references"] = list(set(components["references"]))

        return components
