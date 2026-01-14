"""Test Wikipedia extraction with new chunking and preprocessing features."""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.wikipedia_extractor import WikipediaExtractor
from src.processors.text_preprocessor import TextPreprocessor
from src.processors.text_chunker import TextChunker
from src.utils.logger import logger


def test_full_wikipedia_extraction():
    """Test full Wikipedia extraction with chunking."""
    # Test with a well-known politician
    test_person = "Nancy Pelosi"

    print("=" * 80)
    print(f"Testing Wikipedia Extraction with Chunking for: {test_person}")
    print("=" * 80)

    # Initialize extractor
    extractor = WikipediaExtractor()

    # Fetch person data
    print("\n1. Fetching Wikipedia data...")
    wiki_data = extractor.fetch_person_data(test_person)

    if not wiki_data:
        print(f"ERROR: No Wikipedia data found for {test_person}")
        return

    print(f"[OK] Successfully fetched Wikipedia data")
    print(f"  - Wikipedia Title: {wiki_data.get('wikipedia_title')}")
    print(f"  - URL: {wiki_data.get('url')}")
    print(f"  - Text Length: {wiki_data.get('text_length', 0):,} characters")
    print(f"  - Total Chunks: {wiki_data.get('total_chunks', 0)}")
    print(f"  - Prioritized Chunks: {len(wiki_data.get('chunks', []))}")
    print(f"  - Sections: {wiki_data.get('section_count', 0)}")

    # Display chunk information
    print("\n2. Chunk Details:")
    chunks = wiki_data.get('chunks', [])
    for i, chunk in enumerate(chunks, 1):
        print(f"\n  Chunk {i}:")
        print(f"    - Section: {chunk['section']}")
        print(f"    - Is Intro: {chunk['is_intro']}")
        print(f"    - Length: {len(chunk['text'])} characters")
        # Encode/decode to handle special characters in Windows console
        try:
            preview = chunk['text'][:150].encode('gbk', errors='ignore').decode('gbk')
            print(f"    - Preview: {preview}...")
        except:
            print(f"    - Preview: [Contains special characters]")

    # Display section information
    if 'sections' in wiki_data:
        print(f"\n3. Sections ({len(wiki_data['sections'])}):")
        for section in wiki_data['sections']:
            print(f"  - {section['name']} (intro={section['is_intro']}, {len(section['text'])} chars)")

    # Save full result to file for inspection
    output_file = Path(__file__).parent / "test_output" / "wikipedia_chunking_test.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(wiki_data, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Full data saved to: {output_file}")

    # Test with multiple people
    print("\n" + "=" * 80)
    print("Testing with Multiple People")
    print("=" * 80)

    test_people = [
        {"name": "Joe Biden"},
        {"name": "Kamala Harris"},
        {"name": "Mitch McConnell"}
    ]

    results = extractor.fetch_batch(test_people)

    print(f"\nFetched data for {len(results)}/{len(test_people)} people:")
    for name, data in results.items():
        chunks_count = len(data.get('chunks', []))
        text_length = data.get('text_length', 0)
        print(f"  - {name}: {chunks_count} chunks, {text_length:,} chars")

    print("\n[OK] Test completed successfully!")
    return wiki_data


def test_components_separately():
    """Test preprocessor and chunker separately."""
    print("\n" + "=" * 80)
    print("Testing Components Separately")
    print("=" * 80)

    # Sample text
    sample_extract = """
Barack Obama (born August 4, 1961) is an American politician and attorney who served as the 44th president of the United States from 2009 to 2017.

== Early life ==
Obama was born in Honolulu, Hawaii. He graduated from Columbia University in 1983 with a Bachelor of Arts degree in political science.

== Education ==
He then attended Harvard Law School, where he was president of the Harvard Law Review. He graduated magna cum laude in 1991.

== Career ==
He worked as a civil rights attorney and taught constitutional law at the University of Chicago Law School from 1992 to 2004.

== Political career ==
He served three terms in the Illinois Senate from 1997 to 2004. He was elected to the U.S. Senate in 2004.

== Presidency ==
Obama was elected president in 2008 and re-elected in 2012. He was the first African-American president of the United States.

== See also ==
- List of presidents
- Obama administration

== References ==
[1] Citation 1
[2] Citation 2
"""

    # Test preprocessor
    print("\n1. Testing TextPreprocessor:")
    preprocessor = TextPreprocessor()

    wiki_data_sample = {
        'name': 'Barack Obama',
        'extract': sample_extract,
        'url': 'https://en.wikipedia.org/wiki/Barack_Obama'
    }

    processed = preprocessor.preprocess(wiki_data_sample)
    print(f"  - Original length: {len(sample_extract)} chars")
    print(f"  - Processed length: {len(processed['extract'])} chars")
    print(f"  - Sections found: {processed['section_count']}")
    for section in processed['sections']:
        print(f"    - {section['name']} (intro={section['is_intro']})")

    # Test chunker
    print("\n2. Testing TextChunker:")
    chunker = TextChunker(max_chunk_size=300, min_chunk_size=100, overlap=50)

    chunks = chunker.chunk_text(processed['extract'], 'Barack Obama')
    print(f"  - Total chunks created: {len(chunks)}")

    prioritized = chunker.prioritize_chunks(chunks, max_chunks=3)
    print(f"  - Prioritized chunks: {len(prioritized)}")
    for i, chunk in enumerate(prioritized, 1):
        print(f"    Chunk {i}: {chunk['section']} ({len(chunk['text'])} chars)")

    print("\n[OK] Component tests completed!")


if __name__ == "__main__":
    try:
        # Test components separately first
        test_components_separately()

        # Test full extraction
        print("\n\n")
        wiki_data = test_full_wikipedia_extraction()

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED! [OK]")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n[FAILED] TEST FAILED: {e}")
        sys.exit(1)
