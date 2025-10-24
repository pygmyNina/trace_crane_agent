#!/usr/bin/env python3
"""
Build Searchable Component Database
Extracts training data into searchable database for the copilot system
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database_builder import DatabaseBuilder
from database_schema import SchematicDatabase
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def show_banner(console: Console):
    """Display welcome banner"""
    banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   Database Builder - Phase 2                                 ║
║                                                              ║
║   Building Searchable Component Database                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[yellow]Purpose:[/yellow]
Extract training data into searchable database for:
✓ Component lookup
✓ Wire path tracing
✓ Troubleshooting copilot
✓ AI agent integration

[yellow]Data Sources:[/yellow]
• Ground truth labels (data/ground_truth/*.json)
• Training examples (data/training_data/training_examples.jsonl)
"""
    console.print(banner)


def show_database_contents(console: Console, db_path: str = "data/copilot/schematic_knowledge.db"):
    """Show what's in the database"""
    with SchematicDatabase(db_path) as db:
        stats = db.get_statistics()

        console.print("\n[bold cyan]Database Contents:[/bold cyan]\n")

        # Create summary table
        summary = Table(title="Summary Statistics")
        summary.add_column("Metric", style="cyan")
        summary.add_column("Count", style="green", justify="right")

        summary.add_row("Total Components", str(stats['total_components']))
        summary.add_row("Component Types", str(stats['component_types']))
        summary.add_row("Total Connections", str(stats['total_connections']))
        summary.add_row("Cabinets", str(stats['cabinets']))
        summary.add_row("Indexed Pages", str(stats['indexed_pages']))

        console.print(summary)

        # Component breakdown
        if stats['components_by_type']:
            console.print("\n[bold]Components by Type:[/bold]")
            type_table = Table()
            type_table.add_column("Type", style="cyan")
            type_table.add_column("Count", style="green", justify="right")

            for comp_type, count in sorted(stats['components_by_type'].items(),
                                          key=lambda x: x[1], reverse=True):
                type_table.add_row(comp_type, str(count))

            console.print(type_table)


def test_search(console: Console, db_path: str = "data/copilot/schematic_knowledge.db"):
    """Test search functionality"""
    with SchematicDatabase(db_path) as db:
        console.print("\n[bold cyan]Testing Search Functionality:[/bold cyan]\n")

        # Search for slaves
        console.print("[yellow]Searching for 'Slave'...[/yellow]")
        results = db.search_component("Slave", search_type="name")
        if results:
            for comp in results[:5]:  # Show first 5
                console.print(f"  • {comp['name']} - Type: {comp['type']}, "
                            f"Index: {comp['index_reference']}, "
                            f"Cabinet: {comp['cabinet']}")
            if len(results) > 5:
                console.print(f"  ... and {len(results) - 5} more")
        else:
            console.print("  [red]No results found[/red]")

        # Search for HVC
        console.print("\n[yellow]Searching for 'HVC'...[/yellow]")
        results = db.search_component("HVC", search_type="type")
        if results:
            for comp in results[:5]:
                console.print(f"  • {comp['name']} at {comp['index_reference']}")
            if len(results) > 5:
                console.print(f"  ... and {len(results) - 5} more")
        else:
            console.print("  [red]No results found[/red]")

        # Search by cabinet
        console.print("\n[yellow]Searching for Cabinet 'E11'...[/yellow]")
        results = db.search_component("E11", search_type="cabinet")
        if results:
            for comp in results[:5]:
                console.print(f"  • {comp['name']} - {comp['type']}")
            if len(results) > 5:
                console.print(f"  ... and {len(results) - 5} more")
        else:
            console.print("  [red]No results found[/red]")


def test_connections(console: Console, db_path: str = "data/copilot/schematic_knowledge.db"):
    """Test connection queries"""
    with SchematicDatabase(db_path) as db:
        console.print("\n[bold cyan]Testing Connection Queries:[/bold cyan]\n")

        # Get first component with connections
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT c.name
            FROM components c
            JOIN connections conn ON c.id = conn.from_component_id OR c.id = conn.to_component_id
            LIMIT 1
        """)
        row = cursor.fetchone()

        if row:
            comp_name = row[0]
            console.print(f"[yellow]Connections for '{comp_name}':[/yellow]")

            connections = db.get_component_connections(comp_name)

            if connections['outgoing']:
                console.print(f"\n  Outgoing ({len(connections['outgoing'])}):")
                for conn in connections['outgoing'][:3]:
                    console.print(f"    → {conn['to_component_name']} "
                                f"(Wire: {conn['wire_label']}, "
                                f"Type: {conn['connection_type']})")

            if connections['incoming']:
                console.print(f"\n  Incoming ({len(connections['incoming'])}):")
                for conn in connections['incoming'][:3]:
                    console.print(f"    ← {conn['from_component_name']} "
                                f"(Wire: {conn['wire_label']}, "
                                f"Type: {conn['connection_type']})")
        else:
            console.print("[yellow]No connections found in database yet[/yellow]")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Build searchable component database")
    parser.add_argument("--build", action="store_true",
                       help="Build database from training data")
    parser.add_argument("--show", action="store_true",
                       help="Show database contents")
    parser.add_argument("--test", action="store_true",
                       help="Test search and queries")
    parser.add_argument("--rebuild", action="store_true",
                       help="Delete and rebuild database from scratch")
    parser.add_argument("--db", default="data/copilot/schematic_knowledge.db",
                       help="Database path (default: data/copilot/schematic_knowledge.db)")

    args = parser.parse_args()

    console = Console()

    # If no args, show banner and build
    if not any([args.build, args.show, args.test, args.rebuild]):
        show_banner(console)
        args.build = True
        args.show = True
        args.test = True

    # Rebuild from scratch
    if args.rebuild:
        console.print("[yellow]Rebuilding database from scratch...[/yellow]")
        db_path = Path(args.db)
        if db_path.exists():
            db_path.unlink()
            console.print(f"[green]✓ Deleted existing database[/green]")
        args.build = True

    # Build database
    if args.build:
        console.print("\n[bold cyan]Building Database...[/bold cyan]\n")

        with DatabaseBuilder(args.db) as builder:
            builder.build_all()

        console.print("\n[green]✓ Database build complete![/green]")

    # Show contents
    if args.show:
        show_database_contents(console, args.db)

    # Test functionality
    if args.test:
        test_search(console, args.db)
        test_connections(console, args.db)

    console.print("\n[bold green]✓ Database ready for copilot system![/bold green]\n")


if __name__ == "__main__":
    main()
