"""
Database Schema for Crane Schematic Knowledge Base
Stores components, connections, and wire paths for searchable database
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class SchematicDatabase:
    """Main database for crane schematic components and connections"""

    def __init__(self, db_path: str = "data/copilot/schematic_knowledge.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._initialize_database()

    def _initialize_database(self):
        """Create database and tables"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = self.conn.cursor()

        # Components table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                index_reference TEXT,
                section INTEGER,
                sheet TEXT,
                column INTEGER,
                page_number INTEGER,
                cabinet TEXT,
                specifications TEXT,
                notes TEXT,
                pdf_filename TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, index_reference)
            )
        """)

        # Connections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_component_id INTEGER,
                to_component_id INTEGER,
                wire_label TEXT,
                connection_type TEXT,
                from_terminal TEXT,
                to_terminal TEXT,
                specifications TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_component_id) REFERENCES components(id),
                FOREIGN KEY (to_component_id) REFERENCES components(id)
            )
        """)

        # Wire paths table (for complete power/signal paths)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wire_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wire_label TEXT,
                path_type TEXT,
                components TEXT,
                terminals TEXT,
                page_references TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Schematic pages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schematic_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_filename TEXT,
                page_number INTEGER,
                section INTEGER,
                sheet TEXT,
                components_count INTEGER DEFAULT 0,
                indexed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                ground_truth_file TEXT,
                UNIQUE(pdf_filename, page_number)
            )
        """)

        # Training data sources table (track what data populated DB)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT,
                source_type TEXT,
                processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                components_added INTEGER DEFAULT 0,
                connections_added INTEGER DEFAULT 0
            )
        """)

        # Create indexes for faster searches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_component_name ON components(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_component_type ON components(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_component_index ON components(index_reference)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_component_cabinet ON components(cabinet)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_connection_wire ON connections(wire_label)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_page_section ON schematic_pages(section)")

        self.conn.commit()

    def add_component(self, name: str, component_type: str = None,
                     index_reference: str = None, **kwargs) -> int:
        """
        Add a component to the database

        Args:
            name: Component name (e.g., "HVC3", "Slave 23")
            component_type: Type (e.g., "HVC", "Slave", "Cabinet")
            index_reference: Location (e.g., "=61/102.0.8")
            **kwargs: Additional fields (section, sheet, cabinet, etc.)

        Returns:
            Component ID
        """
        cursor = self.conn.cursor()

        # Parse index reference if provided
        section, sheet, column = None, None, None
        if index_reference:
            section, sheet, column = self._parse_index_reference(index_reference)

        # Build insert query
        fields = {
            'name': name,
            'type': component_type,
            'index_reference': index_reference,
            'section': section or kwargs.get('section'),
            'sheet': sheet or kwargs.get('sheet'),
            'column': column or kwargs.get('column'),
            'page_number': kwargs.get('page_number'),
            'cabinet': kwargs.get('cabinet'),
            'specifications': json.dumps(kwargs.get('specifications', {})),
            'notes': kwargs.get('notes'),
            'pdf_filename': kwargs.get('pdf_filename')
        }

        # Remove None values
        fields = {k: v for k, v in fields.items() if v is not None}

        columns = ', '.join(fields.keys())
        placeholders = ', '.join(['?' for _ in fields])
        values = list(fields.values())

        try:
            cursor.execute(f"""
                INSERT INTO components ({columns})
                VALUES ({placeholders})
            """, values)
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Component already exists, return existing ID
            cursor.execute("""
                SELECT id FROM components
                WHERE name = ? AND (index_reference = ? OR index_reference IS NULL)
            """, (name, index_reference))
            row = cursor.fetchone()
            return row[0] if row else None

    def add_connection(self, from_component: str, to_component: str,
                      wire_label: str = None, connection_type: str = None,
                      **kwargs) -> int:
        """
        Add a connection between components

        Args:
            from_component: Source component name
            to_component: Destination component name
            wire_label: Wire identifier (e.g., "W1")
            connection_type: "power", "signal", "ground", etc.
            **kwargs: from_terminal, to_terminal, specifications, notes

        Returns:
            Connection ID
        """
        cursor = self.conn.cursor()

        # Get component IDs
        cursor.execute("SELECT id FROM components WHERE name = ?", (from_component,))
        from_row = cursor.fetchone()
        if not from_row:
            raise ValueError(f"Component not found: {from_component}")
        from_id = from_row[0]

        cursor.execute("SELECT id FROM components WHERE name = ?", (to_component,))
        to_row = cursor.fetchone()
        if not to_row:
            raise ValueError(f"Component not found: {to_component}")
        to_id = to_row[0]

        # Insert connection
        cursor.execute("""
            INSERT INTO connections
            (from_component_id, to_component_id, wire_label, connection_type,
             from_terminal, to_terminal, specifications, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (from_id, to_id, wire_label, connection_type,
              kwargs.get('from_terminal'), kwargs.get('to_terminal'),
              kwargs.get('specifications'), kwargs.get('notes')))

        self.conn.commit()
        return cursor.lastrowid

    def search_component(self, query: str, search_type: str = "name") -> List[Dict]:
        """
        Search for components

        Args:
            query: Search term
            search_type: "name", "type", "cabinet", "index", or "all"

        Returns:
            List of matching components
        """
        cursor = self.conn.cursor()

        if search_type == "name":
            cursor.execute("""
                SELECT * FROM components
                WHERE name LIKE ?
                ORDER BY name
            """, (f"%{query}%",))

        elif search_type == "type":
            cursor.execute("""
                SELECT * FROM components
                WHERE type LIKE ?
                ORDER BY name
            """, (f"%{query}%",))

        elif search_type == "cabinet":
            cursor.execute("""
                SELECT * FROM components
                WHERE cabinet LIKE ?
                ORDER BY name
            """, (f"%{query}%",))

        elif search_type == "index":
            cursor.execute("""
                SELECT * FROM components
                WHERE index_reference LIKE ?
                ORDER BY index_reference
            """, (f"%{query}%",))

        else:  # search all
            cursor.execute("""
                SELECT * FROM components
                WHERE name LIKE ? OR type LIKE ? OR cabinet LIKE ?
                   OR index_reference LIKE ? OR notes LIKE ?
                ORDER BY name
            """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))

        return [dict(row) for row in cursor.fetchall()]

    def get_component_connections(self, component_name: str) -> Dict[str, List[Dict]]:
        """
        Get all connections for a component

        Returns:
            Dict with 'incoming' and 'outgoing' connection lists
        """
        cursor = self.conn.cursor()

        # Get component ID
        cursor.execute("SELECT id FROM components WHERE name = ?", (component_name,))
        row = cursor.fetchone()
        if not row:
            return {"incoming": [], "outgoing": []}
        comp_id = row[0]

        # Outgoing connections
        cursor.execute("""
            SELECT c.*, comp.name as to_component_name
            FROM connections c
            JOIN components comp ON c.to_component_id = comp.id
            WHERE c.from_component_id = ?
        """, (comp_id,))
        outgoing = [dict(row) for row in cursor.fetchall()]

        # Incoming connections
        cursor.execute("""
            SELECT c.*, comp.name as from_component_name
            FROM connections c
            JOIN components comp ON c.from_component_id = comp.id
            WHERE c.to_component_id = ?
        """, (comp_id,))
        incoming = [dict(row) for row in cursor.fetchall()]

        return {
            "incoming": incoming,
            "outgoing": outgoing
        }

    def get_component_details(self, component_name: str) -> Optional[Dict]:
        """Get detailed information about a component"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM components WHERE name = ?", (component_name,))
        row = cursor.fetchone()

        if not row:
            return None

        component = dict(row)

        # Add connections
        component['connections'] = self.get_component_connections(component_name)

        # Parse specifications if JSON
        if component.get('specifications'):
            try:
                component['specifications'] = json.loads(component['specifications'])
            except:
                pass

        return component

    def get_components_by_cabinet(self, cabinet: str) -> List[Dict]:
        """Get all components in a specific cabinet"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM components
            WHERE cabinet = ?
            ORDER BY name
        """, (cabinet,))

        return [dict(row) for row in cursor.fetchall()]

    def get_components_by_type(self, component_type: str) -> List[Dict]:
        """Get all components of a specific type"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM components
            WHERE type = ?
            ORDER BY name
        """, (component_type,))

        return [dict(row) for row in cursor.fetchall()]

    def add_schematic_page(self, pdf_filename: str, page_number: int,
                          section: int = None, sheet: str = None,
                          ground_truth_file: str = None) -> int:
        """Register a schematic page"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO schematic_pages
                (pdf_filename, page_number, section, sheet, ground_truth_file)
                VALUES (?, ?, ?, ?, ?)
            """, (pdf_filename, page_number, section, sheet, ground_truth_file))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Page already exists
            cursor.execute("""
                SELECT id FROM schematic_pages
                WHERE pdf_filename = ? AND page_number = ?
            """, (pdf_filename, page_number))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        cursor = self.conn.cursor()

        stats = {}

        # Component counts
        cursor.execute("SELECT COUNT(*) FROM components")
        stats['total_components'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT type) FROM components WHERE type IS NOT NULL")
        stats['component_types'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT cabinet) FROM components WHERE cabinet IS NOT NULL")
        stats['cabinets'] = cursor.fetchone()[0]

        # Connection counts
        cursor.execute("SELECT COUNT(*) FROM connections")
        stats['total_connections'] = cursor.fetchone()[0]

        # Page counts
        cursor.execute("SELECT COUNT(*) FROM schematic_pages")
        stats['indexed_pages'] = cursor.fetchone()[0]

        # Component type breakdown
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM components
            WHERE type IS NOT NULL
            GROUP BY type
            ORDER BY count DESC
        """)
        stats['components_by_type'] = {row[0]: row[1] for row in cursor.fetchall()}

        return stats

    def _parse_index_reference(self, index_ref: str) -> tuple:
        """
        Parse index reference like =61/102.0.8 into (section, sheet, column)

        Returns:
            (section, sheet, column) tuple
        """
        try:
            if not index_ref or not index_ref.startswith('='):
                return None, None, None

            # Remove = sign
            ref = index_ref[1:]

            # Split by /
            parts = ref.split('/')
            if len(parts) != 2:
                return None, None, None

            section = int(parts[0])

            # Handle sheet.column format
            sheet_parts = parts[1].split('.')
            if len(sheet_parts) == 2:
                # Shorthand: =61/102.8 means =61/102.0.8
                sheet = f"{sheet_parts[0]}.0"
                column = int(sheet_parts[1])
            elif len(sheet_parts) == 3:
                # Full format: =61/102.0.8
                sheet = f"{sheet_parts[0]}.{sheet_parts[1]}"
                column = int(sheet_parts[2])
            else:
                return section, None, None

            return section, sheet, column

        except:
            return None, None, None

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Test the database
    print("Testing Schematic Database\n")

    with SchematicDatabase("data/copilot/test_schematic.db") as db:
        # Add some test components
        print("Adding test components...")
        hvc3_id = db.add_component(
            "HVC3",
            component_type="HVC",
            index_reference="=10/103.0.7",
            cabinet="Main Panel"
        )

        slave23_id = db.add_component(
            "Slave 23",
            component_type="Slave",
            index_reference="=61/102.0.8",
            cabinet="Cabinet E11",
            specifications={"modules": 45, "IM151": 1, "PM": 1, "DI": 40, "RTD": 3}
        )

        # Add connection
        print("Adding connection...")
        db.add_connection(
            "HVC3",
            "Slave 23",
            wire_label="W1",
            connection_type="power",
            from_terminal="1",
            to_terminal="PM input"
        )

        # Search
        print("\nSearching for 'Slave'...")
        results = db.search_component("Slave")
        for comp in results:
            print(f"  - {comp['name']} at {comp['index_reference']}")

        # Get details
        print("\nGetting Slave 23 details...")
        details = db.get_component_details("Slave 23")
        print(f"  Location: {details['index_reference']}")
        print(f"  Cabinet: {details['cabinet']}")
        print(f"  Connections: {len(details['connections']['incoming'])} in, {len(details['connections']['outgoing'])} out")

        # Statistics
        print("\nDatabase statistics:")
        stats = db.get_statistics()
        for key, value in stats.items():
            if key != 'components_by_type':
                print(f"  {key}: {value}")

    print("\n✓ Database test complete!")
