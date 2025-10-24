#!/usr/bin/env python3
"""
PDF Cataloging Script
Scans PDF directories and creates a catalog with metadata
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf_processor import SchematicPDFProcessor
from rich.console import Console
from rich.progress import track
from rich.table import Table


class PDFCatalog:
    """Manages the PDF catalog"""

    def __init__(self, pdfs_dir: str = "data/pdfs"):
        self.pdfs_dir = Path(pdfs_dir)
        self.catalog_file = self.pdfs_dir / "catalog.json"
        self.console = Console()
        self.catalog = self._load_catalog()

    def _load_catalog(self):
        """Load existing catalog or create new one"""
        if self.catalog_file.exists():
            with open(self.catalog_file, 'r') as f:
                return json.load(f)
        return {}

    def save_catalog(self):
        """Save catalog to disk"""
        with open(self.catalog_file, 'w') as f:
            json.dump(self.catalog, f, indent=2)

    def scan_directory(self, section_dir: Path):
        """Scan a section directory for PDFs"""
        section_name = section_dir.name
        pdfs = list(section_dir.glob("*.pdf"))

        if not pdfs:
            self.console.print(f"[yellow]No PDFs found in {section_name}[/yellow]")
            return

        self.console.print(f"\n[bold cyan]Scanning {section_name}[/bold cyan] ({len(pdfs)} PDFs)")

        section_catalog = []

        for pdf_path in track(pdfs, description=f"Processing {section_name}"):
            try:
                entry = self._process_pdf(pdf_path)
                section_catalog.append(entry)
            except Exception as e:
                self.console.print(f"[red]Error processing {pdf_path.name}: {e}[/red]")

        self.catalog[section_name] = section_catalog

    def _process_pdf(self, pdf_path: Path):
        """Process a single PDF and extract metadata"""
        with SchematicPDFProcessor(str(pdf_path)) as processor:
            # Extract metadata
            metadata = processor.metadata

            # Get info from first page
            info = processor.get_page_info(0) if processor.num_pages > 0 else {}

            # Extract index references
            text = processor.extract_all_text()
            all_text = " ".join(text.values())
            refs = processor.find_index_references(all_text)
            components = processor.find_components(all_text)

            return {
                "filename": pdf_path.name,
                "path": str(pdf_path.relative_to(Path.cwd())),
                "pages": processor.num_pages,
                "size_bytes": pdf_path.stat().st_size,
                "added_date": datetime.now().isoformat(),
                "index_references": [ref["reference"] for ref in refs[:10]],  # Limit to 10
                "components": list(set([comp["component"] for comp in components[:10]])),  # Unique, limit 10
                "title": metadata.get("title", ""),
                "description": ""  # User can add this manually
            }

    def scan_all(self):
        """Scan all section directories"""
        section_dirs = [d for d in self.pdfs_dir.iterdir() if d.is_dir() and d.name != "__pycache__"]

        if not section_dirs:
            self.console.print("[yellow]No section directories found[/yellow]")
            return

        for section_dir in section_dirs:
            self.scan_directory(section_dir)

        self.save_catalog()
        self.console.print(f"\n[bold green]✓ Catalog saved to {self.catalog_file}[/bold green]")

    def display_catalog(self):
        """Display catalog as a table"""
        if not self.catalog:
            self.console.print("[yellow]Catalog is empty[/yellow]")
            return

        for section, pdfs in self.catalog.items():
            table = Table(title=f"{section} ({len(pdfs)} PDFs)")
            table.add_column("Filename", style="cyan")
            table.add_column("Pages", justify="right")
            table.add_column("Size", justify="right")
            table.add_column("Index Refs", justify="right")
            table.add_column("Components", justify="right")

            for pdf in pdfs:
                size_kb = pdf['size_bytes'] / 1024
                table.add_row(
                    pdf['filename'],
                    str(pdf['pages']),
                    f"{size_kb:.1f} KB",
                    str(len(pdf['index_references'])),
                    str(len(pdf['components']))
                )

            self.console.print(table)
            self.console.print()

    def get_section_pdfs(self, section: str):
        """Get all PDFs for a section"""
        section_key = f"section_{section}"
        return self.catalog.get(section_key, [])


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Catalog PDF schematics")
    parser.add_argument("--scan", action="store_true", help="Scan all PDFs")
    parser.add_argument("--show", action="store_true", help="Display catalog")
    parser.add_argument("--section", help="Scan specific section only")

    args = parser.parse_args()

    catalog = PDFCatalog()

    if args.scan:
        if args.section:
            section_dir = catalog.pdfs_dir / f"section_{args.section}"
            if section_dir.exists():
                catalog.scan_directory(section_dir)
                catalog.save_catalog()
            else:
                catalog.console.print(f"[red]Section directory not found: {section_dir}[/red]")
        else:
            catalog.scan_all()

    if args.show or (not args.scan):
        catalog.display_catalog()


if __name__ == "__main__":
    main()
