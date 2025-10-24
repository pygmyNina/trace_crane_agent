"""
Correction Logging System
Tracks mistakes, provides feedback, and helps improve training
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


class CorrectionLogger:
    """Logs and analyzes corrections during training"""

    def __init__(self, storage, session_id: str):
        """
        Initialize correction logger
        storage: TrainingStorage instance
        session_id: Current training session ID
        """
        self.storage = storage
        self.session_id = session_id
        self.corrections = []
        self.categories = defaultdict(list)

    def log_correction(self, question: str, incorrect_answer: str,
                      correct_answer: str, category: str = "general",
                      explanation: str = "", difficulty: str = "medium"):
        """
        Log a correction with detailed information

        Args:
            question: The question that was asked
            incorrect_answer: What the user answered
            correct_answer: The correct answer
            category: Category of the question (index_format, wire_tracing, etc.)
            explanation: Detailed explanation of the correction
            difficulty: Difficulty level (easy, medium, hard)
        """
        correction = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "incorrect_answer": incorrect_answer,
            "correct_answer": correct_answer,
            "category": category,
            "explanation": explanation,
            "difficulty": difficulty
        }

        self.corrections.append(correction)
        self.categories[category].append(correction)

        # Log to storage
        notes = f"Difficulty: {difficulty}\n{explanation}" if explanation else f"Difficulty: {difficulty}"
        self.storage.log_correction(
            self.session_id,
            question,
            incorrect_answer,
            correct_answer,
            category,
            notes
        )

    def get_corrections_by_category(self, category: str = None) -> List[Dict[str, Any]]:
        """Get corrections, optionally filtered by category"""
        if category:
            return self.categories.get(category, [])
        return self.corrections

    def get_problem_areas(self) -> Dict[str, Any]:
        """
        Analyze corrections to identify problem areas

        Returns:
            Dictionary with categories and their error counts
        """
        problem_areas = {}

        for category, corrections in self.categories.items():
            problem_areas[category] = {
                "count": len(corrections),
                "recent_errors": corrections[-3:] if len(corrections) >= 3 else corrections
            }

        # Sort by count
        sorted_areas = dict(sorted(problem_areas.items(),
                                  key=lambda x: x[1]["count"],
                                  reverse=True))

        return sorted_areas

    def generate_feedback(self) -> str:
        """Generate feedback based on corrections"""
        if not self.corrections:
            return "Great job! No corrections needed so far."

        feedback = "# Training Feedback\n\n"

        # Overall stats
        total_corrections = len(self.corrections)
        feedback += f"Total corrections: {total_corrections}\n\n"

        # Problem areas
        problem_areas = self.get_problem_areas()
        if problem_areas:
            feedback += "## Areas for Improvement\n\n"
            for category, data in problem_areas.items():
                feedback += f"### {category.replace('_', ' ').title()}\n"
                feedback += f"Errors: {data['count']}\n\n"

                if data['recent_errors']:
                    feedback += "Recent mistakes:\n"
                    for error in data['recent_errors']:
                        feedback += f"- Q: {error['question']}\n"
                        feedback += f"  Your answer: {error['incorrect_answer']}\n"
                        feedback += f"  Correct answer: {error['correct_answer']}\n"
                        if error.get('explanation'):
                            feedback += f"  Explanation: {error['explanation']}\n"
                        feedback += "\n"

        # Recommendations
        feedback += "## Recommendations\n\n"
        if problem_areas:
            top_category = list(problem_areas.keys())[0]
            feedback += f"Focus on: {top_category.replace('_', ' ').title()}\n"
            feedback += f"This area has the most corrections ({problem_areas[top_category]['count']})\n"

        return feedback

    def generate_review_questions(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Generate review questions from recent corrections

        Returns:
            List of questions to review
        """
        if not self.corrections:
            return []

        # Get unique questions from corrections
        review_questions = []
        seen_questions = set()

        # Prioritize recent corrections
        for correction in reversed(self.corrections):
            question = correction['question']
            if question not in seen_questions and len(review_questions) < count:
                review_questions.append({
                    "question": question,
                    "correct_answer": correction['correct_answer'],
                    "category": correction['category'],
                    "previous_mistake": correction['incorrect_answer'],
                    "explanation": correction.get('explanation', '')
                })
                seen_questions.add(question)

        return review_questions

    def export_corrections(self, output_path: str):
        """Export corrections to a JSON file"""
        export_data = {
            "session_id": self.session_id,
            "export_date": datetime.now().isoformat(),
            "total_corrections": len(self.corrections),
            "corrections": self.corrections,
            "problem_areas": self.get_problem_areas()
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def get_category_summary(self) -> Dict[str, int]:
        """Get a summary count of corrections by category"""
        summary = {}
        for category, corrections in self.categories.items():
            summary[category] = len(corrections)
        return summary

    def format_correction_report(self) -> str:
        """Format a detailed correction report"""
        if not self.corrections:
            return "No corrections logged in this session."

        report = f"# Correction Report - Session {self.session_id}\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        report += f"## Summary\n"
        report += f"- Total corrections: {len(self.corrections)}\n"
        report += f"- Categories: {len(self.categories)}\n\n"

        # Category breakdown
        report += "## Category Breakdown\n\n"
        for category, count in self.get_category_summary().items():
            report += f"- {category.replace('_', ' ').title()}: {count}\n"

        report += "\n## All Corrections\n\n"

        for i, correction in enumerate(self.corrections, 1):
            report += f"### Correction {i}\n"
            report += f"**Category**: {correction['category']}\n"
            report += f"**Time**: {correction['timestamp']}\n\n"
            report += f"**Question**: {correction['question']}\n\n"
            report += f"**Your Answer**: {correction['incorrect_answer']}\n\n"
            report += f"**Correct Answer**: {correction['correct_answer']}\n\n"

            if correction.get('explanation'):
                report += f"**Explanation**: {correction['explanation']}\n\n"

            report += "---\n\n"

        return report

    def suggest_training_focus(self) -> List[str]:
        """Suggest areas to focus on based on correction patterns"""
        suggestions = []

        problem_areas = self.get_problem_areas()

        for category, data in problem_areas.items():
            if data['count'] >= 3:
                suggestions.append(
                    f"Review {category.replace('_', ' ')} - {data['count']} mistakes"
                )

        if not suggestions:
            suggestions.append("Continue practicing all areas")

        return suggestions


# Predefined categories for crane schematics
CATEGORIES = {
    "index_format": "Index format interpretation (=XX/YY.Y.Z)",
    "wire_tracing": "Wire tracing and connections",
    "component_identification": "Component identification",
    "slave_sequence": "Slave sequence understanding",
    "module_counting": "Module counting and configuration",
    "schematic_reading": "General schematic reading",
    "notation": "Notation and shorthand",
    "location": "Component location finding"
}


def get_category_description(category: str) -> str:
    """Get description for a category"""
    return CATEGORIES.get(category, "General category")


if __name__ == "__main__":
    # Test the correction logger
    from storage import TrainingStorage

    storage = TrainingStorage()
    session_id = storage.create_session()

    logger = CorrectionLogger(storage, session_id)

    # Test logging some corrections
    logger.log_correction(
        "What does =61/102.8 expand to?",
        "=61/102.8.0",
        "=61/102.0.8",
        "index_format",
        "Remember: shorthand omits the .Y when it's .0, so the missing part is the sheet minor digit",
        "medium"
    )

    logger.log_correction(
        "Are two wires connected when they cross perpendicularly without a dot?",
        "Yes",
        "No",
        "wire_tracing",
        "Only wires with dots at crossing points are connected",
        "easy"
    )

    print(logger.generate_feedback())
    print("\n" + "="*60 + "\n")
    print(logger.format_correction_report())
