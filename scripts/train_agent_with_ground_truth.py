#!/usr/bin/env python3
"""
Agent Training with Ground Truth Labeling
YOU label schematics completely, then Claude learns from your labels
"""

import sys
import json
import base64
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from schematic_analyzer import SchematicAnalyzer
from ground_truth_labeler import GroundTruthLabeler
from training_data_builder import TrainingDataBuilder
from pdf_processor import SchematicPDFProcessor
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from dotenv import load_dotenv


class GroundTruthTrainer:
    """Train Claude using ground truth labels"""

    def __init__(self):
        load_dotenv()
        self.console = Console()
        self.analyzer = SchematicAnalyzer()
        self.labeler = GroundTruthLabeler()
        self.training_builder = TrainingDataBuilder()

    def show_banner(self):
        """Display welcome banner"""
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   Ground Truth Training Mode                                 ║
║                                                              ║
║   YOU Label → Claude Learns                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[yellow]How Ground Truth Training Works:[/yellow]

[bold]Step 1: YOU Label the Schematic[/bold]
- View the schematic
- Label ALL components, index refs, connections
- Create complete ground truth

[bold]Step 2: Claude Analyzes Same Schematic[/bold]
- Claude uses Vision AI
- Identifies what it can find

[bold]Step 3: Compare & Learn[/bold]
- Compare Claude's analysis vs YOUR labels
- See precision, recall, F1 scores
- Identify what Claude missed or got wrong

[bold]Step 4: Build Training Data[/bold]
- YOUR labels become training examples
- High-quality dataset for fine-tuning
- Claude learns from your expertise

