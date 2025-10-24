#!/usr/bin/env python3
"""
Agent Training Script
Trains Claude to read crane schematics using corrections and feedback
"""

import sys
import json
import base64
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from schematic_analyzer import SchematicAnalyzer
from correction_interface import CorrectionInterface
from training_data_builder import TrainingDataBuilder
from pdf_processor import SchematicPDFProcessor
from ground_truth_labeler import GroundTruthLabeler
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import track
from dotenv import load_dotenv


class AgentTrainer:
    """Main trainer for teaching Claude to read schematics"""

    def __init__(self):
        load_dotenv()
        self.console = Console()
        self.analyzer = SchematicAnalyzer()
        self.correction_interface = CorrectionInterface()
        self.training_builder = TrainingDataBuilder()
        self.ground_truth_labeler = GroundTruthLabeler()

    def show_banner(self):
        """Display welcome banner"""
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   TRACE Agent Training System                                ║
║                                                              ║
║   Teaching Claude to Read Crane Schematics                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[yellow]Two Training Modes:[/yellow]

[bold]Mode 1: Ground Truth Labeling[/bold] (Recommended)
1. YOU label everything in the schematic first (ground truth)
2. Claude analyzes the same schematic
3. System compares Claude vs your labels
4. Shows precision/recall metrics
5. Uses YOUR labels as training data

[bold]Mode 2: Correction-Based[/bold]
1. Claude analyzes your schematic first
2. You correct Claude's mistakes
3. System learns from corrections

