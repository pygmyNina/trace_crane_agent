#!/usr/bin/env python3
"""
Import Glossary Script for TRACE
Reads glossary files and imports definitions into knowledge base.

Supports: Word documents (.docx), Excel files (.xls, .xlsx)

Handles multiple glossary types:
  - System Groups: =10, =61, etc. (system categories, not locations)
  - Terminals: -X10, -X11, etc. (terminal types and wire types)
  - Locations: abbreviations for physical crane locations

Expected format: 2-column tables
  System Groups:
    Column 1: Code (e.g., =10, =61)
    Column 2: Definition (e.g., MV-Supply, PLC/CMS)

  Terminals:
    Column 1: Terminal Code (e.g., -X10, -X11)
    Column 2: Description (e.g., Power terminal)

  Locations:
    Column 1: Abbreviation (e.g., E11, MCC, CB)
    Column 2: Description (e.g., Electrical Cabinet 11)

Usage:
  python3 import_glossary.py glossary/electrical_sections.docx
  python3 import_glossary.py glossary/locations.xls
"""

import json
import sys
import os
from datetime import datetime

# Try importing Word document reader
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Try importing Excel readers
try:
    import xlrd  # For .xls (old Excel format)
    XLRD_AVAILABLE = True
except ImportError:
    XLRD_AVAILABLE = False

