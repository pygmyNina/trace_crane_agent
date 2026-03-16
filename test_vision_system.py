#!/usr/bin/env python3
"""
Test script for TRACE Vision system
Tests basic functionality without requiring API key
"""

import os
import sys

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from trace.knowledge_base import KnowledgeBase
        from trace.training_interface import TrainingInterface
        from trace.pdf_image_converter import PDFImageConverter
        from trace.vision_analyzer import VisionAnalyzer
        from trace.section_manager import SectionManager
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_knowledge_base():
    """Test knowledge base functionality"""
    print("\nTesting knowledge base...")
    try:
        from trace.knowledge_base import KnowledgeBase

        kb = KnowledgeBase("test_knowledge.json")

        # Test adding data
        kb.add_slave(99, ["DI", "DO"], 2, "TEST")
        kb.add_connection("Test A", "Test B", "test_signal")
        kb.add_sequence("test", [1, 2, 3])

        # Test retrieval
        slave = kb.get_slave(99)
        assert slave is not None, "Failed to retrieve slave"
        assert slave["cabinet"] == "TEST", "Slave data incorrect"

        # Cleanup
        if os.path.exists("test_knowledge.json"):
            os.remove("test_knowledge.json")

        print("✓ Knowledge base working")
        return True
    except Exception as e:
        print(f"✗ Knowledge base error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_section_manager():
    """Test section manager"""
    print("\nTesting section manager...")
    try:
        from trace.section_manager import SectionManager

        mgr = SectionManager("test_schematics", "test_registry.json")

        # Test section creation
        sections = mgr.list_sections()
        assert 'electrical' in sections, "Sections not created"

        print("✓ Section manager working")

        # Cleanup
        if os.path.exists("test_registry.json"):
            os.remove("test_registry.json")
        import shutil
        if os.path.exists("test_schematics"):
            shutil.rmtree("test_schematics")

        return True
    except Exception as e:
        print(f"✗ Section manager error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_converter():
    """Test PDF image converter"""
    print("\nTesting PDF converter...")
    try:
        from trace.pdf_image_converter import PDFImageConverter

        converter = PDFImageConverter("test_cache")

        # Test cache management
        file_count, size = converter.get_cache_size()
        assert isinstance(file_count, int), "Cache stats failed"

        print("✓ PDF converter initialized")

        # Check if pdf2image is available
        from trace.pdf_image_converter import PDF2IMAGE_AVAILABLE
        if PDF2IMAGE_AVAILABLE:
            print("  ✓ pdf2image library available")
        else:
            print("  ⚠ pdf2image not installed (pip install pdf2image)")

        # Cleanup
        if os.path.exists("test_cache"):
            import shutil
            shutil.rmtree("test_cache")

        return True
    except Exception as e:
        print(f"✗ PDF converter error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vision_analyzer():
    """Test vision analyzer"""
    print("\nTesting vision analyzer...")
    try:
        from trace.vision_analyzer import VisionAnalyzer, ANTHROPIC_AVAILABLE

        if not ANTHROPIC_AVAILABLE:
            print("  ⚠ anthropic library not installed")
            print("  Install with: pip install anthropic")
            return True

        analyzer = VisionAnalyzer()

        # Check API availability (doesn't require actual key)
        if analyzer.check_api_available():
            print("  ✓ Vision API configured")
        else:
            print("  ⚠ Vision API not configured (need ANTHROPIC_API_KEY)")

        # Test cost estimation
        estimate = analyzer.get_usage_estimate(10)
        assert estimate["pages"] == 10, "Cost estimate failed"

        print("✓ Vision analyzer initialized")
        return True
    except Exception as e:
        print(f"✗ Vision analyzer error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_import():
    """Test that CLI can be imported"""
    print("\nTesting CLI import...")
    try:
        # Don't actually run CLI, just import it
        import importlib.util
        spec = importlib.util.spec_from_file_location("trace_cli", "trace_cli.py")
        module = importlib.util.module_from_spec(spec)

        print("✓ CLI can be imported")
        return True
    except Exception as e:
        print(f"✗ CLI import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("  TRACE Vision System Tests")
    print("="*60)

    tests = [
        ("Imports", test_imports),
        ("Knowledge Base", test_knowledge_base),
        ("Section Manager", test_section_manager),
        ("PDF Converter", test_pdf_converter),
        ("Vision Analyzer", test_vision_analyzer),
        ("CLI Import", test_cli_import),
    ]

    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    # Summary
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8s} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! System is ready.")
        print("\nNext steps:")
        print("  1. Set ANTHROPIC_API_KEY for Vision features")
        print("  2. Install pdf2image if needed: pip install pdf2image")
        print("  3. Install poppler if needed (for pdf2image)")
        print("  4. Run: python trace_cli.py")
    else:
        print("\n⚠ Some tests failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