[green]Both modes create:[/green]
✓ High-quality training dataset
✓ Fine-tuning examples
✓ Knowledge base for your schematics
"""
        self.console.print(banner)

    def train_on_pdf(self, pdf_path: str, pages: list = None):
        """
        Train Claude on a PDF schematic

        Args:
            pdf_path: Path to PDF file
            pages: List of page numbers to train on (0-indexed), None for all pages
        """
        self.console.print(f"\n[bold]Training on:[/bold] {pdf_path}\n")

        with SchematicPDFProcessor(pdf_path) as processor:
            num_pages = processor.num_pages

            if pages is None:
                pages = list(range(num_pages))

            self.console.print(f"Pages to analyze: {len(pages)}")

            for page_num in pages:
                if page_num >= num_pages:
                    self.console.print(f"[yellow]Skipping page {page_num} (out of range)[/yellow]")
                    continue

                self.console.print("\n" + "="*80)
                self.console.print(f"[bold cyan]Analyzing Page {page_num + 1}/{num_pages}[/bold cyan]")
                self.console.print("="*80)

                # Get page image for training data
                img = processor.render_page_image(page_num, zoom=2.0)
                import io
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')

                # Analyze with Claude Vision
                self.console.print("\n[yellow]⏳ Claude is analyzing the schematic...[/yellow]\n")

                analysis = self.analyzer.analyze_schematic_page(pdf_path, page_num)

                # Collect corrections
                correction = self.correction_interface.collect_corrections(analysis)

                # Show summary
                self.correction_interface.show_correction_summary(correction)

                # Add to training data
                self.training_builder.add_correction(correction, img_base64)

                self.console.print("\n[green]✓ Training data saved![/green]")

                # Ask if user wants to continue
                if page_num < pages[-1]:
                    if not Confirm.ask("\nContinue to next page?", default=True):
                        break

    def train_on_section(self, section: str):
        """Train on all PDFs in a section"""
        # Load catalog
        catalog_file = Path("data/pdfs/catalog.json")

        if not catalog_file.exists():
            self.console.print("[red]No PDF catalog found. Run 'python3 scripts/catalog_pdfs.py --scan' first[/red]")
            return

        with open(catalog_file, 'r') as f:
            catalog = json.load(f)

        section_key = f"section_{section}"
        pdfs = catalog.get(section_key, [])

        if not pdfs:
            self.console.print(f"[red]No PDFs found for section {section}[/red]")
            return

        self.console.print(f"\n[bold cyan]Training on Section {section}[/bold cyan]")
        self.console.print(f"Found {len(pdfs)} PDFs\n")

        for i, pdf_info in enumerate(pdfs, 1):
            self.console.print(f"\n{'='*80}")
            self.console.print(f"[bold]PDF {i}/{len(pdfs)}: {pdf_info['filename']}[/bold]")
            self.console.print(f"{'='*80}\n")

            pdf_path = pdf_info['path']

            # Train on this PDF
            self.train_on_pdf(pdf_path)

            # Ask if user wants to continue
            if i < len(pdfs):
                if not Confirm.ask("\nContinue to next PDF?", default=True):
                    break

    def show_training_stats(self):
        """Show statistics about training progress"""
        stats = self.training_builder.get_training_stats()

        self.console.print(Panel(
            f"[bold cyan]Training Statistics[/bold cyan]\n\n"
            f"Total Training Examples: {stats['total_examples']}\n"
            f"Validated Examples: {stats['validated_examples']}\n"
            f"Common Mistakes Tracked: {stats['total_mistakes']}\n"
            f"Last Updated: {stats['last_updated']}\n",
            border_style="cyan"
        ))

        # Show common mistakes
        mistakes = self.training_builder.get_common_mistakes(limit=5)
        if mistakes:
            self.console.print("\n[bold]Common Mistakes:[/bold]")
            for mistake in mistakes:
                if "correction" in mistake:
                    self.console.print(f"  • {mistake['category']}: '{mistake['mistake']}' → '{mistake['correction']}'")
                else:
                    self.console.print(f"  • {mistake['category']}: {mistake['mistake']}")

    def export_training_data(self):
        """Export training data for fine-tuning"""
        self.console.print("\n[bold]Exporting Training Data[/bold]\n")

        output_path = self.training_builder.export_for_finetuning()

        if output_path:
            self.console.print(f"[green]✓ Fine-tuning dataset exported to:[/green]")
            self.console.print(f"  {output_path}")
            self.console.print("\n[cyan]This file can be submitted to Anthropic for fine-tuning[/cyan]")
        else:
            self.console.print("[yellow]No training data to export yet[/yellow]")

        # Show improved prompt
        self.console.print("\n[bold]Improved Analysis Prompt:[/bold]")
        prompt = self.training_builder.generate_improved_prompt()
        self.console.print(Panel(prompt, border_style="green"))


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Train Claude to read crane schematics")
    parser.add_argument("--pdf", help="PDF file to train on")
    parser.add_argument("--section", help="Section number to train on (e.g., 61)")
    parser.add_argument("--pages", help="Comma-separated page numbers (e.g., 0,1,2)")
    parser.add_argument("--stats", action="store_true", help="Show training statistics")
    parser.add_argument("--export", action="store_true", help="Export training data")

    args = parser.parse_args()

    trainer = AgentTrainer()
    trainer.show_banner()

    if args.stats:
        trainer.show_training_stats()
        return

    if args.export:
        trainer.export_training_data()
        return

    if args.pdf:
        pages = None
        if args.pages:
            pages = [int(p.strip()) for p in args.pages.split(",")]

        trainer.train_on_pdf(args.pdf, pages)
        trainer.show_training_stats()

    elif args.section:
        trainer.train_on_section(args.section)
        trainer.show_training_stats()

    else:
        # Interactive mode
        trainer.console.print("\n[bold yellow]Interactive Mode[/bold yellow]\n")

        choice = Prompt.ask(
            "What would you like to do?",
            choices=["train_pdf", "train_section", "stats", "export", "quit"],
            default="train_section"
        )

        if choice == "train_pdf":
            pdf_path = Prompt.ask("Enter PDF path")
            trainer.train_on_pdf(pdf_path)

        elif choice == "train_section":
            section = Prompt.ask("Enter section number (e.g., 61)")
            trainer.train_on_section(section)

        elif choice == "stats":
            trainer.show_training_stats()

        elif choice == "export":
            trainer.export_training_data()

    trainer.console.print("\n[bold green]✓ Training session complete![/bold green]\n")


if __name__ == "__main__":
    main()
