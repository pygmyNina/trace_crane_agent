#!/usr/bin/env python3
"""
TRACE - Crane Schematic Assistant and Copilot
Command-line interface for training and querying crane schematic knowledge
"""

import sys
import os
from trace.knowledge_base import KnowledgeBase
from trace.pdf_loader import PDFSchematicLoader
from trace.training_interface import TrainingInterface


class TRACECLI:
    """Main CLI interface for TRACE"""

    def __init__(self):
        self.kb = KnowledgeBase()
        self.pdf_loader = PDFSchematicLoader()
        self.trainer = TrainingInterface(self.kb)
        self.running = True

    def print_header(self):
        """Print TRACE header"""
        print("\n" + "="*60)
        print("  TRACE - Crane Schematic Assistant & Copilot")
        print("  Version 0.1.0")
        print("="*60 + "\n")

    def print_help(self):
        """Print available commands"""
        print("\nAvailable Commands:")
        print("  train          - Enter training mode to teach TRACE")
        print("  query <text>   - Search the knowledge base")
        print("  load <pdf>     - Load a schematic PDF file")
        print("  list           - List available schematics")
        print("  show slaves    - Show all known slaves")
        print("  show slave <N> - Show details for specific slave")
        print("  show connections - Show all connections")
        print("  summary        - Display knowledge base summary")
        print("  export         - Export knowledge to file")
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
        """Query the knowledge base"""
        results = self.kb.search(query)

        if not results:
            print(f"\nNo results found for: {query}\n")
            return

        print(f"\nSearch results for '{query}':")
        print("-" * 50)

        for result in results:
            result_type = result["type"]
            data = result["data"]

            if result_type == "slave":
                print(f"\n[Slave {data['id']}]")
                print(f"  Cabinet: {data.get('cabinet', 'N/A')}")
                print(f"  Modules: {data.get('module_count', 0)}")
                if data.get('modules'):
                    print(f"  Types: {', '.join(data['modules'][:5])}")

            elif result_type == "connection":
                print(f"\n[Connection]")
                print(f"  From: {data['from']}")
                print(f"  To: {data['to']}")
                if data.get('signal_type'):
                    print(f"  Type: {data['signal_type']}")

            elif result_type == "learning":
                print(f"\n[Learning: {data.get('topic', 'N/A')}]")
                print(f"  {data.get('content', '')[:100]}")

        print()

    def load_pdf(self, pdf_path: str):
        """Load a PDF schematic"""
        print(f"\nLoading PDF: {pdf_path}")

        result = self.pdf_loader.load_pdf(pdf_path)

        if "error" in result:
            print(f"✗ Error: {result['error']}\n")
            return

        print(f"✓ Loaded {result['num_pages']} pages from {result['filename']}")

        # Extract component information
        components = self.pdf_loader.extract_component_info(result)

        print(f"\nExtracted:")
        print(f"  Slaves: {', '.join(components['slaves']) if components['slaves'] else 'None'}")
        print(f"  Cabinets: {', '.join(components['cabinets']) if components['cabinets'] else 'None'}")
        print(f"  References: {len(components['references'])} found")

        if components['references']:
            print(f"  Sample refs: {', '.join(components['references'][:5])}")

        print()

    def show_slaves(self):
        """Show all known slaves"""
        slaves = self.kb.get_all_slaves()

        if not slaves:
            print("\nNo slaves in knowledge base yet.\n")
            return

        print("\n=== Known Slaves ===")
        for slave_id, data in sorted(slaves.items(), key=lambda x: int(x[0])):
            print(f"\nSlave {slave_id}:")
            print(f"  Cabinet: {data.get('cabinet', 'N/A')}")
            print(f"  Modules: {data.get('module_count', 0)}")
            if data.get('modules'):
                module_summary = {}
                for mod in data['modules']:
                    module_summary[mod] = module_summary.get(mod, 0) + 1
                print(f"  Types: {', '.join([f'{count} {mod}' for mod, count in module_summary.items()])}")

    def show_slave_detail(self, slave_id: int):
        """Show details for a specific slave"""
        slave = self.kb.get_slave(slave_id)

        if not slave:
            print(f"\nSlave {slave_id} not found in knowledge base.\n")
            return

        print(f"\n=== Slave {slave_id} ===")
        print(f"Cabinet: {slave.get('cabinet', 'N/A')}")
        print(f"Total Modules: {slave.get('module_count', 0)}")

        if slave.get('modules'):
            print("\nModule Breakdown:")
            module_summary = {}
            for mod in slave['modules']:
                module_summary[mod] = module_summary.get(mod, 0) + 1
            for mod, count in sorted(module_summary.items()):
                print(f"  {count:2d} × {mod}")

        # Show connections
        from_conns = self.kb.get_connections_from(f"slave_{slave_id}")
        to_conns = self.kb.get_connections_to(f"slave_{slave_id}")

        if from_conns or to_conns:
            print("\nConnections:")
            for conn in from_conns:
                print(f"  → {conn['to']}")
            for conn in to_conns:
                print(f"  ← {conn['from']}")

        print()

    def show_connections(self):
        """Show all connections"""
        connections = self.kb.knowledge["connections"]

        if not connections:
            print("\nNo connections in knowledge base yet.\n")
            return

        print("\n=== Known Connections ===")
        for conn in connections:
            signal = f" ({conn['signal_type']})" if conn.get('signal_type') else ""
            print(f"  {conn['from']} → {conn['to']}{signal}")
        print()

    def run_command(self, command: str, args: List[str] = None):
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
            if not args:
                print("\nUsage: load <pdf_file_path>\n")
            else:
                self.load_pdf(" ".join(args))

        elif command == "list":
            schematics = self.pdf_loader.list_schematics()
            if schematics:
                print("\nAvailable schematics:")
                for schematic in schematics:
                    print(f"  - {schematic}")
                print()
            else:
                print(f"\nNo schematics found in {self.pdf_loader.schematics_dir}/")
                print("Place PDF files there or use 'load <path>' to load from elsewhere.\n")

        elif command == "show":
            if not args:
                print("\nUsage: show [slaves|slave <N>|connections]\n")
            elif args[0] == "slaves":
                self.show_slaves()
            elif args[0] == "slave" and len(args) > 1:
                try:
                    slave_id = int(args[1])
                    self.show_slave_detail(slave_id)
                except ValueError:
                    print(f"\nInvalid slave ID: {args[1]}\n")
            elif args[0] == "connections":
                self.show_connections()
            else:
                print(f"\nUnknown show command: {args[0]}\n")

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
            print(f"\nUnknown command: {command}")
            print("Type 'help' for available commands.\n")

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


def main():
    """Entry point"""
    cli = TRACECLI()
    cli.run()


if __name__ == "__main__":
    main()
