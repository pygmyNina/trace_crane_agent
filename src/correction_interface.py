"""
Interactive Correction Interface
Allows user to correct Claude's schematic analysis and builds training data
"""

from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
import json
from datetime import datetime


class CorrectionInterface:
    """Interactive interface for correcting Claude's schematic analysis"""

    def __init__(self):
        self.console = Console()
        self.corrections = []

    def show_analysis(self, analysis: Dict[str, Any]):
        """Display Claude's analysis for review"""
        self.console.print("\n" + "="*80)
        self.console.print(Panel(
            f"[bold cyan]Claude's Analysis[/bold cyan]\n\n"
            f"PDF: {analysis['pdf_path']}\n"
            f"Page: {analysis['page_num'] + 1}",
            border_style="cyan"
        ))

        # Show raw response
        self.console.print(Panel(
            Markdown(analysis['raw_response']),
            title="Analysis Details",
            border_style="blue"
        ))

    def show_parsed_data(self, parsed: Dict[str, Any]):
        """Show parsed/structured data"""
        if parsed.get('components'):
            self.console.print("\n[bold green]Components Found:[/bold green]")
            for i, comp in enumerate(parsed['components'], 1):
                self.console.print(f"  {i}. {comp}")

        if parsed.get('index_references'):
            self.console.print("\n[bold green]Index References Found:[/bold green]")
            for i, ref in enumerate(parsed['index_references'], 1):
                self.console.print(f"  {i}. {ref}")

        if parsed.get('wire_connections'):
            self.console.print("\n[bold green]Wire Connections Found:[/bold green]")
            for i, conn in enumerate(parsed['wire_connections'], 1):
                self.console.print(f"  {i}. {conn}")

    def collect_corrections(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interactive session to collect corrections

        Returns corrected analysis with user feedback
        """
        self.show_analysis(analysis)
        self.show_parsed_data(analysis['parsed_analysis'])

        self.console.print("\n" + "="*80)
        self.console.print("[bold yellow]Now let's review and correct this analysis[/bold yellow]\n")

        corrected = {
            "original_analysis": analysis,
            "corrections": {},
            "ground_truth": {},
            "feedback": "",
            "timestamp": datetime.now().isoformat()
        }

        # Ask if analysis is correct
        if Confirm.ask("\nIs Claude's analysis completely correct?", default=False):
            corrected["feedback"] = "Analysis is correct"
            self.console.print("[green]✓ Great! Analysis confirmed as correct.[/green]")
            return corrected

        # Collect corrections for each category
        self.console.print("\n[bold]Let's correct each category:[/bold]\n")

        # Components
        if Confirm.ask("Review/correct COMPONENTS?", default=True):
            corrected["corrections"]["components"] = self._correct_category(
                "Components",
                analysis['parsed_analysis'].get('components', [])
            )

        # Index References
        if Confirm.ask("Review/correct INDEX REFERENCES?", default=True):
            corrected["corrections"]["index_references"] = self._correct_category(
                "Index References",
                analysis['parsed_analysis'].get('index_references', [])
            )

        # Wire Connections
        if Confirm.ask("Review/correct WIRE CONNECTIONS?", default=True):
            corrected["corrections"]["wire_connections"] = self._correct_category(
                "Wire Connections",
                analysis['parsed_analysis'].get('wire_connections', [])
            )

        # Additional feedback
        self.console.print("\n")
        feedback = Prompt.ask(
            "Any additional notes or feedback about this schematic?",
            default=""
        )
        corrected["feedback"] = feedback

        # Build ground truth
        corrected["ground_truth"] = self._build_ground_truth(corrected["corrections"])

        self.corrections.append(corrected)

        return corrected

    def _correct_category(self, category_name: str, items: List[str]) -> Dict[str, Any]:
        """Correct a specific category of analysis"""
        self.console.print(f"\n[bold cyan]Correcting: {category_name}[/bold cyan]")

        corrections = {
            "removed": [],
            "modified": [],
            "added": [],
            "correct": []
        }

        # Review each item Claude found
        for item in items:
            self.console.print(f"\n  Claude found: [yellow]{item}[/yellow]")

            choice = Prompt.ask(
                "  Is this correct?",
                choices=["correct", "wrong", "modify", "skip"],
                default="correct"
            )

            if choice == "correct":
                corrections["correct"].append(item)
            elif choice == "wrong":
                corrections["removed"].append(item)
                self.console.print(f"    [red]✗ Marked as incorrect[/red]")
            elif choice == "modify":
                corrected_item = Prompt.ask("    Enter corrected version")
                corrections["modified"].append({
                    "original": item,
                    "corrected": corrected_item
                })
                self.console.print(f"    [green]✓ Updated to: {corrected_item}[/green]")

        # Ask for missing items
        if Confirm.ask(f"\n  Did Claude miss any {category_name}?", default=False):
            self.console.print(f"  [bold]Add missing {category_name}[/bold]")
            self.console.print("  (Enter one per line, empty line to finish)")

            while True:
                missing = Prompt.ask("    Add item (or press Enter to finish)", default="")
                if not missing:
                    break
                corrections["added"].append(missing)
                self.console.print(f"    [green]✓ Added: {missing}[/green]")

        return corrections

    def _build_ground_truth(self, corrections: Dict[str, Any]) -> Dict[str, List[str]]:
        """Build ground truth from corrections"""
        ground_truth = {}

        for category, category_corrections in corrections.items():
            truth_items = []

            # Add correct items
            truth_items.extend(category_corrections.get("correct", []))

            # Add modified items (corrected version)
            for mod in category_corrections.get("modified", []):
                truth_items.append(mod["corrected"])

            # Add newly added items
            truth_items.extend(category_corrections.get("added", []))

            ground_truth[category] = truth_items

        return ground_truth

    def show_correction_summary(self, correction: Dict[str, Any]):
        """Display summary of corrections made"""
        self.console.print("\n" + "="*80)
        self.console.print(Panel(
            "[bold green]Correction Summary[/bold green]",
            border_style="green"
        ))

        for category, changes in correction["corrections"].items():
            self.console.print(f"\n[bold]{category.upper()}:[/bold]")

            if changes.get("correct"):
                self.console.print(f"  ✓ Correct: {len(changes['correct'])}")

            if changes.get("removed"):
                self.console.print(f"  ✗ Removed: {len(changes['removed'])}")
                for item in changes['removed']:
                    self.console.print(f"      - {item}")

            if changes.get("modified"):
                self.console.print(f"  ↻ Modified: {len(changes['modified'])}")
                for mod in changes['modified']:
                    self.console.print(f"      {mod['original']} → {mod['corrected']}")

            if changes.get("added"):
                self.console.print(f"  + Added: {len(changes['added'])}")
                for item in changes['added']:
                    self.console.print(f"      + {item}")

        if correction.get("feedback"):
            self.console.print(f"\n[bold]Feedback:[/bold] {correction['feedback']}")

    def export_corrections(self, output_path: str):
        """Export all corrections to a JSON file"""
        with open(output_path, 'w') as f:
            json.dump(self.corrections, f, indent=2)

        self.console.print(f"\n[green]✓ Exported {len(self.corrections)} corrections to {output_path}[/green]")

    def get_all_corrections(self) -> List[Dict[str, Any]]:
        """Get all corrections collected in this session"""
        return self.corrections


if __name__ == "__main__":
    # Test the correction interface
    console = Console()

    # Mock analysis for testing
    mock_analysis = {
        "pdf_path": "test.pdf",
        "page_num": 0,
        "raw_response": "Test analysis response",
        "parsed_analysis": {
            "components": ["HVC3", "Slave 22", "Cabinet E11"],
            "index_references": ["=61/102.0.8", "=61/103.0.7"],
            "wire_connections": ["W1 connects to W2 at terminal 5"]
        }
    }

    interface = CorrectionInterface()

    console.print("[bold cyan]Correction Interface Test[/bold cyan]\n")
    correction = interface.collect_corrections(mock_analysis)
    interface.show_correction_summary(correction)

    print("\n\nFinal correction data:")
    print(json.dumps(correction, indent=2))
