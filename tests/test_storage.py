"""
Tests for Storage System
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from storage import TrainingStorage


def test_storage_initialization():
    """Test storage initialization"""
    storage = TrainingStorage(data_dir="data/test_storage")
    assert storage.db_path.exists()
    print("✓ Storage initialization test passed")


def test_create_session():
    """Test session creation"""
    storage = TrainingStorage(data_dir="data/test_storage")
    session_id = storage.create_session(pdf_file="test.pdf")
    assert session_id.startswith("session_")
    assert (storage.sessions_dir / session_id).exists()
    print("✓ Session creation test passed")
    return session_id


def test_log_question():
    """Test logging questions"""
    time.sleep(1.1)  # Ensure unique session ID
    storage = TrainingStorage(data_dir="data/test_storage")
    session_id = storage.create_session()

    storage.log_question(
        session_id,
        "What is =61/102.8?",
        "=61/102.8.0",
        "=61/102.0.8",
        False,
        "index_format"
    )

    stats = storage.get_session_stats(session_id)
    assert stats["total_questions"] == 1
    assert stats["correct_answers"] == 0
    print("✓ Log question test passed")


def test_log_correction():
    """Test logging corrections"""
    time.sleep(1.1)  # Ensure unique session ID
    storage = TrainingStorage(data_dir="data/test_storage")
    session_id = storage.create_session()

    storage.log_correction(
        session_id,
        "What is =61/102.8?",
        "=61/102.8.0",
        "=61/102.0.8",
        "index_format",
        "Shorthand notation"
    )

    corrections = storage.get_corrections(session_id)
    assert len(corrections) >= 1
    print("✓ Log correction test passed")


def test_session_stats():
    """Test session statistics"""
    time.sleep(1.1)  # Ensure unique session ID
    storage = TrainingStorage(data_dir="data/test_storage")
    session_id = storage.create_session()

    # Log some questions
    storage.log_question(session_id, "Q1", "A1", "A1", True, "general")
    storage.log_question(session_id, "Q2", "Wrong", "Right", False, "general")

    stats = storage.get_session_stats(session_id)
    assert stats["total_questions"] == 2
    assert stats["correct_answers"] == 1
    assert stats["accuracy"] == 50.0
    print("✓ Session stats test passed")


def test_end_session():
    """Test ending a session"""
    time.sleep(1.1)  # Ensure unique session ID
    storage = TrainingStorage(data_dir="data/test_storage")
    session_id = storage.create_session()

    storage.end_session(session_id)

    stats = storage.get_session_stats(session_id)
    assert stats["end_time"] is not None
    print("✓ End session test passed")


if __name__ == "__main__":
    print("Running Storage Tests...\n")
    test_storage_initialization()
    test_create_session()
    test_log_question()
    test_log_correction()
    test_session_stats()
    test_end_session()
    print("\n✓ All tests passed!")
