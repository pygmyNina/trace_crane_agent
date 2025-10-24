"""
PDF Processing System for Crane Schematics
Handles PDF import, text extraction, and image processing
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import io
import re


class SchematicPDFProcessor:
    """Processes PDF schematics for TRACE training"""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.doc = fitz.open(str(self.pdf_path))
        self.num_pages = len(self.doc)
        self.metadata = self._extract_metadata()

    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata from PDF"""
        metadata = self.doc.metadata
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "num_pages": self.num_pages,
            "filename": self.pdf_path.name
        }

    def extract_page_text(self, page_num: int) -> str:
        """Extract text from a specific page (0-indexed)"""
        if page_num < 0 or page_num >= self.num_pages:
            raise ValueError(f"Page number {page_num} out of range (0-{self.num_pages-1})")

        page = self.doc[page_num]
        return page.get_text()

    def extract_all_text(self) -> Dict[int, str]:
        """Extract text from all pages"""
        text_by_page = {}
        for page_num in range(self.num_pages):
            text_by_page[page_num] = self.extract_page_text(page_num)
        return text_by_page

    def find_index_references(self, text: str = None) -> List[Dict[str, Any]]:
        """
        Find crane schematic index references (=XX/YY.Y.Z or =XX/YY.Z format)
        in the text
        """
        if text is None:
            text = " ".join(self.extract_all_text().values())

        # Pattern for full format: =XX/YY.Y.Z
        full_pattern = r'=(\d{2})/(\d{2})\.(\d)\.(\d)'
        # Pattern for shorthand: =XX/YY.Z (implies YY.0.Z)
        short_pattern = r'=(\d{2})/(\d{2})\.(\d)(?!\.)'

        references = []

        # Find full format references
        for match in re.finditer(full_pattern, text):
            references.append({
                "format": "full",
                "reference": match.group(0),
                "section": match.group(1),
                "sheet_major": match.group(2),
                "sheet_minor": match.group(3),
                "column": match.group(4),
                "position": match.start()
            })

        # Find shorthand format references
        for match in re.finditer(short_pattern, text):
            references.append({
                "format": "shorthand",
                "reference": match.group(0),
                "section": match.group(1),
                "sheet_major": match.group(2),
                "sheet_minor": "0",  # Implied
                "column": match.group(3),
                "position": match.start(),
                "expansion": f"={match.group(1)}/{match.group(2)}.0.{match.group(3)}"
            })

        # Sort by position
        references.sort(key=lambda x: x["position"])

        return references

    def render_page_image(self, page_num: int, zoom: float = 2.0) -> Image.Image:
        """Render a page as an image"""
        if page_num < 0 or page_num >= self.num_pages:
            raise ValueError(f"Page number {page_num} out of range (0-{self.num_pages-1})")

        page = self.doc[page_num]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        return img

    def save_page_image(self, page_num: int, output_path: str, zoom: float = 2.0):
        """Save a page as an image file"""
        img = self.render_page_image(page_num, zoom)
        img.save(output_path)

    def extract_page_region(self, page_num: int, rect: Tuple[float, float, float, float],
                           zoom: float = 2.0) -> Image.Image:
        """
        Extract a specific region from a page
        rect: (x0, y0, x1, y1) in page coordinates
        """
        if page_num < 0 or page_num >= self.num_pages:
            raise ValueError(f"Page number {page_num} out of range (0-{self.num_pages-1})")

        page = self.doc[page_num]
        mat = fitz.Matrix(zoom, zoom)

        # Create a clip rectangle
        clip_rect = fitz.Rect(rect)
        pix = page.get_pixmap(matrix=mat, clip=clip_rect)

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        return img

    def search_text(self, search_term: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for text across all pages
        Returns list of matches with page number and position
        """
        results = []

        for page_num in range(self.num_pages):
            page = self.doc[page_num]
            text_instances = page.search_for(search_term, quads=True)

            for inst in text_instances:
                results.append({
                    "page": page_num,
                    "text": search_term,
                    "bbox": inst.rect,  # Bounding box
                    "quad": inst  # Quadrilateral (for highlighting)
                })

        return results

    def find_components(self, text: str = None) -> List[Dict[str, Any]]:
        """
        Find component references in the schematic
        Looks for common patterns like component names followed by index references
        """
        if text is None:
            text = " ".join(self.extract_all_text().values())

        # Common component patterns in crane schematics
        patterns = [
            r'(HVC\d+)',  # High Voltage Contactors
            r'(Transformer)',
            r'(Slave\s*\d+)',
            r'(Cabinet\s*[A-Z]\d+)',
            r'(IM\d+)',  # Interface modules
            r'(PM\d*)',  # Power modules
            r'(DI\d*)',  # Digital input modules
            r'(RTD\d*)',  # RTD modules
        ]

        components = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                components.append({
                    "component": match.group(0),
                    "type": pattern.strip(r'()'),
                    "position": match.start()
                })

        return components

    def get_page_info(self, page_num: int) -> Dict[str, Any]:
        """Get detailed information about a page"""
        if page_num < 0 or page_num >= self.num_pages:
            raise ValueError(f"Page number {page_num} out of range (0-{self.num_pages-1})")

        page = self.doc[page_num]
        text = page.get_text()
        index_refs = self.find_index_references(text)
        components = self.find_components(text)

        return {
            "page_number": page_num,
            "width": page.rect.width,
            "height": page.rect.height,
            "rotation": page.rotation,
            "text_length": len(text),
            "index_references": index_refs,
            "components": components,
            "has_images": len(page.get_images()) > 0,
            "num_images": len(page.get_images())
        }

    def create_training_context(self, page_num: int) -> str:
        """
        Create a formatted training context from a page
        Includes text, index references, and components
        """
        info = self.get_page_info(page_num)
        text = self.extract_page_text(page_num)

        context = f"# Page {page_num + 1} of {self.num_pages}\n\n"
        context += f"## Page Information\n"
        context += f"- Dimensions: {info['width']:.1f} x {info['height']:.1f}\n"
        context += f"- Text length: {info['text_length']} characters\n"
        context += f"- Images: {info['num_images']}\n\n"

        if info['index_references']:
            context += f"## Index References Found ({len(info['index_references'])})\n"
            for ref in info['index_references'][:10]:  # Limit to first 10
                if ref['format'] == 'shorthand':
                    context += f"- {ref['reference']} (expands to {ref['expansion']})\n"
                else:
                    context += f"- {ref['reference']}\n"
            context += "\n"

        if info['components']:
            context += f"## Components Found ({len(info['components'])})\n"
            for comp in info['components'][:10]:  # Limit to first 10
                context += f"- {comp['component']}\n"
            context += "\n"

        context += "## Full Page Text\n"
        context += text[:1000] + "..." if len(text) > 1000 else text

        return context

    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_processor.py <pdf_file>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        with SchematicPDFProcessor(pdf_path) as processor:
            print(f"Processing: {processor.pdf_path.name}")
            print(f"Pages: {processor.num_pages}")
            print("\nMetadata:")
            for key, value in processor.metadata.items():
                print(f"  {key}: {value}")

            # Show info for first page
            if processor.num_pages > 0:
                print("\n" + "="*60)
                print(processor.create_training_context(0))

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
