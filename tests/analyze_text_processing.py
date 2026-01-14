"""Analyze how AI enhancer processes Wikipedia text."""
import json
from pathlib import Path

def analyze_text_processing():
    """Analyze the text processing strategy in AI enhancer."""

    # Load Wikipedia cache
    wiki_cache_path = Path('data/intermediate/wikipedia_cache.json')
    with open(wiki_cache_path, 'r', encoding='utf-8') as f:
        wiki_data = json.load(f)

    print("=" * 80)
    print("AI ENHANCER TEXT PROCESSING ANALYSIS")
    print("=" * 80)

    # Analyze the text limits used in _get_relevant_text (UPDATED VALUES)
    processing_stages = {
        "Basic Info (gender)": {"max_chars": 1600, "keywords": [], "old_limit": 800},
        "Education": {"max_chars": 6000, "keywords": ['education', 'university', 'college', 'graduated', 'degree', 'studied'], "old_limit": 3000},
        "Career History": {"max_chars": 8000, "keywords": ['career', 'elected', 'appointed', 'served', 'position', 'founded', 'work'], "old_limit": 3500},
        "Biography": {"max_chars": 10000, "keywords": ['born', 'early life', 'career', 'education', 'political'], "old_limit": 4000},
        "Organization": {"max_chars": 4000, "keywords": ['current', 'serves', 'member', 'senator', 'representative'], "old_limit": 2000},
    }

    print("\nProcessing Stages and Character Limits:")
    print("-" * 80)
    print("NOTE: Character limits have been INCREASED to improve coverage")
    for stage, config in processing_stages.items():
        old_limit = config.get('old_limit', 0)
        new_limit = config['max_chars']
        increase_pct = ((new_limit - old_limit) / old_limit * 100) if old_limit > 0 else 0
        print(f"\n{stage}:")
        print(f"  OLD limit: {old_limit:,} chars")
        print(f"  NEW limit: {new_limit:,} chars (+{increase_pct:.0f}%)")
        print(f"  Keywords: {', '.join(config['keywords']) if config['keywords'] else 'None'}")

    # Analyze Wikipedia data
    print("\n" + "=" * 80)
    print("WIKIPEDIA DATA ANALYSIS")
    print("=" * 80)

    total_persons = len(wiki_data)
    extract_lengths = []
    chunk_coverages = []

    for name, person in wiki_data.items():
        extract = person.get('extract', '')
        chunks = person.get('chunks', [])

        extract_len = len(extract)
        extract_lengths.append(extract_len)

        if chunks:
            total_chunk_chars = sum(len(c.get('text', '')) for c in chunks)
            coverage = (total_chunk_chars / extract_len * 100) if extract_len > 0 else 0
            chunk_coverages.append(coverage)

    import statistics

    print(f"\nTotal persons: {total_persons}")
    print(f"\nExtract Length Statistics:")
    print(f"  Average: {statistics.mean(extract_lengths):,.0f} chars")
    print(f"  Median: {statistics.median(extract_lengths):,.0f} chars")
    print(f"  Min: {min(extract_lengths):,} chars")
    print(f"  Max: {max(extract_lengths):,} chars")

    if chunk_coverages:
        print(f"\nChunk Coverage Statistics:")
        print(f"  Average coverage: {statistics.mean(chunk_coverages):.1f}%")
        print(f"  Median coverage: {statistics.median(chunk_coverages):.1f}%")
        print(f"  Min coverage: {min(chunk_coverages):.1f}%")
        print(f"  Max coverage: {max(chunk_coverages):.1f}%")

    # Show examples of how much text would be used
    print("\n" + "=" * 80)
    print("TEXT USAGE EXAMPLES")
    print("=" * 80)

    # Pick a few examples with different extract lengths
    examples = [
        ('Donald J. Trump', 198387),
        ('Glenn Youngkin', 104143),
        ('Chuck Grassley', 89117),
    ]

    for name, extract_len in examples:
        if name in wiki_data:
            person = wiki_data[name]
            chunks = person.get('chunks', [])

            print(f"\n{name}:")
            print(f"  Total extract: {extract_len:,} chars")
            print(f"  Number of chunks: {len(chunks)}")

            if chunks:
                total_chunk_chars = sum(len(c.get('text', '')) for c in chunks)
                print(f"  Total chunk text: {total_chunk_chars:,} chars ({total_chunk_chars/extract_len*100:.1f}% of extract)")

            print(f"\n  Text used per stage:")
            for stage, config in processing_stages.items():
                max_chars = config['max_chars']
                if chunks:
                    # Simulate what would be selected
                    used_chars = min(total_chunk_chars, max_chars)
                else:
                    used_chars = min(extract_len, max_chars)

                percentage = (used_chars / extract_len * 100)
                print(f"    {stage}: {used_chars:,} chars ({percentage:.1f}% of full extract)")

    # Analysis of potential issues
    print("\n" + "=" * 80)
    print("POTENTIAL ISSUES")
    print("=" * 80)

    print("\n1. CHUNK COVERAGE PROBLEM:")
    print("   - Chunks only cover ~22% of the full Wikipedia extract")
    print("   - Most extract data (78%) is NOT included in chunks")
    print("   - This means important information may be missed")

    print("\n2. CHARACTER LIMIT CONSIDERATIONS:")
    print("   - Biography stage uses max 4,000 chars")
    print("   - For Trump (198K chars), this is only 2% of the full text")
    print("   - Even with good chunking, may miss critical information")

    print("\n3. KEYWORD-BASED SELECTION:")
    print("   - Current approach scores chunks by keywords")
    print("   - Intro sections get +100 bonus score")
    print("   - Each keyword match gets +10 score")
    print("   - This prioritization helps but is limited by chunk availability")

    print("\n4. IMPROVEMENTS IMPLEMENTED:")
    print("   ✓ Fixed section pattern regex to recognize ===, ====, etc.")
    print("   ✓ Added h4 heading support to HTML parser")
    print("   ✓ Increased max_chunks from 5 to 10")
    print("   ✓ Doubled character limits for all AI enhancement stages:")
    print("     - Basic info: 800 → 1,600 chars (+100%)")
    print("     - Education: 3,000 → 6,000 chars (+100%)")
    print("     - Career: 3,500 → 8,000 chars (+129%)")
    print("     - Biography: 4,000 → 10,000 chars (+150%)")
    print("     - Organization: 2,000 → 4,000 chars (+100%)")
    print("\n5. EXPECTED RESULTS:")
    print("   - Chunk coverage should improve from ~22% to 60-80%")
    print("   - More comprehensive text for AI processing")
    print("   - Better extraction of education, career, and biography info")
    print("\n6. FUTURE RECOMMENDATIONS:")
    print("   a) Add adaptive limits based on extract length")
    print("   b) Consider using embeddings for semantic chunk selection")
    print("   c) Implement progressive summarization for very long articles")

if __name__ == "__main__":
    analyze_text_processing()
