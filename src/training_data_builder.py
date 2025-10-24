"""
Training Data Builder
Converts corrections into training examples for fine-tuning and knowledge base updates
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import base64


class TrainingDataBuilder:
    """Builds training datasets from corrections"""

    def __init__(self, output_dir: str = "data/training_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.examples_file = self.output_dir / "training_examples.jsonl"
        self.knowledge_file = self.output_dir / "learned_knowledge.json"
        self.finetuning_file = self.output_dir / "finetuning_dataset.jsonl"

        self.learned_knowledge = self._load_knowledge()

    def _load_knowledge(self) -> Dict[str, Any]:
        """Load existing learned knowledge"""
        if self.knowledge_file.exists():
            with open(self.knowledge_file, 'r') as f:
                return json.load(f)
        return {
            "component_patterns": [],
            "index_reference_patterns": [],
            "wire_connection_patterns": [],
            "common_mistakes": [],
            "validated_examples": [],
            "last_updated": datetime.now().isoformat()
        }

    def add_correction(self, correction: Dict[str, Any], image_base64: str = None):
        """
        Add a correction to the training dataset

        Args:
            correction: Correction data from CorrectionInterface
            image_base64: Optional base64-encoded schematic image
        """
        # Create training example
        training_example = self._create_training_example(correction, image_base64)

        # Append to training examples file
        with open(self.examples_file, 'a') as f:
            f.write(json.dumps(training_example) + "\n")

        # Update learned knowledge
        self._update_knowledge(correction)

        # Create fine-tuning example
        if image_base64:
            finetuning_example = self._create_finetuning_example(correction, image_base64)
            with open(self.finetuning_file, 'a') as f:
                f.write(json.dumps(finetuning_example) + "\n")

    def _create_training_example(self, correction: Dict[str, Any],
                                 image_base64: str = None) -> Dict[str, Any]:
        """Create a structured training example"""
        example = {
            "timestamp": correction.get("timestamp", datetime.now().isoformat()),
            "pdf_path": correction["original_analysis"]["pdf_path"],
            "page_num": correction["original_analysis"]["page_num"],
            "original_analysis": correction["original_analysis"]["raw_response"],
            "corrections": correction["corrections"],
            "ground_truth": correction["ground_truth"],
            "feedback": correction.get("feedback", ""),
        }

        if image_base64:
            example["image_base64"] = image_base64

        return example

    def _create_finetuning_example(self, correction: Dict[str, Any],
                                   image_base64: str) -> Dict[str, Any]:
        """
        Create example in Anthropic's fine-tuning format

        Format for vision fine-tuning:
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", ...}},
                        {"type": "text", "text": "Analyze this schematic..."}
                    ]
                },
                {
                    "role": "assistant",
                    "content": "Correct analysis here..."
                }
            ]
        }
        """
        # Build the corrected response
        corrected_response = self._build_correct_response(correction["ground_truth"])

        return {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": "Analyze this crane schematic and identify components, index references, and wire connections."
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": corrected_response
                }
            ]
        }

    def _build_correct_response(self, ground_truth: Dict[str, List[str]]) -> str:
        """Build the correct analysis response from ground truth"""
        response = "# Schematic Analysis\n\n"

        if ground_truth.get("components"):
            response += "## COMPONENTS\n\n"
            for comp in ground_truth["components"]:
                response += f"- {comp}\n"
            response += "\n"

        if ground_truth.get("index_references"):
            response += "## INDEX REFERENCES\n\n"
            for ref in ground_truth["index_references"]:
                response += f"- {ref}\n"
            response += "\n"

        if ground_truth.get("wire_connections"):
            response += "## WIRE CONNECTIONS\n\n"
            for conn in ground_truth["wire_connections"]:
                response += f"- {conn}\n"
            response += "\n"

        return response

    def _update_knowledge(self, correction: Dict[str, Any]):
        """Update learned knowledge base with new patterns"""
        # Extract patterns from corrections
        for category, changes in correction["corrections"].items():
            # Track common mistakes
            if changes.get("removed") or changes.get("modified"):
                for wrong_item in changes.get("removed", []):
                    self.learned_knowledge["common_mistakes"].append({
                        "category": category,
                        "mistake": wrong_item,
                        "timestamp": correction["timestamp"]
                    })

                for mod in changes.get("modified", []):
                    self.learned_knowledge["common_mistakes"].append({
                        "category": category,
                        "mistake": mod["original"],
                        "correction": mod["corrected"],
                        "timestamp": correction["timestamp"]
                    })

        # Add validated examples
        if correction.get("ground_truth"):
            self.learned_knowledge["validated_examples"].append({
                "pdf": correction["original_analysis"]["pdf_path"],
                "page": correction["original_analysis"]["page_num"],
                "ground_truth": correction["ground_truth"],
                "timestamp": correction["timestamp"]
            })

        # Update timestamp
        self.learned_knowledge["last_updated"] = datetime.now().isoformat()

        # Save updated knowledge
        with open(self.knowledge_file, 'w') as f:
            json.dump(self.learned_knowledge, f, indent=2)

    def get_few_shot_examples(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get n most recent validated examples for few-shot learning

        Returns examples in format suitable for including in prompts
        """
        examples = self.learned_knowledge.get("validated_examples", [])

        # Get n most recent
        recent = sorted(examples, key=lambda x: x["timestamp"], reverse=True)[:n]

        # Format for prompts
        formatted = []
        for ex in recent:
            formatted.append({
                "schematic": f"{ex['pdf']} page {ex['page'] + 1}",
                "ground_truth": ex["ground_truth"]
            })

        return formatted

    def get_common_mistakes(self, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get common mistakes, optionally filtered by category"""
        mistakes = self.learned_knowledge.get("common_mistakes", [])

        if category:
            mistakes = [m for m in mistakes if m.get("category") == category]

        # Get most recent
        recent = sorted(mistakes, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

        return recent

    def generate_improved_prompt(self) -> str:
        """
        Generate an improved analysis prompt based on learned patterns

        This incorporates few-shot examples and common mistakes
        """
        prompt = """You are analyzing a crane electrical schematic.

# Important Rules

## Index Format
- Format: =XX/YY.Y.Z
- Shorthand: =XX/YY.Z means =XX/YY.0.Z
- Be precise with the exact format as it appears

## Wire Connections
- Only mark connections where there's a clear dot at the crossing
- Perpendicular crossings without dots are NOT connections

## Component Identification
- Use exact labels as they appear on the schematic
- Don't infer component types unless clearly labeled

"""

        # Add common mistakes section
        mistakes = self.get_common_mistakes(limit=5)
        if mistakes:
            prompt += "\n# Common Mistakes to Avoid\n\n"
            for mistake in mistakes:
                if "correction" in mistake:
                    prompt += f"- Don't confuse '{mistake['mistake']}' with '{mistake['correction']}'\n"
                else:
                    prompt += f"- Avoid incorrectly identifying: {mistake['mistake']}\n"
            prompt += "\n"

        # Add few-shot examples
        examples = self.get_few_shot_examples(n=3)
        if examples:
            prompt += "\n# Example Analyses\n\n"
            for i, ex in enumerate(examples, 1):
                prompt += f"## Example {i}: {ex['schematic']}\n\n"
                for category, items in ex['ground_truth'].items():
                    if items:
                        prompt += f"### {category.upper()}:\n"
                        for item in items:
                            prompt += f"- {item}\n"
                        prompt += "\n"

        prompt += """
# Now Analyze This Schematic

Provide detailed analysis with:
1. COMPONENTS - List all identifiable components
2. INDEX REFERENCES - List all index references (=XX/YY.Y.Z)
3. WIRE CONNECTIONS - Identify wire connections and labels

Be specific and precise. Use exact labels as they appear.
"""

        return prompt

    def export_for_finetuning(self, output_path: str = None):
        """Export training data in format ready for fine-tuning submission"""
        if output_path is None:
            output_path = self.output_dir / "finetuning_ready.jsonl"

        # Copy the fine-tuning file
        if self.finetuning_file.exists():
            import shutil
            shutil.copy(self.finetuning_file, output_path)
            return output_path
        return None

    def get_training_stats(self) -> Dict[str, Any]:
        """Get statistics about training data collected"""
        stats = {
            "total_examples": 0,
            "total_corrections": 0,
            "total_mistakes": len(self.learned_knowledge.get("common_mistakes", [])),
            "validated_examples": len(self.learned_knowledge.get("validated_examples", [])),
            "last_updated": self.learned_knowledge.get("last_updated", "Never")
        }

        # Count examples in file
        if self.examples_file.exists():
            with open(self.examples_file, 'r') as f:
                stats["total_examples"] = sum(1 for _ in f)

        return stats


if __name__ == "__main__":
    # Test the training data builder
    builder = TrainingDataBuilder()

    print("Training Data Builder Test")
    print("="*60)

    # Mock correction
    mock_correction = {
        "timestamp": datetime.now().isoformat(),
        "original_analysis": {
            "pdf_path": "test.pdf",
            "page_num": 0,
            "raw_response": "Found HVC3, Slave 22"
        },
        "corrections": {
            "components": {
                "correct": ["HVC3"],
                "removed": [],
                "modified": [{"original": "Slave 22", "corrected": "Slave 23"}],
                "added": ["Cabinet E11"]
            }
        },
        "ground_truth": {
            "components": ["HVC3", "Slave 23", "Cabinet E11"]
        },
        "feedback": "Slave number was wrong"
    }

    builder.add_correction(mock_correction)

    print("\nTraining Stats:")
    print(json.dumps(builder.get_training_stats(), indent=2))

    print("\nCommon Mistakes:")
    print(json.dumps(builder.get_common_mistakes(limit=3), indent=2))

    print("\nImproved Prompt:")
    print(builder.generate_improved_prompt())