[green]Benefits of Ground Truth:[/green]
✓ Comprehensive labeling (nothing missed)
✓ Higher quality training data
✓ Clear performance metrics
✓ YOU are the expert, Claude learns from you
"""
        self.console.print(banner)

    def train_with_ground_truth(self, pdf_path: str, page_num: int = 0):
        """
        Train using ground truth labeling workflow

        Workflow:
        1. User provides ground truth labels
        2. Claude analyzes same schematic
        3. Compare results
        4. Build training data from ground truth
        """
        self.console.print(f"\n[bold]Training with Ground Truth[/bold]")
        self.console.print(f"PDF: {pdf_path}")
        self.console.print(f"Page: {page_num + 1}\n")

        with SchematicPDFProcessor(pdf_path) as processor:
            if page_num >= processor.num_pages:
                self.console.print(f"[red]Page {page_num} out of range[/red]")
                return

            # Save page image for reference
            img_path = f"/tmp/schematic_page_{page_num}.png"
            processor.save_page_image(page_num, img_path, zoom=2.0)

            # Get base64 for training data
            img = processor.render_page_image(page_num, zoom=2.0)
            import io
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')

        # STEP 1: Get ground truth from user
        self.console.print("="*80)
        self.console.print("[bold green]STEP 1: Provide Ground Truth Labels[/bold green]")
        self.console.print(f"[dim]Image saved to: {img_path}[/dim]")
        self.console.print("[dim]Open this image to reference while labeling[/dim]\n")

        ground_truth = self.labeler.label_schematic(pdf_path, page_num, img_path)

        if not ground_truth:
            self.console.print("[yellow]Training cancelled[/yellow]")
            return

        # Save ground truth
        gt_file = self.labeler.save_ground_truth(ground_truth)

        # STEP 2: Have Claude analyze
        self.console.print("\n" + "="*80)
        self.console.print("[bold yellow]STEP 2: Claude Analyzing Same Schematic[/bold yellow]")
        self.console.print("[dim]Claude will now analyze the same schematic...[/dim]\n")

        claude_analysis = self.analyzer.analyze_schematic_page(pdf_path, page_num)

        # STEP 3: Compare
        self.console.print("\n" + "="*80)
        self.console.print("[bold cyan]STEP 3: Comparing Claude vs Ground Truth[/bold cyan]\n")

        comparison = self.labeler.compare_with_analysis(
            ground_truth,
            claude_analysis['parsed_analysis']
        )

        self.labeler.show_comparison(comparison)

        # STEP 4: Build training data
        self.console.print("\n" + "="*80)
        self.console.print("[bold green]STEP 4: Building Training Data[/bold green]\n")

        # Create training example using ground truth
        training_example = {
            "timestamp": datetime.now().isoformat(),
            "original_analysis": {
                "pdf_path": pdf_path,
                "page_num": page_num,
                "raw_response": claude_analysis['raw_response']
            },
            "corrections": self._build_corrections_from_comparison(comparison),
            "ground_truth": {
                "components": ground_truth.get("components", []),
                "index_references": ground_truth.get("index_references", []),
                "wire_connections": ground_truth.get("wire_connections", [])
            },
            "feedback": f"Ground truth labeling. Claude performance: P={comparison['overall_precision']:.1%}, R={comparison['overall_recall']:.1%}, F1={comparison['overall_f1']:.1%}"
        }

        self.training_builder.add_correction(training_example, img_base64)

        self.console.print("[green]✓ Training data saved![/green]")
        self.console.print(f"\nGround Truth: {gt_file}")

        # Show what Claude needs to improve on
        if comparison["misses"]:
            self.console.print(f"\n[yellow]Claude needs to learn to find:[/yellow]")
            for miss in comparison["misses"][:5]:
                self.console.print(f"  • {miss['category']}: {miss['item']}")

        if comparison["false_positives"]:
            self.console.print(f"\n[yellow]Claude incorrectly identified:[/yellow]")
            for fp in comparison["false_positives"][:5]:
                self.console.print(f"  • {fp['category']}: {fp['item']}")

    def _build_corrections_from_comparison(self, comparison: Dict) -> Dict:
        """Build corrections structure from comparison"""
        corrections = {}

        for category, metrics in comparison["by_category"].items():
            corrections[category] = {
                "correct": metrics["correct"],
                "removed": [fp["item"] for fp in comparison["false_positives"]
                           if fp["category"] == category],
                "added": [miss["item"] for miss in comparison["misses"]
                         if miss["category"] == category],
                "modified": []
            }

        return corrections

    def train_on_section(self, section: str):
        """Train on all PDFs in a section using ground truth"""
        # Load catalog
        catalog_file = Path("data/pdfs/catalog.json")

        if not catalog_file.exists():
            self.console.print("[red]No PDF catalog found[/red]")
            return

        with open(catalog_file, 'r') as f:
            catalog = json.load(f)

        section_key = f"section_{section}"
        pdfs = catalog.get(section_key, [])

        if not pdfs:
            self.console.print(f"[red]No PDFs found for section {section}[/red]")
            return

        self.console.print(f"\n[bold cyan]Ground Truth Training on Section {section}[/bold cyan]")
        self.console.print(f"Found {len(pdfs)} PDFs\n")

        for i, pdf_info in enumerate(pdfs, 1):
            self.console.print(f"\n{'='*80}")
            self.console.print(f"[bold]PDF {i}/{len(pdfs)}: {pdf_info['filename']}[/bold]")
            self.console.print(f"{'='*80}\n")

            pdf_path = pdf_info['path']

            # Train on each page
            with SchematicPDFProcessor(pdf_path) as processor:
                num_pages = processor.num_pages

                for page_num in range(num_pages):
                    self.console.print(f"\n[bold]Page {page_num + 1}/{num_pages}[/bold]")

                    self.train_with_ground_truth(pdf_path, page_num)

                    if page_num < num_pages - 1:
                        if not Confirm.ask("\nContinue to next page?", default=True):
                            break

            if i < len(pdfs):
                if not Confirm.ask("\nContinue to next PDF?", default=True):
                    break

    def show_training_stats(self):
        """Show training statistics"""
        stats = self.training_builder.get_training_stats()

        self.console.print(Panel(
            f"[bold cyan]Training Statistics[/bold cyan]\n\n"
            f"Total Training Examples: {stats['total_examples']}\n"
            f"Validated Examples: {stats['validated_examples']}\n"
            f"Common Mistakes Tracked: {stats['total_mistakes']}\n"
            f"Last Updated: {stats['last_updated']}\n",
            border_style="cyan"
        ))


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Train Claude using ground truth labels")
    parser.add_argument("--pdf", help="PDF file to train on")
    parser.add_argument("--section", help="Section number (e.g., 61)")
    parser.add_argument("--page", type=int, default=0, help="Page number (default: 0)")
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    args = parser.parse_args()

    trainer = GroundTruthTrainer()
    trainer.show_banner()

    if args.stats:
        trainer.show_training_stats()
        return

    if args.pdf:
        trainer.train_with_ground_truth(args.pdf, args.page)
        trainer.show_training_stats()

    elif args.section:
        trainer.train_on_section(args.section)
        trainer.show_training_stats()

    else:
        # Interactive mode
        trainer.console.print("\n[bold yellow]Interactive Mode[/bold yellow]\n")

        choice = Prompt.ask(
            "What would you like to do?",
            choices=["train_pdf", "train_section", "stats", "quit"],
            default="train_pdf"
        )

        if choice == "train_pdf":
            pdf_path = Prompt.ask("Enter PDF path")
            page = int(Prompt.ask("Enter page number", default="0"))
            trainer.train_with_ground_truth(pdf_path, page)

        elif choice == "train_section":
            section = Prompt.ask("Enter section number (e.g., 61)")
            trainer.train_on_section(section)

        elif choice == "stats":
            trainer.show_training_stats()

    trainer.console.print("\n[bold green]✓ Ground truth training complete![/bold green]\n")


if __name__ == "__main__":
    main()
