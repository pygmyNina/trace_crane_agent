#!/usr/bin/env python3
"""
Quick demo of TRACE capabilities
Run this after importing the October 23 training data
"""

from trace.knowledge_base import KnowledgeBase
from trace.training_interface import TrainingInterface


def demo():
    """Demonstrate TRACE functionality"""

    print("\n" + "="*60)
    print("  TRACE Demo - Crane Schematic Assistant")
    print("="*60 + "\n")

    # Initialize
    kb = KnowledgeBase()
    trainer = TrainingInterface(kb)

    # Show what we know
    print("1. KNOWLEDGE BASE SUMMARY")
    print("-" * 60)
    print(kb.export_summary())

    # Show slave details
    print("\n2. SLAVE 22 DETAILS")
    print("-" * 60)
    slave = kb.get_slave(22)
    if slave:
        print(f"Slave ID: {slave['id']}")
        print(f"Cabinet: {slave['cabinet']}")
        print(f"Total Modules: {slave['module_count']}")
        print("\nModule Breakdown:")
        module_count = {}
        for mod in slave['modules']:
            module_count[mod] = module_count.get(mod, 0) + 1
        for mod, count in module_count.items():
            print(f"  {count:2d} × {mod}")

    # Search examples
    print("\n3. SEARCH EXAMPLES")
    print("-" * 60)

    print("\nSearching for 'E11':")
    results = kb.search("E11")
    for r in results:
        if r["type"] == "slave":
            print(f"  → Found Slave {r['data']['id']} in Cabinet {r['data']['cabinet']}")

    print("\nSearching for 'HVC3':")
    results = kb.search("HVC3")
    for r in results:
        if r["type"] == "connection":
            print(f"  → Found connection: {r['data']['from']} → {r['data']['to']}")

    # Training example
    print("\n4. TRAINING EXAMPLE")
    print("-" * 60)
    print("Training: 'Slave 23 has 30 modules in Cabinet E12'")

    response = trainer.process_training_input("Slave 23 has 30 modules in Cabinet E12")

    if response["understood"]:
        for item in response["understood"]:
            print(f"  ✓ {item}")
    print(f"  {response['message']}")

    # Verify it was learned
    print("\nVerifying learned data:")
    slave23 = kb.get_slave(23)
    if slave23:
        print(f"  → Slave 23: {slave23['module_count']} modules in {slave23['cabinet']}")

    # Show sequences
    print("\n5. SEQUENCES")
    print("-" * 60)
    for name, seq_data in kb.knowledge["sequences"].items():
        print(f"{name}: {seq_data['sequence']}")
        if seq_data.get("description"):
            print(f"  ({seq_data['description']})")

    print("\n" + "="*60)
    print("  Demo complete! Launch TRACE with: python trace_cli.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    demo()
