"""
Knowledge Base for TRACE
Stores and retrieves crane schematic knowledge including:
- Components (slaves, modules, cabinets)
- Connections (wires, breakers, transformers)
- Schema rules and notation
- Training corrections and learnings
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class KnowledgeBase:
    """Manages the persistent knowledge base for crane schematics"""

    def __init__(self, knowledge_file: str = "trace_knowledge.json"):
        self.knowledge_file = knowledge_file
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self) -> Dict[str, Any]:
        """Load knowledge from file or create new structure"""
        if os.path.exists(self.knowledge_file):
            with open(self.knowledge_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "schema_rules": {
                    "index_format": "=XX/YY.Y.Z",
                    "wire_rules": {
                        "dots": "connections - dots indicate connected wires",
                        "perpendicular_crossings": "no connection - perpendicular crossings without dots are not connected"
                    }
                },
                "components": {
                    "slaves": {},
                    "modules": {},
                    "cabinets": {},
                    "breakers": {},
                    "transformers": {}
                },
                "connections": [],
                "sequences": {},
                "learnings": [],
                "training_sessions": []
            }

    def save(self):
        """Persist knowledge to disk"""
        with open(self.knowledge_file, 'w') as f:
            json.dump(self.knowledge, f, indent=2)
        print(f"✓ Knowledge saved to {self.knowledge_file}")

    def add_slave(self, slave_id: int, modules: List[str], count: int, cabinet: str):
        """Add or update a slave configuration"""
        self.knowledge["components"]["slaves"][str(slave_id)] = {
            "id": slave_id,
            "modules": modules,
            "module_count": count,
            "cabinet": cabinet,
            "added": datetime.now().isoformat()
        }
        self.save()

    def add_connection(self, from_ref: str, to_ref: str, signal_type: str = None, notes: str = None):
        """Add a connection between components"""
        connection = {
            "from": from_ref,
            "to": to_ref,
            "signal_type": signal_type,
            "notes": notes,
            "added": datetime.now().isoformat()
        }
        self.knowledge["connections"].append(connection)
        self.save()

    def add_sequence(self, name: str, sequence: List[int], description: str = None):
        """Add a named sequence"""
        self.knowledge["sequences"][name] = {
            "sequence": sequence,
            "description": description,
            "added": datetime.now().isoformat()
        }
        self.save()

    def add_learning(self, topic: str, content: str, source: str = "training"):
        """Add a learning or correction"""
        learning = {
            "topic": topic,
            "content": content,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        self.knowledge["learnings"].append(learning)
        self.save()

    def add_training_session(self, session_data: Dict[str, Any]):
        """Record a training session"""
        session_data["timestamp"] = datetime.now().isoformat()
        self.knowledge["training_sessions"].append(session_data)
        self.save()

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information"""
        results = []
        query_lower = query.lower()

        # Search slaves
        for slave_id, slave_data in self.knowledge["components"]["slaves"].items():
            if (query_lower in str(slave_id).lower() or
                query_lower in str(slave_data.get("cabinet", "")).lower()):
                results.append({"type": "slave", "data": slave_data})

        # Search connections
        for conn in self.knowledge["connections"]:
            if (query_lower in conn.get("from", "").lower() or
                query_lower in conn.get("to", "").lower()):
                results.append({"type": "connection", "data": conn})

        # Search learnings
        for learning in self.knowledge["learnings"]:
            if (query_lower in learning.get("topic", "").lower() or
                query_lower in learning.get("content", "").lower()):
                results.append({"type": "learning", "data": learning})

        return results

    def get_slave(self, slave_id: int) -> Optional[Dict[str, Any]]:
        """Get slave information by ID"""
        return self.knowledge["components"]["slaves"].get(str(slave_id))

    def get_all_slaves(self) -> Dict[str, Any]:
        """Get all slaves"""
        return self.knowledge["components"]["slaves"]

    def get_connections_from(self, ref: str) -> List[Dict[str, Any]]:
        """Get all connections originating from a reference"""
        return [c for c in self.knowledge["connections"] if c["from"] == ref]

    def get_connections_to(self, ref: str) -> List[Dict[str, Any]]:
        """Get all connections going to a reference"""
        return [c for c in self.knowledge["connections"] if c["to"] == ref]

    def get_schema_rules(self) -> Dict[str, Any]:
        """Get schematic notation and rules"""
        return self.knowledge["schema_rules"]

    def export_summary(self) -> str:
        """Export a human-readable summary of the knowledge base"""
        summary = []
        summary.append("=== TRACE Knowledge Base Summary ===\n")

        summary.append(f"Schema Rules:")
        summary.append(f"  Index Format: {self.knowledge['schema_rules']['index_format']}")
        for rule, desc in self.knowledge['schema_rules']['wire_rules'].items():
            summary.append(f"  {rule}: {desc}")
        summary.append("")

        summary.append(f"Components:")
        summary.append(f"  Slaves: {len(self.knowledge['components']['slaves'])}")
        summary.append(f"  Connections: {len(self.knowledge['connections'])}")
        summary.append(f"  Sequences: {len(self.knowledge['sequences'])}")
        summary.append("")

        summary.append(f"Learning Data:")
        summary.append(f"  Learnings: {len(self.knowledge['learnings'])}")
        summary.append(f"  Training Sessions: {len(self.knowledge['training_sessions'])}")

        return "\n".join(summary)
