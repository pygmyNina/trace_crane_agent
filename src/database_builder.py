"""
Database Builder
Populates the searchable component database from training data
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from database_schema import SchematicDatabase


class DatabaseBuilder:
    """Builds searchable database from training data"""

    def __init__(self, db_path: str = "data/copilot/schematic_knowledge.db"):
        self.db = SchematicDatabase(db_path)
        self.stats = {
            "components_added": 0,
            "connections_added": 0,
            "pages_indexed": 0,
            "sources_processed": 0
        }

    def build_from_ground_truth(self, ground_truth_dir: str = "data/ground_truth"):
        """
        Build database from ground truth JSON files

        Args:
            ground_truth_dir: Directory containing ground truth JSON files
        """
        gt_path = Path(ground_truth_dir)

        if not gt_path.exists():
            print(f"Ground truth directory not found: {ground_truth_dir}")
            return

        json_files = list(gt_path.glob("*.json"))

        if not json_files:
            print(f"No ground truth files found in {ground_truth_dir}")
            return

        print(f"\nProcessing {len(json_files)} ground truth files...")

        for gt_file in json_files:
            self._process_ground_truth_file(gt_file)

        print(f"\n✓ Processed {len(json_files)} ground truth files")

    def _process_ground_truth_file(self, gt_file: Path):
        """Process a single ground truth JSON file"""
        try:
            with open(gt_file, 'r') as f:
                data = json.load(f)

            pdf_filename = data.get("pdf_path", "").split("/")[-1]
            page_num = data.get("page_num", 0)

            # Extract section from filename or ground truth
            section = self._extract_section(pdf_filename, data)

            # Register page
            page_id = self.db.add_schematic_page(
                pdf_filename=pdf_filename,
                page_number=page_num,
                section=section,
                ground_truth_file=str(gt_file)
            )

            ground_truth = data.get("ground_truth", {})

            # Process components
            components_added = self._process_components(
                ground_truth.get("components", []),
                pdf_filename,
                page_num,
                section
            )

            # Process wire connections
            connections_added = self._process_wire_connections(
                ground_truth.get("wire_connections", []),
                pdf_filename
            )

            # Track source
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO training_sources
                (source_file, source_type, components_added, connections_added)
                VALUES (?, ?, ?, ?)
            """, (str(gt_file), "ground_truth", components_added, connections_added))
            self.db.conn.commit()

            self.stats["components_added"] += components_added
            self.stats["connections_added"] += connections_added
            self.stats["pages_indexed"] += 1
            self.stats["sources_processed"] += 1

            print(f"  ✓ {gt_file.name}: {components_added} components, {connections_added} connections")

        except Exception as e:
            print(f"  ✗ Error processing {gt_file.name}: {e}")

    def _process_components(self, components: List[str], pdf_filename: str,
                           page_num: int, section: int = None) -> int:
        """
        Process component list and add to database

        Components can be in various formats:
        - "HVC3"
        - "Slave 23 in Cabinet E11"
        - "IM151 module at =61/102.0.8"
        - "Slave 23: 45 modules, IM151-1, PM, DI40, RTD3"
        """
        count = 0

        for comp_str in components:
            try:
                # Parse component string
                parsed = self._parse_component_string(comp_str)

                # Add to database
                self.db.add_component(
                    name=parsed["name"],
                    component_type=parsed.get("type"),
                    index_reference=parsed.get("index_reference"),
                    cabinet=parsed.get("cabinet"),
                    specifications=parsed.get("specifications"),
                    notes=parsed.get("notes"),
                    pdf_filename=pdf_filename,
                    page_number=page_num,
                    section=section
                )
                count += 1
            except Exception as e:
                print(f"    Warning: Could not parse component '{comp_str}': {e}")

        return count

    def _parse_component_string(self, comp_str: str) -> Dict[str, Any]:
        """
        Parse component string into structured data

        Examples:
        - "HVC3" → {name: "HVC3"}
        - "Slave 23 in Cabinet E11" → {name: "Slave 23", cabinet: "Cabinet E11"}
        - "Slave 23: 45 modules, IM151-1, PM, DI40, RTD3" → {name: "Slave 23", specifications: {...}}
        """
        result = {}

        # Extract index reference if present
        index_pattern = r'(=\d{2}/\d{2,3}\.\d+\.?\d*)'
        index_match = re.search(index_pattern, comp_str)
        if index_match:
            result["index_reference"] = index_match.group(1)
            comp_str = comp_str.replace(index_match.group(0), "").strip()

        # Extract cabinet if present
        cabinet_pattern = r'in\s+(Cabinet\s+\w+)'
        cabinet_match = re.search(cabinet_pattern, comp_str, re.IGNORECASE)
        if cabinet_match:
            result["cabinet"] = cabinet_match.group(1)
            comp_str = comp_str.replace(cabinet_match.group(0), "").strip()

        # Extract specifications after colon
        if ":" in comp_str:
            parts = comp_str.split(":", 1)
            name = parts[0].strip()
            specs_str = parts[1].strip()

            result["name"] = name
            result["specifications"] = self._parse_specifications(specs_str)
        else:
            # Remove common suffixes
            comp_str = re.sub(r'\s+(module|at)\s*$', '', comp_str, flags=re.IGNORECASE)
            result["name"] = comp_str.strip()

        # Infer component type from name
        result["type"] = self._infer_component_type(result["name"])

        return result

    def _parse_specifications(self, specs_str: str) -> Dict[str, Any]:
        """Parse specification string into structured data"""
        specs = {}

        # Split by comma
        items = [item.strip() for item in specs_str.split(",")]

        for item in items:
            # Check for number patterns
            if re.match(r'^\d+\s+\w+', item):
                # "45 modules" → modules: 45
                match = re.match(r'^(\d+)\s+(\w+)', item)
                if match:
                    specs[match.group(2)] = int(match.group(1))
            else:
                # Just a name like "IM151-1", "PM", "DI40"
                # Count occurrences
                if item in specs:
                    specs[item] += 1
                else:
                    specs[item] = 1

        return specs

    def _infer_component_type(self, name: str) -> Optional[str]:
        """Infer component type from name"""
        name_upper = name.upper()

        if "HVC" in name_upper:
            return "HVC"
        elif "SLAVE" in name_upper:
            return "Slave"
        elif "CABINET" in name_upper:
            return "Cabinet"
        elif "IM151" in name_upper:
            return "IM151"
        elif re.match(r'^(PM|DI|DO|AI|AO|RTD|TC)\d*$', name_upper):
            return "Module"

        return None

    def _process_wire_connections(self, connections: List[str],
                                  pdf_filename: str) -> int:
        """
        Process wire connection list and add to database

        Connections can be in formats like:
        - "W1 connects to W2 at terminal 5"
        - "Power from HVC3 pin 1 to Slave 23 PM input"
        - "Signal wire W105 from sensor to DI module terminal 3"
        """
        count = 0

        for conn_str in connections:
            try:
                parsed = self._parse_connection_string(conn_str)

                if parsed.get("from_component") and parsed.get("to_component"):
                    # Both components identified - add connection
                    self.db.add_connection(
                        from_component=parsed["from_component"],
                        to_component=parsed["to_component"],
                        wire_label=parsed.get("wire_label"),
                        connection_type=parsed.get("connection_type"),
                        from_terminal=parsed.get("from_terminal"),
                        to_terminal=parsed.get("to_terminal"),
                        notes=parsed.get("notes")
                    )
                    count += 1
                else:
                    # Incomplete connection - just store as wire path note
                    # We'll handle this in wire_paths table later
                    pass

            except Exception as e:
                print(f"    Warning: Could not parse connection '{conn_str}': {e}")

        return count

    def _parse_connection_string(self, conn_str: str) -> Dict[str, Any]:
        """
        Parse connection string into structured data

        Patterns:
        - "W1 connects to W2" → wire_label: W1 (but no components)
        - "HVC3 to Slave 23" → from: HVC3, to: Slave 23
        - "Power from HVC3 pin 1 to Slave 23 PM input" → full detail
        """
        result = {}

        # Extract wire label (W followed by numbers)
        wire_pattern = r'\b(W\d+)\b'
        wire_match = re.search(wire_pattern, conn_str)
        if wire_match:
            result["wire_label"] = wire_match.group(1)

        # Detect connection type
        if re.search(r'\bpower\b', conn_str, re.IGNORECASE):
            result["connection_type"] = "power"
        elif re.search(r'\bsignal\b', conn_str, re.IGNORECASE):
            result["connection_type"] = "signal"
        elif re.search(r'\bground\b', conn_str, re.IGNORECASE):
            result["connection_type"] = "ground"

        # Extract terminals
        terminal_pattern = r'\b(?:pin|terminal)\s+(\d+|[A-Z]\d+)\b'
        terminals = re.findall(terminal_pattern, conn_str, re.IGNORECASE)
        if len(terminals) >= 1:
            result["from_terminal"] = terminals[0]
        if len(terminals) >= 2:
            result["to_terminal"] = terminals[1]

        # Parse "from X to Y" pattern
        from_to_pattern = r'from\s+([A-Za-z0-9\s]+?)\s+(?:pin|terminal)?\s*\d*\s+to\s+([A-Za-z0-9\s]+?)(?:\s+(?:pin|terminal|input|output))?'
        from_to_match = re.search(from_to_pattern, conn_str, re.IGNORECASE)
        if from_to_match:
            result["from_component"] = from_to_match.group(1).strip()
            result["to_component"] = from_to_match.group(2).strip()
        else:
            # Try simple "X to Y" pattern
            simple_pattern = r'([A-Za-z0-9]+)\s+to\s+([A-Za-z0-9\s]+?)(?:\s|$|,)'
            simple_match = re.search(simple_pattern, conn_str)
            if simple_match:
                result["from_component"] = simple_match.group(1).strip()
                result["to_component"] = simple_match.group(2).strip()

        # Store original string as notes if we have a connection
        if result.get("from_component") or result.get("to_component"):
            result["notes"] = conn_str

        return result

    def build_from_training_examples(self, training_file: str = "data/training_data/training_examples.jsonl"):
        """
        Build database from training examples JSONL file

        Args:
            training_file: Path to training examples JSONL file
        """
        training_path = Path(training_file)

        if not training_path.exists():
            print(f"Training file not found: {training_file}")
            return

        print(f"\nProcessing training examples from {training_file}...")

        count = 0
        with open(training_path, 'r') as f:
            for line in f:
                try:
                    example = json.loads(line)
                    self._process_training_example(example)
                    count += 1
                except Exception as e:
                    print(f"  ✗ Error processing line: {e}")

        print(f"✓ Processed {count} training examples")

    def _process_training_example(self, example: Dict[str, Any]):
        """Process a single training example"""
        # Training examples have ground_truth field
        if "ground_truth" not in example:
            return

        pdf_filename = example.get("pdf_path", "").split("/")[-1]
        page_num = example.get("page_num", 0)

        section = self._extract_section(pdf_filename, example)

        # Register page
        self.db.add_schematic_page(
            pdf_filename=pdf_filename,
            page_number=page_num,
            section=section
        )

        ground_truth = example["ground_truth"]

        # Process components
        components_added = self._process_components(
            ground_truth.get("components", []),
            pdf_filename,
            page_num,
            section
        )

        # Process wire connections
        connections_added = self._process_wire_connections(
            ground_truth.get("wire_connections", []),
            pdf_filename
        )

        self.stats["components_added"] += components_added
        self.stats["connections_added"] += connections_added

    def _extract_section(self, pdf_filename: str, data: Dict[str, Any]) -> Optional[int]:
        """Extract section number from filename or data"""
        # Try from filename (e.g., "61_1.pdf" → 61)
        match = re.match(r'^(\d+)[_\.]', pdf_filename)
        if match:
            return int(match.group(1))

        # Try from index references in data
        if "ground_truth" in data:
            for ref in data["ground_truth"].get("index_references", []):
                # =61/102.0.8 → 61
                match = re.match(r'^=(\d+)/', ref)
                if match:
                    return int(match.group(1))

        return None

    def build_all(self):
        """Build database from all available training sources"""
        print("\n" + "="*60)
        print("Building Schematic Knowledge Database")
        print("="*60)

        # Build from ground truth files (highest quality)
        self.build_from_ground_truth()

        # Build from training examples
        self.build_from_training_examples()

        # Show statistics
        self.show_statistics()

    def show_statistics(self):
        """Show database build statistics"""
        print("\n" + "="*60)
        print("Database Build Statistics")
        print("="*60)

        print(f"\nData Sources Processed: {self.stats['sources_processed']}")
        print(f"Pages Indexed: {self.stats['pages_indexed']}")
        print(f"Components Added: {self.stats['components_added']}")
        print(f"Connections Added: {self.stats['connections_added']}")

        # Get database statistics
        db_stats = self.db.get_statistics()

        print(f"\nDatabase Totals:")
        print(f"  Total Components: {db_stats['total_components']}")
        print(f"  Component Types: {db_stats['component_types']}")
        print(f"  Total Connections: {db_stats['total_connections']}")
        print(f"  Cabinets: {db_stats['cabinets']}")
        print(f"  Indexed Pages: {db_stats['indexed_pages']}")

        if db_stats['components_by_type']:
            print(f"\nComponents by Type:")
            for comp_type, count in sorted(db_stats['components_by_type'].items(),
                                          key=lambda x: x[1], reverse=True):
                print(f"  {comp_type}: {count}")

    def close(self):
        """Close database connection"""
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Test the database builder
    print("Database Builder Test\n")

    with DatabaseBuilder() as builder:
        builder.build_all()
