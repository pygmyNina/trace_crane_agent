#!/usr/bin/env python3
"""
Import Glossary Script for TRACE
Reads glossary files (Word documents with tables) and imports definitions into knowledge base.

Expected format: 2-column table
  Column 1: Code (e.g., =10, =61)
  Column 2: Definition (e.g., MV-Supply, PLC/CMS)

Usage:
  python3 import_glossary.py glossary/electrical_sections.doc
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
    print("⚠ python-docx not available. Install with: pip3 install python-docx")


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

    def _ensure_glossary_section(self):
        """Ensure glossary section exists in knowledge base"""
        if "system_groups" not in self.knowledge:
            self.knowledge["system_groups"] = {}
            print("✓ Created 'system_groups' section in knowledge base")

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

        # Look for tables in document
        if not doc.tables:
            print(f"✗ No tables found in {doc_path}")
            return False

        print(f"\n📄 Reading {doc_path}...")
        print(f"   Found {len(doc.tables)} table(s)\n")

        # Process first table
        table = doc.tables[0]
        definitions_added = 0

        self._ensure_glossary_section()

        # Skip header row, process data rows
        for i, row in enumerate(table.rows[1:], start=1):
            cells = row.cells
            if len(cells) >= 2:
                code = cells[0].text.strip()
                definition = cells[1].text.strip()

                if code and definition:
                    # Store in knowledge base
                    self.knowledge["system_groups"][code] = {
                        "code": code,
                        "definition": definition,
                        "source": os.path.basename(doc_path),
                        "added": datetime.now().isoformat()
                    }
                    definitions_added += 1
                    print(f"  ✓ {code:10} → {definition}")

        self._save_knowledge()
        print(f"\n✓ Imported {definitions_added} definitions successfully!")
        return True

    def import_from_manual_input(self):
        """Manually enter definitions one by one"""
        print("\n=== Manual Glossary Entry ===")
        print("Enter definitions in format: CODE | DEFINITION")
        print("Example: =10 | MV-Supply")
        print("Type 'done' when finished\n")

        self._ensure_glossary_section()
        definitions_added = 0

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
                self.knowledge["system_groups"][code] = {
                    "code": code,
                    "definition": definition,
                    "source": "manual_entry",
                    "added": datetime.now().isoformat()
                }
                definitions_added += 1
                print(f"  ✓ Added: {code} → {definition}")
            else:
                print("  ✗ Both code and definition required")

        if definitions_added > 0:
            self._save_knowledge()
            print(f"\n✓ Imported {definitions_added} definitions successfully!")
        else:
            print("\n  No definitions added.")

        return definitions_added > 0

    def show_all_definitions(self):
        """Display all system group definitions"""
        if "system_groups" not in self.knowledge or not self.knowledge["system_groups"]:
            print("\nNo system group definitions in knowledge base.")
            return

        print("\n=== System Groups ===\n")
        for code in sorted(self.knowledge["system_groups"].keys()):
            entry = self.knowledge["system_groups"][code]
            print(f"  {code:10} → {entry['definition']}")

        print(f"\nTotal: {len(self.knowledge['system_groups'])} definitions")


def main():
    """Main entry point"""
    importer = GlossaryImporter()

    if len(sys.argv) < 2:
        print("Usage: python3 import_glossary.py <path-to-glossary.docx>")
        print("   OR: python3 import_glossary.py --manual")
        print("   OR: python3 import_glossary.py --show")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--show":
        importer.show_all_definitions()
    elif arg == "--manual":
        importer.import_from_manual_input()
    else:
        doc_path = arg
        if not os.path.exists(doc_path):
            print(f"✗ File not found: {doc_path}")
            sys.exit(1)

        importer.import_from_docx(doc_path)


if __name__ == "__main__":
    main()
