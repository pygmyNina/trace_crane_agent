"""
Conversational Training Interface
Uses Claude AI to provide interactive TRACE training for crane schematics
"""

import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

from knowledge_base import KnowledgeBase
from storage import TrainingStorage
from correction_logger import CorrectionLogger, CATEGORIES
from pdf_processor import SchematicPDFProcessor


class TrainingInterface:
    """Interactive training interface using Claude AI"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the training interface"""
        self.console = Console()

        # Initialize API key
        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it as an environment variable or pass it to the constructor."
            )

        self.client = anthropic.Anthropic(api_key=api_key)

        # Initialize components
        self.knowledge_base = KnowledgeBase()
        self.storage = TrainingStorage()
        self.session_id = None
        self.correction_logger = None

        # Conversation history
        self.conversation_history = []

        # Current PDF processor
        self.pdf_processor = None

    def start_session(self, pdf_file: Optional[str] = None) -> str:
        """Start a new training session"""
        self.session_id = self.storage.create_session(pdf_file)
        self.correction_logger = CorrectionLogger(self.storage, self.session_id)

        # Load PDF if provided
        if pdf_file and Path(pdf_file).exists():
            self.pdf_processor = SchematicPDFProcessor(pdf_file)
            self.storage.add_pdf(
                Path(pdf_file).name,
                self.pdf_processor.num_pages,
                f"Loaded for session {self.session_id}"
            )

        self.console.print(Panel(
            f"[bold green]Training Session Started[/bold green]\n"
            f"Session ID: {self.session_id}\n"
            f"PDF: {pdf_file if pdf_file else 'None'}",
            title="TRACE Training",
            border_style="green"
        ))

        return self.session_id

    def end_session(self):
        """End the current training session"""
        if self.session_id:
            self.storage.end_session(self.session_id)

            # Show session stats
            stats = self.storage.get_session_stats(self.session_id)

            self.console.print(Panel(
                f"[bold blue]Session Complete[/bold blue]\n\n"
                f"Questions: {stats['total_questions']}\n"
                f"Correct: {stats['correct_answers']}\n"
                f"Accuracy: {stats['accuracy']:.1f}%\n\n"
                f"{self.correction_logger.generate_feedback()}",
                title="Session Summary",
                border_style="blue"
            ))

            # Close PDF if open
            if self.pdf_processor:
                self.pdf_processor.close()

    def _build_system_prompt(self) -> str:
        """Build the system prompt with foundation knowledge"""
        kb_context = self.knowledge_base.format_for_training()

        system_prompt = f"""You are a TRACE training assistant for crane schematics. Your role is to:

1. Teach users how to read and interpret crane electrical schematics
2. Ask questions to test their understanding
3. Provide corrections and explanations when they make mistakes
4. Track their progress and identify areas for improvement

# Foundation Knowledge

{kb_context}

# Training Approach

- Ask clear, specific questions about the schematics
- When the user answers incorrectly, provide a detailed explanation
- Categorize each question using these categories: {', '.join(CATEGORIES.keys())}
- Be encouraging and educational
- Use the index notation correctly in all your questions
- When discussing wire connections, always clarify the presence or absence of connection dots

# Question Types

You should ask questions about:
- Index format interpretation and expansion
- Wire tracing and connection identification
- Component locations
- Slave configurations
- Module counting
- Schematic notation

Always format your responses clearly and provide detailed explanations for corrections.
"""

        # Add PDF context if available
        if self.pdf_processor:
            system_prompt += f"\n\n# Current PDF\n"
            system_prompt += f"Pages: {self.pdf_processor.num_pages}\n"
            system_prompt += f"Filename: {self.pdf_processor.pdf_path.name}\n"

        return system_prompt

    def chat(self, user_message: str) -> str:
        """Send a message and get response from Claude"""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Call Claude API
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            system=self._build_system_prompt(),
            messages=self.conversation_history
        )

        # Extract assistant's response
        assistant_message = response.content[0].text

        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def interactive_training(self):
        """Run interactive training session"""
        self.console.print(Panel(
            "[bold cyan]Interactive Training Mode[/bold cyan]\n\n"
            "The AI trainer will ask you questions about crane schematics.\n"
            "Answer to the best of your ability.\n\n"
            "Commands:\n"
            "- Type 'quit' or 'exit' to end session\n"
            "- Type 'feedback' to see your progress\n"
            "- Type 'help' for assistance",
            border_style="cyan"
        ))

        # Start with AI introduction
        intro = self.chat(
            "Please introduce yourself and ask me your first question about crane schematics. "
            "Make it a foundational question about the index format."
        )

        self.console.print(Panel(Markdown(intro), title="AI Trainer", border_style="cyan"))

        while True:
            # Get user input
            user_input = Prompt.ask("\n[bold yellow]Your answer[/bold yellow]")

            # Check for commands
            if user_input.lower() in ['quit', 'exit']:
                if Confirm.ask("Are you sure you want to end the training session?"):
                    break
                continue

            if user_input.lower() == 'feedback':
                self.console.print(Panel(
                    self.correction_logger.generate_feedback(),
                    title="Current Feedback",
                    border_style="blue"
                ))
                continue

            if user_input.lower() == 'help':
                self.console.print(Panel(
                    self.knowledge_base.format_for_training(),
                    title="Foundation Knowledge",
                    border_style="green"
                ))
                continue

            # Send to AI
            response = self.chat(user_input)

            # Display response
            self.console.print(Panel(Markdown(response), title="AI Trainer", border_style="cyan"))

    def quiz_mode(self, num_questions: int = 10):
        """Run a structured quiz"""
        self.console.print(Panel(
            f"[bold magenta]Quiz Mode[/bold magenta]\n\n"
            f"You will be asked {num_questions} questions.\n"
            f"Answer carefully - your score will be tracked!",
            border_style="magenta"
        ))

        # Request quiz questions
        quiz_request = f"""Please create a quiz with {num_questions} questions about crane schematics.
Cover these categories: {', '.join(CATEGORIES.keys())}

Format each question clearly and number them.
After I answer all questions, provide my score and corrections.
"""

        response = self.chat(quiz_request)
        self.console.print(Panel(Markdown(response), title="Quiz", border_style="magenta"))

        # Continue conversation for answers
        answers_remaining = True
        while answers_remaining:
            user_input = Prompt.ask("\n[bold yellow]Your answer[/bold yellow]")

            if user_input.lower() in ['quit', 'exit']:
                break

            response = self.chat(user_input)
            self.console.print(Panel(Markdown(response), title="Quiz", border_style="magenta"))

            # Check if quiz is complete
            if "score" in response.lower() or "completed" in response.lower():
                answers_remaining = False

    def review_corrections(self):
        """Review past corrections"""
        corrections = self.storage.get_corrections(self.session_id)

        if not corrections:
            self.console.print("[yellow]No corrections to review yet![/yellow]")
            return

        self.console.print(Panel(
            f"[bold blue]Reviewing {len(corrections)} Corrections[/bold blue]",
            border_style="blue"
        ))

        for i, corr in enumerate(corrections, 1):
            self.console.print(f"\n[bold]Correction {i}[/bold]")
            self.console.print(f"Category: {corr['category']}")
            self.console.print(f"Q: {corr['question']}")
            self.console.print(f"[red]Your answer: {corr['incorrect_answer']}[/red]")
            self.console.print(f"[green]Correct answer: {corr['correct_answer']}[/green]")

            if corr['notes']:
                self.console.print(f"Notes: {corr['notes']}")

            self.console.print("-" * 60)

    def practice_category(self, category: str):
        """Practice a specific category"""
        if category not in CATEGORIES:
            self.console.print(f"[red]Unknown category: {category}[/red]")
            self.console.print(f"Available categories: {', '.join(CATEGORIES.keys())}")
            return

        self.console.print(Panel(
            f"[bold green]Practice: {CATEGORIES[category]}[/bold green]",
            border_style="green"
        ))

        # Request category-specific questions
        request = f"""Please focus on the '{category}' category ({CATEGORIES[category]}).
Ask me 3-5 questions specifically about this topic.
Provide detailed explanations for any incorrect answers.
"""

        response = self.chat(request)
        self.console.print(Panel(Markdown(response), title="Practice", border_style="green"))

        # Continue practice session
        while True:
            user_input = Prompt.ask("\n[bold yellow]Your answer[/bold yellow]")

            if user_input.lower() in ['quit', 'exit', 'done']:
                break

            response = self.chat(user_input)
            self.console.print(Panel(Markdown(response), title="Practice", border_style="green"))

    def load_pdf_page(self, page_num: int):
        """Load and discuss a specific PDF page"""
        if not self.pdf_processor:
            self.console.print("[red]No PDF loaded in this session[/red]")
            return

        try:
            context = self.pdf_processor.create_training_context(page_num)

            # Send context to AI
            request = f"""Here is page {page_num + 1} from the schematic:

{context}

Please analyze this page and ask me 2-3 questions about it.
Focus on the index references and components found on this page.
"""

            response = self.chat(request)
            self.console.print(Panel(
                Markdown(response),
                title=f"Page {page_num + 1} Analysis",
                border_style="cyan"
            ))

        except Exception as e:
            self.console.print(f"[red]Error loading page: {e}[/red]")


if __name__ == "__main__":
    # Test the training interface
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    try:
        trainer = TrainingInterface()
        trainer.start_session()

        # Run interactive training
        trainer.interactive_training()

        trainer.end_session()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