try:
    import openpyxl  # For .xlsx (new Excel format)
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class GlossaryImporter:
    """Imports glossary definitions into TRACE knowledge base"""

    def __init__(self, knowledge_file="trace_knowledge.json"):
        self.knowledge_file = knowledge_file
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self):
        """Load existing knowledge base"""
        if os.path.exists(self.knowledge_file):
            with open(self.knowledge_file, 'r') as f:
                return json.load(f)
        else:
            print(f"✗ Knowledge file not found: {self.knowledge_file}")
            sys.exit(1)

    def _save_knowledge(self):
        """Save updated knowledge base"""
        with open(self.knowledge_file, 'w') as f:
            json.dump(self.knowledge, f, indent=2)
        print(f"✓ Knowledge saved to {self.knowledge_file}")

    def _ensure_glossary_sections(self):
        """Ensure glossary sections exist in knowledge base"""
        created = []
        if "system_groups" not in self.knowledge:
            self.knowledge["system_groups"] = {}
            created.append("system_groups")
        if "terminals" not in self.knowledge:
            self.knowledge["terminals"] = {}
            created.append("terminals")
        if "locations" not in self.knowledge:
            self.knowledge["locations"] = {}
            created.append("locations")
        if created:
            print(f"✓ Created sections: {', '.join(created)}")

    def _add_definition(self, code, definition, source):
        """Add a definition to the appropriate section based on code format"""
        if code.startswith('='):
            # System Group (e.g., =10, =61)
            self.knowledge["system_groups"][code] = {
                "code": code,
                "definition": definition,
                "source": source,
                "added": datetime.now().isoformat()
            }
            return "system_group"
        elif code.startswith('-'):
            # Terminal (e.g., -X10, -X11)
            self.knowledge["terminals"][code] = {
                "code": code,
                "terminal_type": definition,
                "source": source,
                "added": datetime.now().isoformat()
            }
            return "terminal"
        else:
            # Location abbreviation (e.g., E11, MCC, CB)
            self.knowledge["locations"][code] = {
                "abbreviation": code,
                "description": definition,
                "source": source,
                "added": datetime.now().isoformat()
            }
            return "location"

    def import_from_docx(self, doc_path):
        """Import glossary from Word document (.docx format)"""
        if not DOCX_AVAILABLE:
            print("✗ python-docx library required for .docx files")
            print("  Install with: pip3 install python-docx")
            return False

        try:
            doc = Document(doc_path)
        except Exception as e:
            print(f"✗ Could not open {doc_path}")
            print(f"  Error: {e}")
            print("\n💡 Note: This script works with .docx files (newer format).")
            print("   If you have a .doc file (old format), please:")
            print("   1. Open it in Word")
            print("   2. Save As -> .docx format")
            print("   3. Run this script again")
            return False

        print(f"\n📄 Reading {doc_path}...")

        self._ensure_glossary_sections()

        system_groups_added = 0
        terminals_added = 0
        locations_added = 0

        # Check if document has tables
        if doc.tables:
            print(f"   Found {len(doc.tables)} table(s)\n")
            # Process ALL tables in the document
            for table_num, table in enumerate(doc.tables, start=1):
                print(f"\n--- Processing Table {table_num} ---")

                # Skip header row, process data rows
                for i, row in enumerate(table.rows[1:], start=1):
                    cells = row.cells
                    if len(cells) >= 2:
                        code = cells[0].text.strip()
                        definition = cells[1].text.strip()

                        if code and definition:
                            added = self._add_definition(code, definition, doc_path)
                            if added == "system_group":
                                system_groups_added += 1
                                print(f"  ✓ System Group: {code:10} → {definition}")
                            elif added == "terminal":
                                terminals_added += 1
                                print(f"  ✓ Terminal:     {code:10} → {definition}")
                            elif added == "location":
                                locations_added += 1
                                print(f"  ✓ Location:     {code:10} → {definition}")
        else:
            # No tables found - try reading as plain text with spacing
            print("   No tables found - reading as plain text\n")

            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue

                # Skip header lines
                if text.lower().startswith('system') or text.lower().startswith('terminal'):
                    print(f"\n--- {text} ---")
                    continue

                # Try to parse line with multiple spaces/tabs between code and definition
                # Split on 2+ spaces or tabs
                import re
                parts = re.split(r'\s{2,}|\t+', text, maxsplit=1)

                if len(parts) >= 2:
                    code = parts[0].strip()
                    definition = parts[1].strip()

                    if code and definition:
                        added = self._add_definition(code, definition, doc_path)
                        if added == "system_group":
                            system_groups_added += 1
                            print(f"  ✓ System Group: {code:10} → {definition}")
                        elif added == "terminal":
                            terminals_added += 1
                            print(f"  ✓ Terminal:     {code:10} → {definition}")
                        elif added == "location":
                            locations_added += 1
                            print(f"  ✓ Location:     {code:10} → {definition}")
                elif text.startswith('=') or text.startswith('-'):
                    # Single word entries or malformed - show warning
                    print(f"  ⚠ Could not parse: {text[:50]}")

        self._save_knowledge()
        print(f"\n{'='*60}")
        print(f"✓ Import Complete!")
        print(f"  System Groups: {system_groups_added}")
        print(f"  Terminals:     {terminals_added}")
        print(f"  Locations:     {locations_added}")
        print(f"  Total:         {system_groups_added + terminals_added + locations_added}")
        print(f"{'='*60}\n")
        return True

    def import_from_excel(self, excel_path):
        """Import glossary from Excel file (.xls or .xlsx format)"""
        file_ext = os.path.splitext(excel_path)[1].lower()

        if file_ext == '.xlsx':
            if not OPENPYXL_AVAILABLE:
                print("✗ openpyxl library required for .xlsx files")
                print("  Install with: pip3 install openpyxl")
                return False
            return self._import_from_xlsx(excel_path)
        elif file_ext == '.xls':
            if not XLRD_AVAILABLE:
                print("✗ xlrd library required for .xls files")
                print("  Install with: pip3 install xlrd")
                return False
            return self._import_from_xls(excel_path)
        else:
            print(f"✗ Unsupported file type: {file_ext}")
            return False

    def _import_from_xlsx(self, excel_path):
        """Import from .xlsx (newer Excel format)"""
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            sheet = wb.active
        except Exception as e:
            print(f"✗ Could not open {excel_path}")
            print(f"  Error: {e}")
            return False

        print(f"\n📊 Reading {excel_path}...")
        print(f"   Sheet: {sheet.title}\n")

        self._ensure_glossary_sections()

        system_groups_added = 0
        terminals_added = 0
        locations_added = 0

        # Skip header row (row 1), process data rows
        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if len(row) >= 2 and row[0] and row[1]:
                code = str(row[0]).strip()
                definition = str(row[1]).strip()

                if code and definition:
                    added = self._add_definition(code, definition, os.path.basename(excel_path))
                    if added == "system_group":
                        system_groups_added += 1
                        print(f"  ✓ System Group: {code:10} → {definition}")
                    elif added == "terminal":
                        terminals_added += 1
                        print(f"  ✓ Terminal:     {code:10} → {definition}")
                    elif added == "location":
                        locations_added += 1
                        print(f"  ✓ Location:     {code:10} → {definition}")

        wb.close()
        self._save_knowledge()
        print(f"\n{'='*60}")
        print(f"✓ Import Complete!")
        print(f"  System Groups: {system_groups_added}")
        print(f"  Terminals:     {terminals_added}")
        print(f"  Locations:     {locations_added}")
        print(f"  Total:         {system_groups_added + terminals_added + locations_added}")
        print(f"{'='*60}\n")
        return True

    def _import_from_xls(self, excel_path):
        """Import from .xls (older Excel format)"""
        try:
            wb = xlrd.open_workbook(excel_path)
            sheet = wb.sheet_by_index(0)
        except Exception as e:
            print(f"✗ Could not open {excel_path}")
            print(f"  Error: {e}")
            return False

        print(f"\n📊 Reading {excel_path}...")
        print(f"   Sheet: {sheet.name}\n")

        self._ensure_glossary_sections()

        system_groups_added = 0
        terminals_added = 0
        locations_added = 0

        # Skip header row (row 0), process data rows
        for row_num in range(1, sheet.nrows):
            if sheet.ncols >= 2:
                code = str(sheet.cell_value(row_num, 0)).strip()
                definition = str(sheet.cell_value(row_num, 1)).strip()

                if code and definition:
                    added = self._add_definition(code, definition, os.path.basename(excel_path))
                    if added == "system_group":
                        system_groups_added += 1
                        print(f"  ✓ System Group: {code:10} → {definition}")
                    elif added == "terminal":
                        terminals_added += 1
                        print(f"  ✓ Terminal:     {code:10} → {definition}")
                    elif added == "location":
                        locations_added += 1
                        print(f"  ✓ Location:     {code:10} → {definition}")

        self._save_knowledge()
        print(f"\n{'='*60}")
        print(f"✓ Import Complete!")
        print(f"  System Groups: {system_groups_added}")
        print(f"  Terminals:     {terminals_added}")
        print(f"  Locations:     {locations_added}")
        print(f"  Total:         {system_groups_added + terminals_added + locations_added}")
        print(f"{'='*60}\n")
        return True

    def import_from_manual_input(self):
        """Manually enter definitions one by one"""
        print("\n=== Manual Glossary Entry ===")
        print("Enter definitions in format: CODE | DEFINITION")
        print("Examples:")
        print("  =10 | MV-Supply        (system group)")
        print("  -X10 | Power terminal  (terminal)")
        print("Type 'done' when finished\n")

        self._ensure_glossary_sections()
        system_groups_added = 0
        terminals_added = 0

        while True:
            entry = input("Enter definition (or 'done'): ").strip()

            if entry.lower() == 'done':
                break

            if '|' not in entry:
                print("  ✗ Format should be: CODE | DEFINITION")
                continue

            parts = entry.split('|', 1)
            code = parts[0].strip()
            definition = parts[1].strip()

            if code and definition:
                if code.startswith('='):
                    # System Group
                    self.knowledge["system_groups"][code] = {
                        "code": code,
                        "definition": definition,
                        "source": "manual_entry",
                        "added": datetime.now().isoformat()
                    }
                    system_groups_added += 1
                    print(f"  ✓ Added System Group: {code} → {definition}")
                elif code.startswith('-'):
                    # Terminal
                    self.knowledge["terminals"][code] = {
                        "code": code,
                        "terminal_type": definition,
                        "source": "manual_entry",
                        "added": datetime.now().isoformat()
                    }
                    terminals_added += 1
                    print(f"  ✓ Added Terminal: {code} → {definition}")
                else:
                    print(f"  ✗ Unknown format: {code} (expected = or - prefix)")
            else:
                print("  ✗ Both code and definition required")

        total_added = system_groups_added + terminals_added
        if total_added > 0:
            self._save_knowledge()
            print(f"\n✓ Imported {total_added} definitions successfully!")
            print(f"  System Groups: {system_groups_added}")
            print(f"  Terminals:     {terminals_added}")
        else:
            print("\n  No definitions added.")

        return total_added > 0

    def show_all_definitions(self):
        """Display all glossary definitions"""
        has_data = False

        # Show System Groups
        if "system_groups" in self.knowledge and self.knowledge["system_groups"]:
            print("\n=== System Groups (System Categories) ===\n")
            for code in sorted(self.knowledge["system_groups"].keys()):
                entry = self.knowledge["system_groups"][code]
                print(f"  {code:10} → {entry['definition']}")
            print(f"\n  Total: {len(self.knowledge['system_groups'])} system groups")
            has_data = True

        # Show Terminals
        if "terminals" in self.knowledge and self.knowledge["terminals"]:
            print("\n=== Terminals (Terminal Types) ===\n")
            for code in sorted(self.knowledge["terminals"].keys()):
                entry = self.knowledge["terminals"][code]
                print(f"  {code:10} → {entry['terminal_type']}")
            print(f"\n  Total: {len(self.knowledge['terminals'])} terminals")
            has_data = True

        # Show Locations
        if "locations" in self.knowledge and self.knowledge["locations"]:
            print("\n=== Locations (Physical Crane Locations) ===\n")
            for code in sorted(self.knowledge["locations"].keys()):
                entry = self.knowledge["locations"][code]
                print(f"  {code:10} → {entry['description']}")
            print(f"\n  Total: {len(self.knowledge['locations'])} locations")
            has_data = True

        if not has_data:
            print("\nNo glossary definitions in knowledge base.")
            print("Use: python3 import_glossary.py <file> to import\n")


def main():
    """Main entry point"""
    importer = GlossaryImporter()

    if len(sys.argv) < 2:
        print("Usage: python3 import_glossary.py <path-to-file>")
        print("   OR: python3 import_glossary.py --manual")
        print("   OR: python3 import_glossary.py --show")
        print("\nSupported formats: .docx, .xls, .xlsx")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--show":
        importer.show_all_definitions()
    elif arg == "--manual":
        importer.import_from_manual_input()
    else:
        file_path = arg
        if not os.path.exists(file_path):
            print(f"✗ File not found: {file_path}")
            sys.exit(1)

        # Detect file type and route to appropriate import method
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.docx':
            importer.import_from_docx(file_path)
        elif file_ext in ['.xls', '.xlsx']:
            importer.import_from_excel(file_path)
        else:
            print(f"✗ Unsupported file format: {file_ext}")
            print("  Supported formats: .docx, .xls, .xlsx")
            sys.exit(1)


if __name__ == "__main__":
    main()
