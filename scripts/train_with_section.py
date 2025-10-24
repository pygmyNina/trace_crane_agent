#!/usr/bin/env python3
"""
Train with Section PDFs
Helper script to easily train with specific sections
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from training_interface import TrainingInterface
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table


class SectionTrainer:
    """Helper for training with section PDFs"""

    def __init__(self):
        self.console = Console()
        self.pdfs_dir = Path("data/pdfs")
        self.catalog_file = self.pdfs_dir / "catalog.json"
        self.catalog = self._load_catalog()

    def _load_catalog(self):
        """Load PDF catalog"""
        if self.catalog_file.exists():
            with open(self.catalog_file, 'r') as f:
                return json.load(f)
        return {}

    def list_sections(self):
        """List available sections"""
        if not self.catalog:
            self.console.print("[yellow]No PDFs cataloged. Run 'python scripts/catalog_pdfs.py --scan' first[/yellow]")
            return []

        sections = []
        table = Table(title="Available Sections")
        table.add_column("Section", style="cyan")
        table.add_column("PDFs", justify="right")
        table.add_column("Total Pages", justify="right")

        for section_key, pdfs in self.catalog.items():
            if pdfs:
                section_num = section_key.replace("section_", "")
                total_pages = sum(pdf['pages'] for pdf in pdfs)
                sections.append(section_num)

                table.add_row(
                    section_num,
                    str(len(pdfs)),
                    str(total_pages)
                )

        self.console.print(table)
        return sections

    def list_section_pdfs(self, section: str):
        """List PDFs in a section"""
        section_key = f"section_{section}"
        pdfs = self.catalog.get(section_key, [])

        if not pdfs:
            self.console.print(f"[yellow]No PDFs found for section {section}[/yellow]")
            return []

        table = Table(title=f"Section {section} PDFs")
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Filename")
        table.add_column("Pages", justify="right")
        table.add_column("Index Refs", justify="right")
        table.add_column("Components", justify="right")

        for i, pdf in enumerate(pdfs, 1):
            table.add_row(
                str(i),
                pdf['filename'],
                str(pdf['pages']),
                str(len(pdf['index_references'])),
                str(len(pdf['components']))
            )

        self.console.print(table)
        return pdfs

    def train_with_section(self, section: str, sheet_numbers: list = None):
        """Start training with section PDFs"""
        section_key = f"section_{section}"
        pdfs = self.catalog.get(section_key, [])

        if not pdfs:
            self.console.print(f"[red]Section {section} not found or has no PDFs[/red]")
            return

        # Filter by sheet numbers if specified
        if sheet_numbers:
            filtered_pdfs = []
            for pdf in pdfs:
                # Try to extract sheet number from filename
                for sheet_num in sheet_numbers:
                    if f"{section}.{sheet_num}" in pdf['filename'] or f"{section}_{sheet_num}" in pdf['filename']:
                        filtered_pdfs.append(pdf)
                        break
            pdfs = filtered_pdfs

        if not pdfs:
            self.console.print(f"[red]No PDFs found matching the criteria[/red]")
            return

        # Show what will be loaded
        self.console.print(f"\n[bold cyan]Training with {len(pdfs)} PDF(s) from Section {section}[/bold cyan]\n")
        for i, pdf in enumerate(pdfs, 1):
            self.console.print(f"{i}. {pdf['filename']} ({pdf['pages']} pages)")

        if not Confirm.ask("\nProceed with training?", default=True):
            return

        # Train with each PDF
        for pdf in pdfs:
            pdf_path = pdf['path']

            self.console.print(f"\n[bold green]Loading: {pdf['filename']}[/bold green]")

            # Show PDF details
            if pdf['index_references']:
                self.console.print(f"Index references found: {', '.join(pdf['index_references'][:5])}")
            if pdf['components']:
                self.console.print(f"Components found: {', '.join(pdf['components'][:5])}")

            # Start training session with this PDF
            try:
                trainer = TrainingInterface()
                trainer.start_session(pdf_path)
                trainer.interactive_training()
                trainer.end_session()
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Training interrupted[/yellow]")
                if not Confirm.ask("Continue with next PDF?", default=False):
                    break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                if not Confirm.ask("Continue with next PDF?", default=True):
                    break

    def train_with_pdf(self, pdf_path: str):
        """Train with a specific PDF"""
        if not Path(pdf_path).exists():
            self.console.print(f"[red]PDF not found: {pdf_path}[/red]")
            return

        try:
            trainer = TrainingInterface()
            trainer.start_session(pdf_path)
            trainer.interactive_training()
            trainer.end_session()
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Train with section PDFs")
    parser.add_argument("--section", help="Section number (e.g., 61, 10)")
    parser.add_argument("--sheets", help="Comma-separated sheet numbers (e.g., 1,2,3)")
    parser.add_argument("--list", action="store_true", help="List available sections")
    parser.add_argument("--pdf", help="Train with specific PDF file")

    args = parser.parse_args()

    trainer = SectionTrainer()

    if args.list:
        trainer.list_sections()
        return

    if args.pdf:
        trainer.train_with_pdf(args.pdf)
        return

    if args.section:
        sheet_numbers = None
        if args.sheets:
            sheet_numbers = [s.strip() for s in args.sheets.split(",")]

        # Show PDFs in section first
        trainer.list_section_pdfs(args.section)

        # Start training
        trainer.train_with_section(args.section, sheet_numbers)
    else:
        # Interactive mode
        sections = trainer.list_sections()

        if sections:
            section = Prompt.ask("\nSelect section number", choices=sections)
            trainer.list_section_pdfs(section)

            if Confirm.ask("\nStart training with this section?", default=True):
                trainer.train_with_section(section)


if __name__ == "__main__":
    main()
