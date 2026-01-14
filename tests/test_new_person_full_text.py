"""Test full Wikipedia extraction with a person not in cache."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.wikipedia_extractor import WikipediaExtractor
from src.utils.logger import logger


def test_full_extraction():
    """Test full extraction for a new person."""
    # Use someone who likely isn't in cache yet
    test_person = "Alexandria Ocasio-Cortez"

    print("=" * 80)
    print(f"Testing FULL Wikipedia Extraction for: {test_person}")
    print("=" * 80)

    extractor = WikipediaExtractor()

    # Clear cache for this person if exists
    if test_person in extractor.cache:
        print(f"\nClearing cached data for {test_person}...")
        del extractor.cache[test_person]
        extractor._save_cache()

    print(f"\nFetching fresh Wikipedia data...")
    wiki_data = extractor.fetch_person_data(test_person)

    if not wiki_data:
        print(f"ERROR: No data found for {test_person}")
        return

    print(f"\n[SUCCESS] Fetched Wikipedia data:")
    print(f"  - Title: {wiki_data.get('wikipedia_title')}")
    print(f"  - URL: {wiki_data.get('url')}")
    print(f"  - Text Length: {wiki_data.get('text_length', 0):,} characters")
    print(f"  - Total Chunks: {wiki_data.get('total_chunks', 0)}")
    print(f"  - Prioritized Chunks: {len(wiki_data.get('chunks', []))}")
    print(f"  - Sections: {wiki_data.get('section_count', 0)}")

    # Show sections
    print(f"\nSections Found:")
    sections = wiki_data.get('sections', [])
    for section in sections:
        print(f"  - {section['name']} (intro={section['is_intro']}, {len(section['text'])} chars)")

    # Show chunks
    print(f"\nChunks Created:")
    chunks = wiki_data.get('chunks', [])
    for i, chunk in enumerate(chunks, 1):
        print(f"\n  Chunk {i}:")
        print(f"    Section: {chunk['section']}")
        print(f"    Is Intro: {chunk['is_intro']}")
        print(f"    Length: {len(chunk['text'])} chars")
        # Safe preview
        try:
            preview = chunk['text'][:100].encode('ascii', errors='ignore').decode('ascii')
            print(f"    Preview: {preview}...")
        except:
            print(f"    Preview: [Text contains special characters]")

    # Save to file
    output_file = Path(__file__).parent / "test_output" / "full_wikipedia_extraction.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(wiki_data, f, ensure_ascii=False, indent=2)

    print(f"\n[SUCCESS] Full data saved to: {output_file}")

    # Check if we got full content
    text_length = wiki_data.get('text_length', 0)
    if text_length > 5000:
        print(f"\n[SUCCESS] Got FULL Wikipedia content ({text_length:,} chars)")
    else:
        print(f"\n[WARNING] Content seems short ({text_length:,} chars) - may still be intro only")

    return wiki_data


if __name__ == "__main__":
    try:
        wiki_data = test_full_extraction()
        print("\n" + "=" * 80)
        print("TEST COMPLETED")
        print("=" * 80)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n[FAILED] Test error: {e}")
        sys.exit(1)
