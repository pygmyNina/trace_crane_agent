#!/usr/bin/env python3
"""
TRACE Training System for Crane Schematics
Main entry point
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from knowledge_base import KnowledgeBase
from storage import TrainingStorage
from training_interface import TrainingInterface
from pdf_processor import SchematicPDFProcessor


class TRACETrainer:
    """Main application class"""

    def __init__(self):
        self.console = Console()
        self.storage = TrainingStorage()
        self.knowledge_base = KnowledgeBase()
        self.trainer = None

    def show_banner(self):
        """Display welcome banner"""
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   TRACE Training System for Crane Schematics                ║
║                                                              ║
║   Learn to read and interpret crane electrical schematics   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝[/bold cyan]
"""
        self.console.print(banner)

    def show_main_menu(self):
        """Display main menu"""
        menu = """
[bold yellow]Main Menu[/bold yellow]

1. Start Training Session (Interactive)
2. Quiz Mode
3. Practice Specific Category
4. Review Past Sessions
5. View Foundation Knowledge
6. Load PDF Schematic
7. Statistics
8. Exit

"""
        self.console.print(menu)

    def start_training(self, pdf_file: str = None, max_questions: int = None):
        """Start interactive training session"""
        try:
            # Ask for question limit if not provided
            if max_questions is None:
                self.console.print("\n[bold]Question Limit Configuration[/bold]")
                self.console.print("Set a limit for automatic session breaks (recommended: 10)")
                limit_input = Prompt.ask(
                    "Enter question limit (or 'unlimited')",
                    default="10"
                )
                if limit_input.lower() in ['unlimited', 'none', '0']:
                    max_questions = None
                else:
                    try:
                        max_questions = int(limit_input)
                    except ValueError:
                        max_questions = 10

            self.trainer = TrainingInterface()
            self.trainer.start_session(pdf_file)
            self.trainer.interactive_training(max_questions=max_questions)
            self.trainer.end_session()
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def start_quiz(self):
        """Start quiz mode"""
        try:
            num_questions = int(Prompt.ask("How many questions", default="10"))

            self.trainer = TrainingInterface()
            self.trainer.start_session()
            self.trainer.quiz_mode(num_questions)
            self.trainer.end_session()
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def practice_category(self):
        """Practice specific category"""
        from correction_logger import CATEGORIES

        self.console.print("\n[bold]Available Categories:[/bold]")
        for i, (key, desc) in enumerate(CATEGORIES.items(), 1):
            self.console.print(f"{i}. {key}: {desc}")

        choice = Prompt.ask("\nSelect category number")

        try:
            category_list = list(CATEGORIES.keys())
            category_idx = int(choice) - 1

            if 0 <= category_idx < len(category_list):
                category = category_list[category_idx]

                self.trainer = TrainingInterface()
                self.trainer.start_session()
                self.trainer.practice_category(category)
                self.trainer.end_session()
            else:
                self.console.print("[red]Invalid selection[/red]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def review_sessions(self):
        """Review past training sessions"""
        sessions = self.storage.list_sessions(20)

        if not sessions:
            self.console.print("[yellow]No training sessions found[/yellow]")
            return

        table = Table(title="Recent Training Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Start Time", style="green")
        table.add_column("Questions", justify="right")
        table.add_column("Correct", justify="right")
        table.add_column("Accuracy", justify="right")
        table.add_column("Status", style="yellow")

        for session in sessions:
            total = session['total_questions']
            correct = session['correct_answers']
            accuracy = f"{(correct/total*100):.1f}%" if total > 0 else "N/A"

            table.add_row(
                session['session_id'],
                session['start_time'][:19],
                str(total),
                str(correct),
                accuracy,
                session['status']
            )

        self.console.print(table)

        # Ask if user wants to see details
        if Confirm.ask("\nView details for a specific session?"):
            session_id = Prompt.ask("Enter session ID")
            self.show_session_details(session_id)

    def show_session_details(self, session_id: str):
        """Show detailed stats for a session"""
        stats = self.storage.get_session_stats(session_id)

        if not stats:
            self.console.print(f"[red]Session not found: {session_id}[/red]")
            return

        self.console.print(Panel(
            f"[bold]Session: {stats['session_id']}[/bold]\n\n"
            f"Start: {stats['start_time']}\n"
            f"End: {stats['end_time']}\n"
            f"PDF: {stats['pdf_file'] or 'None'}\n\n"
            f"Questions: {stats['total_questions']}\n"
            f"Correct: {stats['correct_answers']}\n"
            f"Incorrect: {stats['incorrect_answers']}\n"
            f"Accuracy: {stats['accuracy']:.1f}%",
            title="Session Details",
            border_style="blue"
        ))

        # Show corrections
        corrections = self.storage.get_corrections(session_id)
        if corrections:
            self.console.print(f"\n[bold]Corrections: {len(corrections)}[/bold]")
            for corr in corrections[:5]:
                self.console.print(f"\n[yellow]Q: {corr['question']}[/yellow]")
                self.console.print(f"[red]Wrong: {corr['incorrect_answer']}[/red]")
                self.console.print(f"[green]Correct: {corr['correct_answer']}[/green]")

    def show_knowledge_base(self):
        """Display foundation knowledge"""
        kb_text = self.knowledge_base.format_for_training()
        self.console.print(Panel(
            kb_text,
            title="Foundation Knowledge",
            border_style="green"
        ))

    def load_pdf(self):
        """Load and analyze a PDF schematic"""
        pdf_path = Prompt.ask("Enter PDF file path")

        if not Path(pdf_path).exists():
            self.console.print(f"[red]File not found: {pdf_path}[/red]")
            return

        try:
            with SchematicPDFProcessor(pdf_path) as processor:
                self.console.print(Panel(
                    f"[bold]PDF Loaded Successfully[/bold]\n\n"
                    f"File: {processor.pdf_path.name}\n"
                    f"Pages: {processor.num_pages}\n",
                    border_style="green"
                ))

                # Show first page info
                if processor.num_pages > 0:
                    info = processor.get_page_info(0)
                    self.console.print(f"\n[bold]Page 1 Preview:[/bold]")
                    self.console.print(f"Index references: {len(info['index_references'])}")
                    self.console.print(f"Components: {len(info['components'])}")

                # Ask if user wants to train with this PDF
                if Confirm.ask("\nStart training session with this PDF?"):
                    self.start_training(pdf_path)

        except Exception as e:
            self.console.print(f"[red]Error loading PDF: {e}[/red]")

    def show_statistics(self):
        """Show overall statistics"""
        stats = self.storage.get_category_stats()

        if not stats:
            self.console.print("[yellow]No training data available yet[/yellow]")
            return

        table = Table(title="Performance by Category")
        table.add_column("Category", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Correct", justify="right", style="green")
        table.add_column("Incorrect", justify="right", style="red")
        table.add_column("Accuracy", justify="right")

        for category, data in stats.items():
            table.add_row(
                category.replace('_', ' ').title(),
                str(data['total']),
                str(data['correct']),
                str(data['incorrect']),
                f"{data['accuracy']:.1f}%"
            )

        self.console.print(table)

    def run(self):
        """Main application loop"""
        self.show_banner()

        while True:
            self.show_main_menu()
            choice = Prompt.ask("Select option", default="1")

            if choice == "1":
                self.start_training()
            elif choice == "2":
                self.start_quiz()
            elif choice == "3":
                self.practice_category()
            elif choice == "4":
                self.review_sessions()
            elif choice == "5":
                self.show_knowledge_base()
            elif choice == "6":
                self.load_pdf()
            elif choice == "7":
                self.show_statistics()
            elif choice == "8" or choice.lower() == "exit":
                if Confirm.ask("Are you sure you want to exit?"):
                    self.console.print("\n[bold green]Thank you for training! Keep practicing![/bold green]\n")
                    break
            else:
                self.console.print("[red]Invalid choice. Please try again.[/red]")


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description="TRACE Training System for Crane Schematics"
    )
    parser.add_argument(
        "--pdf",
        help="PDF file to load for training",
        type=str
    )
    parser.add_argument(
        "--mode",
        help="Training mode: interactive, quiz, or practice",
        choices=["interactive", "quiz", "practice"],
        default="interactive"
    )
    parser.add_argument(
        "--category",
        help="Category for practice mode",
        type=str
    )
    parser.add_argument(
        "--max-questions",
        help="Maximum questions before prompting to continue (default: 10, 0 for unlimited)",
        type=int,
        default=10
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    try:
        app = TRACETrainer()

        # Convert max_questions to None if 0 or unlimited
        max_questions = None if args.max_questions == 0 else args.max_questions

        # Check if running in non-interactive mode
        if args.pdf or args.mode != "interactive":
            if args.mode == "interactive":
                app.start_training(args.pdf, max_questions=max_questions)
            elif args.mode == "quiz":
                app.start_quiz()
            elif args.mode == "practice":
                if args.category:
                    trainer = TrainingInterface()
                    trainer.start_session()
                    trainer.practice_category(args.category, max_questions=max_questions)
                    trainer.end_session()
                else:
                    app.console.print("[red]--category required for practice mode[/red]")
        else:
            # Run interactive menu
            app.run()

    except KeyboardInterrupt:
        print("\n\nTraining interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
