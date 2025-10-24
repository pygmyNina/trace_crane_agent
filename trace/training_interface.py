"""
Conversational Training Interface for TRACE
Allows mechanics to train the system through natural conversation
"""

from typing import Dict, List, Any, Optional
from trace.knowledge_base import KnowledgeBase
import re


class TrainingInterface:
    """Interactive training interface for TRACE"""

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self.session_log = []

    def process_training_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process natural language training input and extract knowledge
        Returns a response with extracted information and confirmation
        """
        response = {
            "understood": [],
            "needs_clarification": [],
            "saved": False,
            "message": ""
        }

        # Log the input
        self.session_log.append({"input": user_input, "type": "training"})

        # Parse different types of training inputs
        parsed = self._parse_training_input(user_input)

        if parsed["type"] == "slave_config":
            self._handle_slave_config(parsed, response)
        elif parsed["type"] == "connection":
            self._handle_connection(parsed, response)
        elif parsed["type"] == "sequence":
            self._handle_sequence(parsed, response)
        elif parsed["type"] == "rule":
            self._handle_rule(parsed, response)
        elif parsed["type"] == "correction":
            self._handle_correction(parsed, response)
        else:
            response["message"] = "I'm ready to learn. You can tell me about:\n" \
                                  "- Slave configurations (e.g., 'Slave 22 has 45 modules in Cabinet E11')\n" \
                                  "- Connections (e.g., 'HVC3 breaker signal goes to =61/4.1.3')\n" \
                                  "- Sequences (e.g., 'Slave sequence: 22,23,60,24,61,20')\n" \
                                  "- Rules (e.g., 'Wire rule: dots indicate connections')\n" \
                                  "- Corrections to previous information"

        return response

    def _parse_training_input(self, text: str) -> Dict[str, Any]:
        """Parse training input to determine type and extract data"""
        text_lower = text.lower()

        # Slave configuration: "Slave X has Y modules in Cabinet Z"
        slave_pattern = r'slave\s+(\d+).*?(\d+)\s+modules?.*?cabinet\s+([A-Z]\d+)'
        if match := re.search(slave_pattern, text, re.IGNORECASE):
            modules_detail = self._extract_module_details(text)
            return {
                "type": "slave_config",
                "slave_id": int(match.group(1)),
                "module_count": int(match.group(2)),
                "cabinet": match.group(3),
                "modules": modules_detail
            }

        # Connection: "X goes to Y" or "X connects to Y"
        connection_pattern = r'(.+?)\s+(?:goes to|connects to|→)\s+(.+)'
        if match := re.search(connection_pattern, text, re.IGNORECASE):
            return {
                "type": "connection",
                "from": match.group(1).strip(),
                "to": match.group(2).strip()
            }

        # Sequence: "sequence: 1,2,3,4"
        sequence_pattern = r'sequence[:\s]+(\d+(?:,\s*\d+)+)'
        if match := re.search(sequence_pattern, text, re.IGNORECASE):
            sequence_nums = [int(x.strip()) for x in match.group(1).split(',')]
            # Extract sequence name if present
            name_match = re.search(r'(\w+)\s+sequence', text, re.IGNORECASE)
            name = name_match.group(1) if name_match else "unnamed_sequence"
            return {
                "type": "sequence",
                "name": name,
                "sequence": sequence_nums
            }

        # Rules: "wire rule:" or "index format:"
        if 'rule' in text_lower or 'format' in text_lower:
            return {
                "type": "rule",
                "content": text
            }

        # Corrections: "actually", "correction", "I meant"
        if any(word in text_lower for word in ['actually', 'correction', 'i meant', 'wrong']):
            return {
                "type": "correction",
                "content": text
            }

        return {"type": "unknown", "content": text}

    def _extract_module_details(self, text: str) -> List[str]:
        """Extract module type details from text (e.g., '1 IM151, 1 PM, 40 DI, 3 RTD')"""
        # Pattern: number followed by module type
        pattern = r'(\d+)\s+([A-Z][A-Z0-9]+)'
        matches = re.findall(pattern, text)
        modules = []
        for count, module_type in matches:
            modules.extend([module_type] * int(count))
        return modules if modules else []

    def _handle_slave_config(self, parsed: Dict[str, Any], response: Dict[str, Any]):
        """Handle slave configuration training"""
        self.kb.add_slave(
            slave_id=parsed["slave_id"],
            modules=parsed.get("modules", []),
            count=parsed["module_count"],
            cabinet=parsed["cabinet"]
        )

        response["understood"].append(
            f"Slave {parsed['slave_id']}: {parsed['module_count']} modules in {parsed['cabinet']}"
        )
        if parsed.get("modules"):
            response["understood"].append(f"  Module breakdown: {', '.join(parsed['modules'][:5])}" +
                                          (f"... ({len(parsed['modules'])} total)" if len(parsed['modules']) > 5 else ""))
        response["saved"] = True
        response["message"] = f"✓ Learned about Slave {parsed['slave_id']}"

    def _handle_connection(self, parsed: Dict[str, Any], response: Dict[str, Any]):
        """Handle connection training"""
        self.kb.add_connection(
            from_ref=parsed["from"],
            to_ref=parsed["to"]
        )

        response["understood"].append(f"Connection: {parsed['from']} → {parsed['to']}")
        response["saved"] = True
        response["message"] = f"✓ Learned connection from {parsed['from']} to {parsed['to']}"

    def _handle_sequence(self, parsed: Dict[str, Any], response: Dict[str, Any]):
        """Handle sequence training"""
        self.kb.add_sequence(
            name=parsed["name"],
            sequence=parsed["sequence"]
        )

        response["understood"].append(f"Sequence '{parsed['name']}': {parsed['sequence']}")
        response["saved"] = True
        response["message"] = f"✓ Learned {parsed['name']} sequence"

    def _handle_rule(self, parsed: Dict[str, Any], response: Dict[str, Any]):
        """Handle rule/notation training"""
        self.kb.add_learning(
            topic="schema_rule",
            content=parsed["content"]
        )

        response["understood"].append(f"Rule: {parsed['content']}")
        response["saved"] = True
        response["message"] = "✓ Learned new schematic rule"

    def _handle_correction(self, parsed: Dict[str, Any], response: Dict[str, Any]):
        """Handle corrections to previous training"""
        self.kb.add_learning(
            topic="correction",
            content=parsed["content"],
            source="correction"
        )

        response["understood"].append("Correction noted")
        response["saved"] = True
        response["message"] = "✓ Saved correction for review"

    def end_session(self):
        """Save training session log"""
        if self.session_log:
            self.kb.add_training_session({
                "log": self.session_log,
                "items_count": len(self.session_log)
            })
            self.session_log = []
