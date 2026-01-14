"""Test script for Wikipedia section selection functionality."""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extractors.wikipedia_extractor import WikipediaExtractor
from src.processors.ai_enhancer_with_sections import ClaudeAIEnhancerWithSections
from src.utils.logger import logger
import json

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    os.system('chcp 65001 > nul')


def test_wikipedia_sections():
    """Test Wikipedia extractor generates sections and ToC."""
    print("\n" + "="*80)
    print("TEST 1: Wikipedia Section Extraction")
    print("="*80)

    extractor = WikipediaExtractor()

    # Test with a well-known person
    test_name = "Donald J. Trump"
    print(f"\nFetching Wikipedia data for: {test_name}")

    wiki_data = extractor.fetch_person_data(test_name)

    if not wiki_data:
        print("[FAIL] Failed to fetch Wikipedia data")
        return False

    # Check for new fields
    if 'sections' not in wiki_data:
        print("[FAIL] 'sections' field missing from wiki_data")
        return False

    if 'table_of_contents' not in wiki_data:
        print("[FAIL] 'table_of_contents' field missing from wiki_data")
        return False

    sections = wiki_data['sections']
    toc = wiki_data['table_of_contents']

    print(f"\n[OK] Extracted {len(sections)} sections")
    print(f"\n[ToC] Table of Contents:\n{toc}")

    # Show first few sections
    print(f"\n[Sections] First 3 sections:")
    for i, section in enumerate(sections[:3]):
        print(f"\n  Section {i+1}: {section['name']}")
        print(f"    Level: {section.get('heading_level', 0)}")
        print(f"    Length: {len(section['text'])} chars")
        print(f"    Preview: {section['text'][:100]}...")

    # Check backward compatibility
    if 'chunks' in wiki_data:
        print(f"\n[OK] Backward compatibility maintained: {len(wiki_data['chunks'])} chunks available")
    else:
        print("\n[WARN] Warning: 'chunks' field missing (backward compatibility issue)")

    return True


def test_section_selection():
    """Test AI section selection functionality."""
    print("\n" + "="*80)
    print("TEST 2: AI Section Selection")
    print("="*80)

    # Get Wikipedia data first
    extractor = WikipediaExtractor()
    test_name = "Tulsi Gabbard"
    print(f"\nFetching Wikipedia data for: {test_name}")

    wiki_data = extractor.fetch_person_data(test_name)

    if not wiki_data or not wiki_data.get('sections'):
        print("[FAIL] Failed to get Wikipedia data with sections")
        return False

    print(f"\n[Available] Available sections ({len(wiki_data['sections'])} total):")
    print(wiki_data['table_of_contents'])

    # Test AI section selection
    test_person = {
        'name': test_name,
        'ChineseName': '图尔西·加巴德',
        'currentRole': '美国国家情报总监提名人'
    }

    print(f"\n[AI] Testing AI section selection...")
    enhancer = ClaudeAIEnhancerWithSections()

    # Test round 1: section selection
    selected_sections = enhancer._select_sections(test_person, wiki_data)

    if not selected_sections:
        print("[FAIL] AI failed to select sections")
        return False

    print(f"\n[OK] AI selected {len(selected_sections)} sections:")
    for section in selected_sections:
        print(f"  - {section}")

    # Test round 2: information extraction
    print(f"\n[AI] Testing information extraction...")
    result = enhancer.enhance_single(test_person, wiki_data)

    print(f"\n[Result] Extracted information:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Validate results
    if not result.get('name'):
        print("[FAIL] Name missing from result")
        return False

    if result.get('sources') and len(result['sources']) > 0:
        print(f"\n[OK] Sources: {len(result['sources'])} source(s)")
    else:
        print("\n[WARN] Warning: No sources in result")

    return True


def test_backward_compatibility():
    """Test that legacy mode still works."""
    print("\n" + "="*80)
    print("TEST 3: Backward Compatibility (Legacy Mode)")
    print("="*80)

    from src.processors.ai_enhancer import ClaudeAIEnhancer
    from src.config.settings import Settings

    # Temporarily disable section selection
    original_setting = getattr(Settings, 'USE_SECTION_SELECTION', False)
    Settings.USE_SECTION_SELECTION = False

    try:
        enhancer = ClaudeAIEnhancer()
        test_person = {
            'name': 'Nancy Pelosi',
            'ChineseName': '南希·佩洛西',
            'currentRole': 'Former Speaker of the House'
        }

        # Get Wikipedia data
        extractor = WikipediaExtractor()
        wiki_data = extractor.fetch_person_data(test_person['name'])

        if not wiki_data:
            print("[FAIL] Failed to fetch Wikipedia data")
            return False

        # Prepare wiki data dict
        wiki_dict = {test_person['name']: wiki_data}

        print(f"\n[Legacy] Testing legacy mode enhancement...")
        results = enhancer.enhance_batch([test_person], wiki_dict)

        if not results or len(results) == 0:
            print("[FAIL] Legacy mode failed to return results")
            return False

        result = results[0]
        print(f"\n[Result] Legacy mode result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return True

    finally:
        # Restore original setting
        Settings.USE_SECTION_SELECTION = original_setting


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("RUNNING ALL TESTS FOR SECTION SELECTION FEATURE")
    print("="*80)

    tests = [
        ("Wikipedia Sections", test_wikipedia_sections),
        ("AI Section Selection", test_section_selection),
        ("Backward Compatibility", test_backward_compatibility)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "[PASS]" if success else "[FAIL]"
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}", exc_info=True)
            results[test_name] = f"[CRASH]: {e}"

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, status in results.items():
        print(f"{status} - {test_name}")

    all_passed = all("[PASS]" in status for status in results.values())
    print("\n" + "="*80)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED")
    else:
        print("[FAILURE] SOME TESTS FAILED")
    print("="*80)

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
