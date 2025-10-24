#!/usr/bin/env python3
"""
Import training data from October 23, 2024
Initial TRACE knowledge base population
"""

from trace.knowledge_base import KnowledgeBase


def import_oct23_training():
    """Import the October 23 training data"""

    print("Importing October 23 training data...")

    kb = KnowledgeBase()

    # Index format rule
    kb.add_learning(
        topic="index_format",
        content="Index format: =XX/YY.Y.Z - This is the standard reference format used throughout crane schematics",
        source="oct23_training"
    )
    print("✓ Imported index format rule")

    # Wire rules
    kb.add_learning(
        topic="wire_rules",
        content="Wire rule: dots indicate connections - When wires cross with a dot, they are electrically connected",
        source="oct23_training"
    )

    kb.add_learning(
        topic="wire_rules",
        content="Wire rule: perpendicular crossings without dots indicate no connection - When wires cross perpendicularly without a dot, they are NOT electrically connected",
        source="oct23_training"
    )
    print("✓ Imported wire connection rules")

    # Slave sequence
    kb.add_sequence(
        name="slave",
        sequence=[22, 23, 60, 24, 61, 20],
        description="Discovered slave sequence order"
    )
    print("✓ Imported slave sequence: 22, 23, 60, 24, 61, 20")

    # Slave 22 configuration
    kb.add_slave(
        slave_id=22,
        modules=["IM151"] + ["PM"] + ["DI"] * 40 + ["RTD"] * 3,
        count=45,
        cabinet="E11"
    )
    print("✓ Imported Slave 22: 45 modules (1 IM151, 1 PM, 40 DI, 3 RTD) in Cabinet E11")

    # HVC3 breaker connection
    kb.add_connection(
        from_ref="HVC3 breaker signal",
        to_ref="=61/4.1.3",
        signal_type="breaker_signal",
        notes="HVC3 breaker status signal routing"
    )
    print("✓ Imported connection: HVC3 breaker signal → =61/4.1.3")

    # Main transformer
    kb.knowledge["components"]["transformers"]["main"] = {
        "name": "Main transformer",
        "reference": "=10/102.0.3",
        "terminal": "1U",
        "type": "main_transformer"
    }
    kb.save()
    print("✓ Imported Main transformer at =10/102.0.3, terminal 1U")

    # Add a training session record
    kb.add_training_session({
        "source": "import_script",
        "date": "2024-10-23",
        "description": "Initial training data from October 23, 2024",
        "items": [
            "Index format rule",
            "Wire connection rules",
            "Slave sequence: 22,23,60,24,61,20",
            "Slave 22 configuration",
            "HVC3 breaker connection",
            "Main transformer location"
        ]
    })

    print("\n" + "="*60)
    print("✓ October 23 training data imported successfully!")
    print("="*60)

    # Display summary
    print("\n" + kb.export_summary())


if __name__ == "__main__":
    import_oct23_training()
