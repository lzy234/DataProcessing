"""Analyze why gender data is missing."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_gender_issue():
    """Analyze the gender extraction issue."""

    # Load Wikipedia data
    wiki_file = Path('data/intermediate/wikipedia_data.json')
    with open(wiki_file, 'r', encoding='utf-8') as f:
        wiki_data = json.load(f)

    # Check cache
    cache_file = Path('data/cache/ai_responses_cache.json')
    cache = {}
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        print(f"AI Cache entries: {len(cache)}")
    else:
        print("No AI cache found!")

    # Sample people with missing gender
    test_names = ['Donald J. Trump', 'Susie Wiles', 'Tulsi Gabbard', 'Marco Rubio']

    for name in test_names:
        print(f"\n{'='*80}")
        print(f"ANALYZING: {name}")
        print('='*80)

        # Check Wikipedia data
        if name in wiki_data:
            wiki = wiki_data[name]
            extract = wiki.get('extract', '')
            print(f"\n1. Wikipedia Data:")
            print(f"   Extract length: {len(extract)} chars")
            print(f"   Chunks available: {len(wiki.get('chunks', []))}")

            # Check for gender keywords in first 1000 chars
            first_part = extract[:1000].lower()
            gender_indicators = {
                'male': ['he ', ' his ', ' him ', 'himself'],
                'female': ['she ', ' her ', 'herself', 'hers ']
            }

            for gender, keywords in gender_indicators.items():
                found = [kw for kw in keywords if kw in first_part]
                if found:
                    print(f"   → {gender.upper()} indicators found: {found[:3]}")

            # Show excerpt
            print(f"\n   First 400 chars of Wikipedia:")
            print(f"   {extract[:400]}")

        else:
            print(f"\n1. Wikipedia Data: NOT FOUND")

        # Check AI cache
        cache_key = f"{name}_basic"
        if cache_key in cache:
            cached = cache[cache_key]
            print(f"\n2. AI Cache (_basic):")
            print(f"   Gender: '{cached.get('gender', '')}'")
            print(f"   Date of Birth: {cached.get('dateOfBirth')}")
        else:
            print(f"\n2. AI Cache: NOT FOUND (key: {cache_key})")

if __name__ == '__main__':
    analyze_gender_issue()
