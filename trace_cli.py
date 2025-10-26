#!/usr/bin/env python3
"""
TRACE - Crane Schematic Assistant and Copilot (Vision-Enabled)
Command-line interface with Vision API integration for image-based schematics
"""

import sys
import os

# Load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from trace.knowledge_base import KnowledgeBase
from trace.training_interface import TrainingInterface
from trace.section_manager import SectionManager
from trace.vision_analyzer import VisionAnalyzer
from trace.pdf_image_converter import PDFImageConverter


class TRACECLI:
    """Main CLI interface for TRACE with Vision capabilities"""

    def __init__(self):
        self.kb = KnowledgeBase()
        self.trainer = TrainingInterface(self.kb)
        self.section_mgr = SectionManager()
        self.vision = VisionAnalyzer()
        self.converter = PDFImageConverter()
        self.running = True

    def print_header(self):
        """Print TRACE header"""
        print("\n" + "="*60)
        print("  TRACE - Crane Schematic Assistant & Copilot")
        print("  Version 0.2.0 - Vision Enabled")
        print("="*60 + "\n")

        # Check Vision API status
        if self.vision.check_api_available():
            print("✓ Vision API: Ready")
        else:
            print("⚠ Vision API: Not configured (set ANTHROPIC_API_KEY)")

        print()

    def print_help(self):
        """Print available commands"""
        print("\nAvailable Commands:")
        print("\n  === Knowledge Base ===")
        print("  train          - Enter training mode to teach TRACE")
        print("  query <text>   - Search knowledge base and schematic index")
        print("  summary        - Display knowledge base summary")
        print("  export         - Export knowledge to file")
        print("\n  === Schematic Management ===")
        print("  load section <section> <pdf> [--index]")
        print("                 - Load PDF into section (electrical, hydraulic, etc.)")
        print("  index <section> <pdf>  - Index PDF pages with Vision API")
        print("  sections       - List all sections and PDFs")
        print("  section <name> - Show section summary")
        print("\n  === Sheet Queries ===")
        print("  sheets <code>  - Find all sheets for system (=10) or location (+E3)")
        print("  sheet <number> - Find specific sheet by number (e.g., 102)")
        print("  systems        - List all system groups with sheet counts")
        print("\n  === Vision Analysis ===")
        print("  ask <question> - Ask question about schematics (uses Vision API)")
        print("  analyze <section> <pdf> <page>  - Deep analyze specific page")
        print("  trace <from> [to <to>]  - Trace connection between components")
        print("\n  === Legacy ===")
        print("  show slaves    - Show all known slaves")
        print("  show slave <N> - Show details for specific slave")
        print("  show connections - Show all connections")
        print("\n  === System ===")
        print("  cache stats    - Show image cache statistics")
        print("  cache clear    - Clear image cache")
        print("  help           - Show this help message")
        print("  quit/exit      - Exit TRACE")
        print()

    def training_mode(self):
        """Enter interactive training mode"""
        print("\n=== Training Mode ===")
        print("Tell me about crane schematics. I'll learn from your input.")
        print("Type 'done' to exit training mode.\n")

        while True:
            try:
                user_input = input("Training> ").strip()

                if user_input.lower() in ['done', 'exit', 'quit']:
                    self.trainer.end_session()
                    print("✓ Training session saved\n")
                    break

                if not user_input:
                    continue

                response = self.trainer.process_training_input(user_input)

                if response["understood"]:
                    for item in response["understood"]:
                        print(f"  ✓ {item}")

                if response["message"]:
                    print(f"\n{response['message']}\n")

                if response["needs_clarification"]:
                    for item in response["needs_clarification"]:
                        print(f"  ? {item}")

            except KeyboardInterrupt:
                print("\n\nExiting training mode...")
                self.trainer.end_session()
                break
            except EOFError:
                break

    def query_knowledge(self, query: str):
        """Query both knowledge base and schematic index"""
        print(f"\n🔍 Searching for '{query}'...")
        print("="*60)

        # Search knowledge base
        kb_results = self.kb.search(query)

        if kb_results:
            print("\n📚 Knowledge Base Results:")
            for result in kb_results:
                result_type = result["type"]
                data = result["data"]

                if result_type == "slave":
                    print(f"\n  [Slave {data['id']}]")
                    print(f"    Cabinet: {data.get('cabinet', 'N/A')}")
                    print(f"    Modules: {data.get('module_count', 0)}")

                elif result_type == "connection":
                    print(f"\n  [Connection]")
                    print(f"    {data['from']} → {data['to']}")

                elif result_type == "learning":
                    print(f"\n  [Learning: {data.get('topic', 'N/A')}]")
                    print(f"    {data.get('content', '')[:80]}...")

        # Search schematic index
        index_results = self.section_mgr.search_registry(query)

        if index_results:
            print(f"\n📄 Schematic Index Results ({len(index_results)} pages):")
            for result in index_results[:10]:  # Limit to 10 results
                print(f"\n  [{result['section'].upper()}] {result['pdf']}, Page {result['page']}")
                print(f"    {result['summary']}")
                if result['matches']:
                    for match in result['matches'][:3]:
                        print(f"    • {match}")

            if len(index_results) > 10:
                print(f"\n  ... and {len(index_results) - 10} more results")

        if not kb_results and not index_results:
            print("\n  No results found.")

        print()

    def load_section_pdf(self, section: str, pdf_path: str, auto_index: bool = False):
        """Load PDF into a section"""
        print(f"\n📄 Loading {pdf_path} into section '{section}'...")

        result = self.section_mgr.load_pdf(section, pdf_path, auto_index)

        if result["success"]:
            print(f"✓ Loaded: {result['pdf_name']}")
            print(f"  Section: {result['section']}")
            print(f"  Pages: {result['pages']}")

            if auto_index and result.get("indexed"):
                idx_result = result["index_result"]
                print(f"  Indexed: {idx_result.get('pages_indexed', 0)}/{idx_result.get('total_pages', 0)} pages")
            elif auto_index:
                print("  ⚠ Auto-indexing failed (is Vision API configured?)")
        else:
            print(f"✗ Error: {result.get('error', 'Unknown error')}")

        print()

    def index_pdf(self, section: str, pdf_name: str):
        """Index a PDF with Vision API"""
        print(f"\n🔍 Indexing {section}/{pdf_name}...")

        result = self.section_mgr.index_pdf(section, pdf_name)

        if result["success"]:
            print(f"\n✓ Indexed: {result['pages_indexed']}/{result['total_pages']} pages")
            if result.get('errors'):
                print(f"⚠ Errors: {len(result['errors'])}")
                for error in result['errors'][:5]:
                    print(f"  • {error}")
        else:
            print(f"✗ Error: {result.get('error', 'Unknown error')}")

        print()

    def list_sections(self):
        """List all sections and their PDFs"""
        sections = self.section_mgr.list_sections()

        print("\n=== Schematic Sections ===\n")

        for section, pdfs in sections.items():
            if pdfs:
                print(f"📁 {section.upper()}")
                for pdf in pdfs:
                    print(f"   • {pdf}")
            else:
                print(f"📁 {section.upper()} (empty)")

        print()

    def show_section_summary(self, section: str):
        """Show summary for a section"""
        summary = self.section_mgr.get_section_summary(section)

        if "error" in summary:
            print(f"\n✗ {summary['error']}\n")
            return

        print(f"\n=== Section: {section.upper()} ===\n")
        print(f"PDFs: {summary['pdf_count']}")
        print(f"Total Pages: {summary['total_pages']}")
        print(f"Indexed PDFs: {summary['indexed_pdfs']}/{summary['pdf_count']}")

        if summary['pdfs']:
            print("\nPDFs in this section:")
            for pdf in summary['pdfs']:
                status = "✓ Indexed" if pdf['indexed'] else "⚬ Not indexed"
                print(f"  • {pdf['name']} ({pdf['pages']} pages) [{status}]")

        print()

    def ask_question(self, question: str):
        """Ask a question using Vision API"""
        if not self.vision.check_api_available():
            print("\n✗ Vision API not configured. Set ANTHROPIC_API_KEY environment variable.\n")
            return

        print(f"\n🤔 Question: {question}")
        print("🔍 Searching for relevant schematics...")

        # First, try to find relevant pages in index
        # Extract potential search terms from question
        search_terms = []

        # Look for reference patterns
        import re
        refs = re.findall(r'=\d+/[\d.]+', question)
        search_terms.extend(refs)

        # Look for component keywords
        keywords = ['slave', 'breaker', 'transformer', 'motor', 'cabinet', 'terminal']
        words = question.lower().split()
        for keyword in keywords:
            if keyword in words:
                idx = words.index(keyword)
                if idx + 1 < len(words):
                    search_terms.append(f"{keyword} {words[idx + 1]}")

        # Search index
        relevant_pages = []
        for term in search_terms:
            results = self.section_mgr.search_registry(term)
            relevant_pages.extend(results[:3])  # Top 3 results per term

        if not relevant_pages and search_terms:
            print(f"⚠ No indexed pages found for: {', '.join(search_terms)}")
            print("  Try indexing relevant PDFs first with: index <section> <pdf>")
            print()
            return

        # If we found relevant pages, analyze them
        if relevant_pages:
            print(f"📄 Found {len(relevant_pages)} relevant page(s)")

            # Convert pages to images (limit to 3 pages)
            image_paths = []
            for page_info in relevant_pages[:3]:
                section = page_info['section']
                pdf = page_info['pdf']
                page = page_info['page']

                pdf_path = self.section_mgr.registry["sections"][section][pdf]["path"]
                img_path = self.converter.convert_page(pdf_path, page)
                if img_path:
                    image_paths.append(img_path)
                    print(f"  • {section}/{pdf}, page {page}")

            if image_paths:
                print("\n💭 Analyzing with Vision AI...")
                answer = self.vision.ask_question(image_paths, question)

                if answer:
                    print("\n" + "="*60)
                    print("📖 Answer:")
                    print("="*60)
                    print(answer)
                    print("="*60 + "\n")
                else:
                    print("\n✗ Failed to get answer from Vision API\n")
            else:
                print("\n✗ Failed to convert pages to images\n")
        else:
            print("\n⚠ No relevant pages found in index.")
            print("  You can still ask questions if you know the section and page.")
            print("  Try: analyze <section> <pdf> <page>")
            print()

    def analyze_page(self, section: str, pdf_name: str, page_num: int):
        """Deep analyze a specific page"""
        if not self.vision.check_api_available():
            print("\n✗ Vision API not configured.\n")
            return

        # Get PDF path
        try:
            pdf_path = self.section_mgr.registry["sections"][section][pdf_name]["path"]
        except KeyError:
            print(f"\n✗ PDF not found: {section}/{pdf_name}\n")
            return

        print(f"\n🔍 Analyzing {section}/{pdf_name}, page {page_num}...")

        # Convert to image
        img_path = self.converter.convert_page(pdf_path, page_num)
        if not img_path:
            print("✗ Failed to convert page to image\n")
            return

        # Get indexed data if available
        page_data = self.section_mgr.get_page_data(section, pdf_name, page_num)

        if page_data:
            print("\n📊 Indexed Data:")
            print(f"  Summary: {page_data.get('summary', 'N/A')}")
            print(f"  References: {len(page_data.get('references', []))}")
            print(f"  Components: {len(page_data.get('components', []))}")

            if page_data.get('references'):
                print(f"  Sample refs: {', '.join(page_data['references'][:5])}")

        # Ask for detailed analysis
        question = "Provide a detailed analysis of this schematic page, including all components, references, connections, and any notable features."

        print("\n💭 Requesting detailed Vision analysis...")
        answer = self.vision.ask_question([img_path], question)

        if answer:
            print("\n" + "="*60)
            print("📖 Detailed Analysis:")
            print("="*60)
            print(answer)
            print("="*60 + "\n")
        else:
            print("\n✗ Failed to analyze page\n")

    def trace_connection(self, from_comp: str, to_comp: str = None):
        """Trace a connection between components"""
        if not self.vision.check_api_available():
            print("\n✗ Vision API not configured.\n")
            return

        # Search for component in index
        results = self.section_mgr.search_registry(from_comp)

        if not results:
            print(f"\n⚠ Component '{from_comp}' not found in index.")
            print("  Try indexing the relevant schematic first.\n")
            return

        print(f"\n🔍 Tracing connection from '{from_comp}'" +
              (f" to '{to_comp}'" if to_comp else "") + "...")

        # Get images for relevant pages
        image_paths = []
        for page_info in results[:3]:
            section = page_info['section']
            pdf = page_info['pdf']
            page = page_info['page']

            pdf_path = self.section_mgr.registry["sections"][section][pdf]["path"]
            img_path = self.converter.convert_page(pdf_path, page)
            if img_path:
                image_paths.append(img_path)
                print(f"  • Found on {section}/{pdf}, page {page}")

        if image_paths:
            print("\n💭 Analyzing connections with Vision AI...")
            answer = self.vision.analyze_connection(image_paths, from_comp, to_comp)

            if answer:
                print("\n" + "="*60)
                print("🔌 Connection Trace:")
                print("="*60)
                print(answer)
                print("="*60 + "\n")
            else:
                print("\n✗ Failed to trace connection\n")
        else:
            print("\n✗ Failed to load schematic images\n")

    def show_cache_stats(self):
        """Show image cache statistics"""
        file_count, size_mb = self.converter.get_cache_size()
        print(f"\n=== Image Cache ===")
        print(f"Files: {file_count}")
        print(f"Size: {size_mb:.2f} MB")
        print(f"Location: {self.converter.cache_dir}\n")

    def clear_cache(self):
        """Clear image cache"""
        self.converter.clear_cache()
        print("\n✓ Image cache cleared\n")

    def query_sheets_by_system(self, system_code: str):
        """Query all sheets for a specific system group (e.g., =10)"""
        print(f"\n🔍 Searching sheets for system: {system_code}")
        print("="*60)

        # Look up system name from glossary
        system_name = "Unknown"
        if "system_groups" in self.kb.knowledge and system_code in self.kb.knowledge["system_groups"]:
            system_name = self.kb.knowledge["system_groups"][system_code]["definition"]

        print(f"\nSystem Group: {system_code} ({system_name})")
        print("="*60 + "\n")

        sheets_found = []

        # Search through indexed pages
        for section, pdfs in self.section_mgr.registry["sections"].items():
            for pdf_name, pdf_info in pdfs.items():
                if not pdf_info.get("indexed"):
                    continue

                for page_num, page_data in pdf_info.get("pages", {}).items():
                    # Check if this page belongs to the system group
                    if page_data.get("system_group") == system_code:
                        sheets_found.append({
                            "section": section,
                            "pdf": pdf_name,
                            "page": int(page_num),
                            "sheet_number": page_data.get("sheet_number", "unknown"),
                            "location": page_data.get("location", ""),
                            "summary": page_data.get("summary", "")
                        })

        if sheets_found:
            # Sort by sheet number
            sheets_found.sort(key=lambda x: x["sheet_number"])

            for sheet in sheets_found:
                print(f"Sheet {sheet['sheet_number']}")
                if sheet['location']:
                    # Look up location name
                    loc_name = sheet['location']
                    if "locations" in self.kb.knowledge and sheet['location'] in self.kb.knowledge["locations"]:
                        loc_name = self.kb.knowledge["locations"][sheet['location']]["description"]
                    print(f"  Location: {sheet['location']} ({loc_name})")
                print(f"  File: {sheet['section']}/{sheet['pdf']}, Page {sheet['page']}")
                if sheet['summary']:
                    print(f"  Summary: {sheet['summary']}")
                print()

            print(f"Total: {len(sheets_found)} sheet(s) found for {system_code}\n")
        else:
            print(f"  No sheets found for system {system_code}")
            print(f"  (Make sure PDFs are indexed with Vision API)\n")

    def query_sheets_by_location(self, location_code: str):
        """Query all sheets for a specific location (e.g., +E3)"""
        print(f"\n🔍 Searching sheets for location: {location_code}")
        print("="*60)

        # Look up location name from glossary
        location_name = "Unknown"
        if "locations" in self.kb.knowledge and location_code in self.kb.knowledge["locations"]:
            location_name = self.kb.knowledge["locations"][location_code]["description"]

        print(f"\nLocation: {location_code} ({location_name})")
        print("="*60 + "\n")

        sheets_found = []

        # Search through indexed pages
        for section, pdfs in self.section_mgr.registry["sections"].items():
            for pdf_name, pdf_info in pdfs.items():
                if not pdf_info.get("indexed"):
                    continue

                for page_num, page_data in pdf_info.get("pages", {}).items():
                    # Check if this page is at this location
                    if page_data.get("location") == location_code:
                        sheets_found.append({
                            "section": section,
                            "pdf": pdf_name,
                            "page": int(page_num),
                            "sheet_number": page_data.get("sheet_number", "unknown"),
                            "system_group": page_data.get("system_group", ""),
                            "summary": page_data.get("summary", "")
                        })

        if sheets_found:
            # Sort by sheet number
            sheets_found.sort(key=lambda x: x["sheet_number"])

            for sheet in sheets_found:
                print(f"Sheet {sheet['sheet_number']}")
                if sheet['system_group']:
                    # Look up system name
                    sys_name = sheet['system_group']
                    if "system_groups" in self.kb.knowledge and sheet['system_group'] in self.kb.knowledge["system_groups"]:
                        sys_name = self.kb.knowledge["system_groups"][sheet['system_group']]["definition"]
                    print(f"  System: {sheet['system_group']} ({sys_name})")
                print(f"  File: {sheet['section']}/{sheet['pdf']}, Page {sheet['page']}")
                if sheet['summary']:
                    print(f"  Summary: {sheet['summary']}")
                print()

            print(f"Total: {len(sheets_found)} sheet(s) found at {location_code}\n")
        else:
            print(f"  No sheets found at location {location_code}")
            print(f"  (Make sure PDFs are indexed with Vision API)\n")

    def find_sheet(self, sheet_number: str):
        """Find a specific sheet by number"""
        print(f"\n🔍 Searching for sheet: {sheet_number}")
        print("="*60 + "\n")

        # Search through indexed pages
        for section, pdfs in self.section_mgr.registry["sections"].items():
            for pdf_name, pdf_info in pdfs.items():
                if not pdf_info.get("indexed"):
                    continue

                for page_num, page_data in pdf_info.get("pages", {}).items():
                    if page_data.get("sheet_number") == sheet_number:
                        print(f"Sheet {sheet_number} found!")
                        print(f"  File: {section}/{pdf_name}, Page {page_num}")

                        if page_data.get("system_group"):
                            sys_name = page_data["system_group"]
                            if "system_groups" in self.kb.knowledge and page_data["system_group"] in self.kb.knowledge["system_groups"]:
                                sys_name = self.kb.knowledge["system_groups"][page_data["system_group"]]["definition"]
                            print(f"  System: {page_data['system_group']} ({sys_name})")

                        if page_data.get("location"):
                            loc_name = page_data["location"]
                            if "locations" in self.kb.knowledge and page_data["location"] in self.kb.knowledge["locations"]:
                                loc_name = self.kb.knowledge["locations"][page_data["location"]]["description"]
                            print(f"  Location: {page_data['location']} ({loc_name})")

                        if page_data.get("summary"):
                            print(f"  Summary: {page_data['summary']}")

                        print()
                        return

        print(f"  Sheet {sheet_number} not found in indexed PDFs\n")

    def list_systems(self):
        """List all system groups found in indexed sheets"""
        print(f"\n📊 System Groups in Indexed Sheets")
        print("="*60 + "\n")

        systems = {}

        # Collect all system groups from indexed pages
        for section, pdfs in self.section_mgr.registry["sections"].items():
            for pdf_name, pdf_info in pdfs.items():
                if not pdf_info.get("indexed"):
                    continue

                for page_num, page_data in pdf_info.get("pages", {}).items():
                    sys_code = page_data.get("system_group")
                    if sys_code:
                        if sys_code not in systems:
                            systems[sys_code] = {
                                "name": sys_code,
                                "sheets": []
                            }
                        systems[sys_code]["sheets"].append(page_data.get("sheet_number", "unknown"))

        if systems:
            # Look up names from glossary
            for sys_code in sorted(systems.keys()):
                sys_name = sys_code
                if "system_groups" in self.kb.knowledge and sys_code in self.kb.knowledge["system_groups"]:
                    sys_name = self.kb.knowledge["system_groups"][sys_code]["definition"]

                sheet_count = len(systems[sys_code]["sheets"])
                print(f"{sys_code:10} - {sys_name}")
                print(f"             {sheet_count} sheet(s)")
                print()

            print(f"Total: {len(systems)} system group(s) found\n")
        else:
            print("  No indexed sheets found with system group metadata")
            print("  (PDFs need to be indexed or re-indexed with latest Vision extraction)\n")

    def run_command(self, command: str, args: list = None):
        """Execute a command"""
        args = args or []

        if command == "help":
            self.print_help()

        elif command == "train":
            self.training_mode()

        elif command == "query":
            if not args:
                print("\nUsage: query <search text>\n")
            else:
                self.query_knowledge(" ".join(args))

        elif command == "load":
            if len(args) < 3 or args[0] != "section":
                print("\nUsage: load section <section_name> <pdf_path> [--index]\n")
                print(f"Valid sections: {', '.join(SectionManager.VALID_SECTIONS)}\n")
            else:
                section = args[1]
                pdf_path = " ".join(args[2:]).replace("--index", "").strip()
                auto_index = "--index" in args
                self.load_section_pdf(section, pdf_path, auto_index)

        elif command == "index":
            if len(args) < 2:
                print("\nUsage: index <section> <pdf_name>\n")
            else:
                self.index_pdf(args[0], args[1])

        elif command == "sections":
            self.list_sections()

        elif command == "section":
            if not args:
                print("\nUsage: section <section_name>\n")
            else:
                self.show_section_summary(args[0])

        elif command == "ask":
            if not args:
                print("\nUsage: ask <your question>\n")
            else:
                self.ask_question(" ".join(args))

        elif command == "analyze":
            if len(args) < 3:
                print("\nUsage: analyze <section> <pdf_name> <page_number>\n")
            else:
                try:
                    page_num = int(args[2])
                    self.analyze_page(args[0], args[1], page_num)
                except ValueError:
                    print("\n✗ Invalid page number\n")

        elif command == "trace":
            if not args:
                print("\nUsage: trace <from_component> [to <to_component>]\n")
            else:
                to_comp = None
                if "to" in args:
                    to_idx = args.index("to")
                    from_comp = " ".join(args[:to_idx])
                    to_comp = " ".join(args[to_idx+1:])
                else:
                    from_comp = " ".join(args)
                self.trace_connection(from_comp, to_comp)

        elif command == "cache":
            if args and args[0] == "stats":
                self.show_cache_stats()
            elif args and args[0] == "clear":
                self.clear_cache()
            else:
                print("\nUsage: cache [stats|clear]\n")

        elif command == "sheets":
            if not args:
                print("\nUsage: sheets <code>")
                print("  Example: sheets =10    (find sheets for system =10)")
                print("  Example: sheets +E3    (find sheets at location +E3)\n")
            else:
                code = args[0]
                if code.startswith('='):
                    self.query_sheets_by_system(code)
                elif code.startswith('+'):
                    self.query_sheets_by_location(code)
                else:
                    print(f"\n✗ Invalid code format: {code}")
                    print("  System codes start with = (e.g., =10)")
                    print("  Location codes start with + (e.g., +E3)\n")

        elif command == "sheet":
            if not args:
                print("\nUsage: sheet <number>")
                print("  Example: sheet 102\n")
            else:
                self.find_sheet(args[0])

        elif command == "systems":
            self.list_systems()

        elif command == "show":
            if not args:
                print("\nUsage: show [slaves|slave <N>|connections]\n")
            elif args[0] == "slaves":
                self._show_slaves()
            elif args[0] == "slave" and len(args) > 1:
                try:
                    slave_id = int(args[1])
                    self._show_slave_detail(slave_id)
                except ValueError:
                    print(f"\n✗ Invalid slave ID: {args[1]}\n")
            elif args[0] == "connections":
                self._show_connections()

        elif command == "summary":
            print("\n" + self.kb.export_summary() + "\n")

        elif command == "export":
            filename = args[0] if args else "trace_export.json"
            import shutil
            shutil.copy(self.kb.knowledge_file, filename)
            print(f"\n✓ Knowledge exported to {filename}\n")

        elif command in ["quit", "exit"]:
            self.running = False
            print("\nGoodbye!\n")

        else:
            print(f"\n✗ Unknown command: {command}")
            print("Type 'help' for available commands.\n")

    def _show_slaves(self):
        """Show all known slaves (legacy)"""
        slaves = self.kb.get_all_slaves()
        if not slaves:
            print("\nNo slaves in knowledge base.\n")
            return

        print("\n=== Known Slaves ===")
        for slave_id, data in sorted(slaves.items(), key=lambda x: int(x[0])):
            print(f"\nSlave {slave_id}:")
            print(f"  Cabinet: {data.get('cabinet', 'N/A')}")
            print(f"  Modules: {data.get('module_count', 0)}")
        print()

    def _show_slave_detail(self, slave_id: int):
        """Show slave details (legacy)"""
        slave = self.kb.get_slave(slave_id)
        if not slave:
            print(f"\nSlave {slave_id} not found.\n")
            return

        print(f"\n=== Slave {slave_id} ===")
        print(f"Cabinet: {slave.get('cabinet', 'N/A')}")
        print(f"Modules: {slave.get('module_count', 0)}")
        print()

    def _show_connections(self):
        """Show all connections (legacy)"""
        connections = self.kb.knowledge["connections"]
        if not connections:
            print("\nNo connections in knowledge base.\n")
            return

        print("\n=== Known Connections ===")
        for conn in connections:
            print(f"  {conn['from']} → {conn['to']}")
        print()

    def run(self):
        """Main CLI loop"""
        self.print_header()
        print("Type 'help' for available commands.\n")

        while self.running:
            try:
                user_input = input("TRACE> ").strip()

                if not user_input:
                    continue

                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1].split() if len(parts) > 1 else []

                self.run_command(command, args)

            except KeyboardInterrupt:
                print("\n\nUse 'quit' or 'exit' to leave TRACE.\n")
            except EOFError:
                break
            except Exception as e:
                print(f"\n✗ Error: {e}\n")
                import traceback
                traceback.print_exc()


def main():
    """Entry point"""
    cli = TRACECLI()
    cli.run()


if __name__ == "__main__":
    main()
