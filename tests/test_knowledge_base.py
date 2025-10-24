"""
Tests for Knowledge Base
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from knowledge_base import KnowledgeBase


def test_knowledge_base_creation():
    """Test creating knowledge base"""
    kb = KnowledgeBase(data_dir="data/test_kb")
    assert kb.knowledge is not None
    assert "index_format" in kb.knowledge
    assert "wire_tracing" in kb.knowledge
    assert "slave_sequence" in kb.knowledge
    print("✓ Knowledge base creation test passed")


def test_index_format():
    """Test index format information"""
    kb = KnowledgeBase(data_dir="data/test_kb")
    help_text = kb.get_index_format_help()
    assert "=XX/YY.Y.Z" in help_text
    assert "=61/102.8" in help_text
    print("✓ Index format test passed")


def test_slave_sequence():
    """Test slave sequence"""
    kb = KnowledgeBase(data_dir="data/test_kb")
    sequence = kb.get_slave_sequence()
    assert sequence == [22, 23, 60, 24, 61, 20]
    print("✓ Slave sequence test passed")


def test_wire_tracing_rules():
    """Test wire tracing rules"""
    kb = KnowledgeBase(data_dir="data/test_kb")
    rules = kb.get_wire_tracing_rules()
    assert len(rules) >= 2
    assert any("dot" in rule["rule"].lower() for rule in rules)
    print("✓ Wire tracing rules test passed")


def test_component_examples():
    """Test component examples"""
    kb = KnowledgeBase(data_dir="data/test_kb")
    examples = kb.get_component_examples()
    assert "slave_22" in examples
    assert examples["slave_22"]["location"] == "Cabinet E11"
    assert examples["slave_22"]["modules"]["total"] == 45
    print("✓ Component examples test passed")


def test_format_for_training():
    """Test training format"""
    kb = KnowledgeBase(data_dir="data/test_kb")
    formatted = kb.format_for_training()
    assert "Index Format" in formatted
    assert "Wire Tracing" in formatted
    assert "Slave Sequence" in formatted
    print("✓ Format for training test passed")


if __name__ == "__main__":
    print("Running Knowledge Base Tests...\n")
    test_knowledge_base_creation()
    test_index_format()
    test_slave_sequence()
    test_wire_tracing_rules()
    test_component_examples()
    test_format_for_training()
    print("\n✓ All tests passed!")
