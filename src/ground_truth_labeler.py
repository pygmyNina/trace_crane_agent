"""
Ground Truth Labeling Interface
Allows user to provide complete ground truth labels for schematics
"""

from typing import Dict, List, Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
import json
from datetime import datetime
from pathlib import Path


class GroundTruthLabeler:
    """Interface for creating complete ground truth labels"""

    def __init__(self):
        self.console = Console()

    def label_schematic(self, pdf_path: str, page_num: int,
                       show_image_path: str = None) -> Dict[str, Any]:
        """
        Create complete ground truth labels for a schematic

        Args:
            pdf_path: Path to PDF file
            page_num: Page number
            show_image_path: Optional path to image to display

        Returns:
            Complete ground truth labels
        """
        self.console.print("\n" + "="*80)
        self.console.print(Panel(
            f"[bold cyan]Ground Truth Labeling[/bold cyan]\n\n"
            f"PDF: {pdf_path}\n"
            f"Page: {page_num + 1}\n\n"
            f"You will provide complete labels for this schematic.\n"
            f"Label EVERYTHING you see - we'll use this as ground truth.",
            border_style="cyan"
        ))

        if show_image_path:
            self.console.print(f"\n[yellow]Image available at: {show_image_path}[/yellow]")
            self.console.print("[dim]Open this image in another window for reference[/dim]\n")

        ground_truth = {
            "pdf_path": pdf_path,
            "page_num": page_num,
            "timestamp": datetime.now().isoformat(),
            "components": [],
            "index_references": [],
            "wire_connections": [],
            "labels": [],
            "notes": ""
        }

        # Label each category
        self.console.print("\n[bold yellow]Let's label everything in this schematic[/bold yellow]\n")

        # Components
        if Confirm.ask("Label COMPONENTS (HVC, Slaves, Cabinets, Modules)?", default=True):
            ground_truth["components"] = self._label_category(
                "Components",
                "Examples: HVC3, Slave 22, Cabinet E11, IM151, etc."
            )

        # Index References
        if Confirm.ask("\nLabel INDEX REFERENCES (=XX/YY.Y.Z)?", default=True):
            ground_truth["index_references"] = self._label_category(
                "Index References",
                "Examples: =61/102.0.8, =10/103.0.7, etc."
            )

        # Wire Connections
        if Confirm.ask("\nLabel WIRE CONNECTIONS?", default=True):
            ground_truth["wire_connections"] = self._label_category(
                "Wire Connections",
                "Examples: W1 connects to W2 at terminal 5"
            )

        # Other Labels
        if Confirm.ask("\nLabel OTHER TEXT/LABELS (terminals, specs, notes)?", default=False):
            ground_truth["labels"] = self._label_category(
                "Other Labels",
                "Examples: Terminal 5, 24VDC, etc."
            )

        # Overall notes
        notes = Prompt.ask(
            "\nAny notes about this schematic?",
            default=""
        )
        ground_truth["notes"] = notes

        # Show summary
        self._show_ground_truth_summary(ground_truth)

        # Confirm
        if not Confirm.ask("\nSave these ground truth labels?", default=True):
            self.console.print("[yellow]Labels discarded[/yellow]")
            return None

        return ground_truth

    def _label_category(self, category_name: str, help_text: str) -> List[str]:
        """
        Label a specific category

        Args:
            category_name: Name of category
            help_text: Help text with examples

        Returns:
            List of labels
        """
        self.console.print(f"\n[bold cyan]Labeling: {category_name}[/bold cyan]")
        self.console.print(f"[dim]{help_text}[/dim]")
        self.console.print("\n[yellow]Enter items one per line. Press Enter on empty line when done.[/yellow]\n")

        labels = []
        item_num = 1

        while True:
            item = Prompt.ask(f"  [{item_num}]", default="")

            if not item:
                break

            labels.append(item)
            self.console.print(f"    [green]✓ Added: {item}[/green]")
            item_num += 1

        self.console.print(f"\n[bold]{len(labels)} {category_name} labeled[/bold]")

        return labels

    def _show_ground_truth_summary(self, ground_truth: Dict[str, Any]):
        """Display summary of ground truth labels"""
        self.console.print("\n" + "="*80)
        self.console.print(Panel(
            "[bold green]Ground Truth Summary[/bold green]",
            border_style="green"
        ))

        total_labels = (
            len(ground_truth.get("components", [])) +
            len(ground_truth.get("index_references", [])) +
            len(ground_truth.get("wire_connections", [])) +
            len(ground_truth.get("labels", []))
        )

        self.console.print(f"\n[bold]Total Items Labeled: {total_labels}[/bold]\n")

        # Show each category
        for category in ["components", "index_references", "wire_connections", "labels"]:
            items = ground_truth.get(category, [])
            if items:
                self.console.print(f"[bold cyan]{category.upper().replace('_', ' ')}:[/bold cyan] ({len(items)})")
                for item in items:
                    self.console.print(f"  • {item}")
                self.console.print()

        if ground_truth.get("notes"):
            self.console.print(f"[bold]Notes:[/bold] {ground_truth['notes']}\n")

    def save_ground_truth(self, ground_truth: Dict[str, Any], output_dir: str = "data/ground_truth"):
        """Save ground truth labels to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create filename from PDF and page
        pdf_name = Path(ground_truth['pdf_path']).stem
        page_num = ground_truth['page_num']
        filename = f"{pdf_name}_page{page_num}_gt.json"

        filepath = output_path / filename

        with open(filepath, 'w') as f:
            json.dump(ground_truth, f, indent=2)

        self.console.print(f"[green]✓ Ground truth saved to: {filepath}[/green]")

        return str(filepath)

    def load_ground_truth(self, filepath: str) -> Dict[str, Any]:
        """Load ground truth from file"""
        with open(filepath, 'r') as f:
            return json.load(f)

    def compare_with_analysis(self, ground_truth: Dict[str, Any],
                             analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare Claude's analysis with ground truth

        Returns metrics: precision, recall, F1, etc.
        """
        comparison = {
            "ground_truth_total": 0,
            "analysis_total": 0,
            "matches": 0,
            "misses": [],
            "false_positives": [],
            "by_category": {}
        }

        for category in ["components", "index_references", "wire_connections"]:
            gt_items = set(ground_truth.get(category, []))
            analysis_items = set(analysis.get(category, []))

            matches = gt_items & analysis_items
            misses = gt_items - analysis_items  # In ground truth but not found
            false_pos = analysis_items - gt_items  # Found but not in ground truth

            comparison["ground_truth_total"] += len(gt_items)
            comparison["analysis_total"] += len(analysis_items)
            comparison["matches"] += len(matches)

            comparison["by_category"][category] = {
                "ground_truth": len(gt_items),
                "found": len(analysis_items),
                "correct": len(matches),
                "missed": len(misses),
                "false_positives": len(false_pos),
                "precision": len(matches) / len(analysis_items) if analysis_items else 0,
                "recall": len(matches) / len(gt_items) if gt_items else 0
            }

            # Calculate F1
            prec = comparison["by_category"][category]["precision"]
            rec = comparison["by_category"][category]["recall"]
            if prec + rec > 0:
                comparison["by_category"][category]["f1"] = 2 * (prec * rec) / (prec + rec)
            else:
                comparison["by_category"][category]["f1"] = 0

            comparison["misses"].extend([
                {"category": category, "item": item} for item in misses
            ])
            comparison["false_positives"].extend([
                {"category": category, "item": item} for item in false_pos
            ])

        # Overall metrics
        gt_total = comparison["ground_truth_total"]
        analysis_total = comparison["analysis_total"]
        matches = comparison["matches"]

        if analysis_total > 0:
            comparison["overall_precision"] = matches / analysis_total
        else:
            comparison["overall_precision"] = 0

        if gt_total > 0:
            comparison["overall_recall"] = matches / gt_total
        else:
            comparison["overall_recall"] = 0

        prec = comparison["overall_precision"]
        rec = comparison["overall_recall"]
        if prec + rec > 0:
            comparison["overall_f1"] = 2 * (prec * rec) / (prec + rec)
        else:
            comparison["overall_f1"] = 0

        return comparison

    def show_comparison(self, comparison: Dict[str, Any]):
        """Display comparison metrics"""
        self.console.print("\n" + "="*80)
        self.console.print(Panel(
            "[bold cyan]Analysis vs Ground Truth Comparison[/bold cyan]",
            border_style="cyan"
        ))

        # Overall metrics
        self.console.print(f"\n[bold]Overall Performance:[/bold]")
        self.console.print(f"  Precision: {comparison['overall_precision']:.1%}")
        self.console.print(f"  Recall: {comparison['overall_recall']:.1%}")
        self.console.print(f"  F1 Score: {comparison['overall_f1']:.1%}")

        # By category
        self.console.print(f"\n[bold]By Category:[/bold]\n")

        table = Table()
        table.add_column("Category", style="cyan")
        table.add_column("Ground Truth", justify="right")
        table.add_column("Found", justify="right")
        table.add_column("Correct", justify="right", style="green")
        table.add_column("Missed", justify="right", style="yellow")
        table.add_column("False+", justify="right", style="red")
        table.add_column("Precision", justify="right")
        table.add_column("Recall", justify="right")
        table.add_column("F1", justify="right")

        for category, metrics in comparison["by_category"].items():
            table.add_row(
                category.replace("_", " ").title(),
                str(metrics["ground_truth"]),
                str(metrics["found"]),
                str(metrics["correct"]),
                str(metrics["missed"]),
                str(metrics["false_positives"]),
                f"{metrics['precision']:.1%}",
                f"{metrics['recall']:.1%}",
                f"{metrics['f1']:.1%}"
            )

        self.console.print(table)

        # Show misses
        if comparison["misses"]:
            self.console.print(f"\n[bold yellow]Missed Items ({len(comparison['misses'])}):[/bold yellow]")
            for miss in comparison["misses"][:10]:
                self.console.print(f"  • {miss['category']}: {miss['item']}")
            if len(comparison["misses"]) > 10:
                self.console.print(f"  ... and {len(comparison['misses']) - 10} more")

        # Show false positives
        if comparison["false_positives"]:
            self.console.print(f"\n[bold red]False Positives ({len(comparison['false_positives'])}):[/bold red]")
            for fp in comparison["false_positives"][:10]:
                self.console.print(f"  • {fp['category']}: {fp['item']}")
            if len(comparison["false_positives"]) > 10:
                self.console.print(f"  ... and {len(comparison['false_positives']) - 10} more")


if __name__ == "__main__":
    # Test the ground truth labeler
    labeler = GroundTruthLabeler()

    print("Ground Truth Labeling Test\n")

    gt = labeler.label_schematic("test.pdf", 0)

    if gt:
        print("\n\nGround Truth:")
        print(json.dumps(gt, indent=2))

        labeler.save_ground_truth(gt)
