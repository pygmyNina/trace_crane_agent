"""
Knowledge Base for Crane Schematics TRACE Training
Contains foundation rules from October 23 training
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class KnowledgeBase:
    """Manages the foundation knowledge for crane schematic interpretation"""

    def __init__(self, data_dir: str = "data/knowledge_base"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.kb_file = self.data_dir / "foundation.json"
        self.knowledge = self._load_or_create_foundation()

    def _create_foundation(self) -> Dict[str, Any]:
        """Create the foundation knowledge base from October 23 training"""
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),

            "index_format": {
                "description": "Crane schematic index format",
                "format": "=XX/YY.Y.Z",
                "components": {
                    "XX": "Section number (2 digits)",
                    "YY.Y": "Sheet number (2 digits + 1 decimal digit)",
                    "Z": "Column number (1 digit)"
                },
                "shorthand": {
                    "description": "When column is in first major section (.0), it can be omitted",
                    "example": "=61/102.8 means =61/102.0.8",
                    "full_form": "=XX/YY.Y.Z",
                    "short_form": "=XX/YY.Z (when Y decimal = 0)"
                }
            },

            "wire_tracing": {
                "rules": [
                    {
                        "rule": "Dots indicate connections",
                        "description": "When wires cross with a dot, they are electrically connected"
                    },
                    {
                        "rule": "Perpendicular crossings without dots are NOT connections",
                        "description": "When wires cross at 90 degrees without a dot, they pass over/under without connecting"
                    }
                ]
            },

            "slave_sequence": {
                "description": "Slave sequence is non-chronological",
                "sequence": [22, 23, 60, 24, 61, 20],
                "note": "Do NOT assume slaves are numbered sequentially"
            },

            "component_examples": {
                "slave_22": {
                    "location": "Cabinet E11",
                    "modules": {
                        "total": 45,
                        "breakdown": {
                            "IM151": 1,
                            "PM": 1,
                            "DI": 40,
                            "RTD": 3
                        }
                    }
                },
                "components": [
                    {
                        "name": "HVC3",
                        "index": "=10/103.0.7",
                        "type": "Component"
                    },
                    {
                        "name": "Main Transformer",
                        "index": "=10/102.0.3",
                        "type": "Component"
                    }
                ]
            },

            "training_tips": [
                "Always verify the full index format, including section, sheet, and column",
                "Pay attention to shorthand notation - missing .Y means it's .0",
                "When tracing wires, look carefully for connection dots",
                "Remember slave sequence is non-chronological: 22,23,60,24,61,20",
                "Count modules carefully - verify total against expected configuration"
            ]
        }

    def _load_or_create_foundation(self) -> Dict[str, Any]:
        """Load existing knowledge base or create new one"""
        if self.kb_file.exists():
            with open(self.kb_file, 'r') as f:
                return json.load(f)
        else:
            kb = self._create_foundation()
            # Save directly without using self.knowledge (not set yet)
            with open(self.kb_file, 'w') as f:
                json.dump(kb, f, indent=2)
            return kb

    def save(self):
        """Save knowledge base to disk"""
        self.knowledge["last_updated"] = datetime.now().isoformat()
        with open(self.kb_file, 'w') as f:
            json.dump(self.knowledge, f, indent=2)

    def get_index_format_help(self) -> str:
        """Get help text for index format"""
        fmt = self.knowledge["index_format"]
        return f"""
Index Format: {fmt['format']}
- {fmt['components']['XX']}: XX
- {fmt['components']['YY.Y']}: YY.Y
- {fmt['components']['Z']}: Z

Shorthand: {fmt['shorthand']['example']}
Full form: {fmt['shorthand']['full_form']}
Short form: {fmt['shorthand']['short_form']}
"""

    def get_wire_tracing_rules(self) -> List[Dict[str, str]]:
        """Get wire tracing rules"""
        return self.knowledge["wire_tracing"]["rules"]

    def get_slave_sequence(self) -> List[int]:
        """Get the non-chronological slave sequence"""
        return self.knowledge["slave_sequence"]["sequence"]

    def get_component_examples(self) -> Dict[str, Any]:
        """Get component examples"""
        return self.knowledge["component_examples"]

    def add_rule(self, category: str, rule: Dict[str, Any]):
        """Add a new rule to the knowledge base"""
        if category not in self.knowledge:
            self.knowledge[category] = []
        self.knowledge[category].append(rule)
        self.save()

    def get_full_knowledge(self) -> Dict[str, Any]:
        """Get the complete knowledge base"""
        return self.knowledge

    def format_for_training(self) -> str:
        """Format knowledge base as training context"""
        kb = self.knowledge

        context = "# Crane Schematics Foundation Knowledge\n\n"

        # Index format
        context += "## Index Format\n"
        context += f"Format: {kb['index_format']['format']}\n"
        context += f"- XX: {kb['index_format']['components']['XX']}\n"
        context += f"- YY.Y: {kb['index_format']['components']['YY.Y']}\n"
        context += f"- Z: {kb['index_format']['components']['Z']}\n\n"
        context += f"**Shorthand**: {kb['index_format']['shorthand']['description']}\n"
        context += f"Example: {kb['index_format']['shorthand']['example']}\n\n"

        # Wire tracing
        context += "## Wire Tracing Rules\n"
        for rule in kb['wire_tracing']['rules']:
            context += f"- **{rule['rule']}**: {rule['description']}\n"
        context += "\n"

        # Slave sequence
        context += "## Slave Sequence\n"
        context += f"{kb['slave_sequence']['description']}\n"
        context += f"Sequence: {', '.join(map(str, kb['slave_sequence']['sequence']))}\n"
        context += f"Note: {kb['slave_sequence']['note']}\n\n"

        # Component examples
        context += "## Component Examples\n"
        context += "### Slave 22\n"
        slave22 = kb['component_examples']['slave_22']
        context += f"Location: {slave22['location']}\n"
        context += f"Total modules: {slave22['modules']['total']}\n"
        context += "Breakdown:\n"
        for module_type, count in slave22['modules']['breakdown'].items():
            context += f"  - {module_type}: {count}\n"
        context += "\n### Other Components\n"
        for comp in kb['component_examples']['components']:
            context += f"- {comp['name']}: {comp['index']}\n"

        return context


if __name__ == "__main__":
    # Test the knowledge base
    kb = KnowledgeBase()
    print("Knowledge Base Created Successfully!")
    print("\n" + "="*60)
    print(kb.format_for_training())
    print("="*60)
    print(f"\nKnowledge base saved to: {kb.kb_file}")
