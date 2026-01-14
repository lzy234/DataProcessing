"""Analyze missing data in the processing pipeline."""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_missing_data():
    """Analyze what data is missing and why."""

    # Load final output
    output_file = Path('data/output/enhanced_people_data.json')
    if not output_file.exists():
        print("No output file found")
        return

    with open(output_file, 'r', encoding='utf-8') as f:
        people = json.load(f)

    print(f"Total people: {len(people)}")
    print("\n" + "="*80)

    # Analyze missing fields
    missing_stats = {
        'gender': 0,
        'dateOfBirth': 0,
        'education': 0,
        'careerHistory': 0,
        'bio': 0,
        'organization': 0
    }

    examples = {
        'gender': [],
        'dateOfBirth': [],
        'education': [],
    }

    for person in people:
        name = person.get('name', 'Unknown')

        # Check each field
        if not person.get('gender') or person.get('gender') == '':
            missing_stats['gender'] += 1
            if len(examples['gender']) < 5:
                examples['gender'].append(name)

        if not person.get('dateOfBirth'):
            missing_stats['dateOfBirth'] += 1
            if len(examples['dateOfBirth']) < 5:
                examples['dateOfBirth'].append(name)

        if not person.get('education') or person.get('education') == '':
            missing_stats['education'] += 1
            if len(examples['education']) < 5:
                examples['education'].append(name)

        if not person.get('careerHistory') or person.get('careerHistory') == '':
            missing_stats['careerHistory'] += 1

        if not person.get('bio') or person.get('bio') == '':
            missing_stats['bio'] += 1

        if not person.get('organization') or person.get('organization') == '':
            missing_stats['organization'] += 1

    # Print statistics
    print("\nMISSING DATA STATISTICS:")
    print("-" * 80)
    for field, count in missing_stats.items():
        percentage = (count / len(people)) * 100
        print(f"{field:20s}: {count:3d}/{len(people)} missing ({percentage:.1f}%)")

    # Print examples
    print("\n" + "="*80)
    print("\nEXAMPLES OF MISSING DATA:")
    print("-" * 80)

    for field, names in examples.items():
        if names:
            print(f"\n{field} missing for:")
            for name in names:
                print(f"  - {name}")

    # Analyze specific cases
    print("\n" + "="*80)
    print("\nDETAILED ANALYSIS OF MISSING GENDER:")
    print("-" * 80)

    # Load Wikipedia data to check what was available
    wiki_file = Path('data/intermediate/wikipedia_data.json')
    if wiki_file.exists():
        with open(wiki_file, 'r', encoding='utf-8') as f:
            wiki_data = json.load(f)

        for name in examples['gender'][:3]:
            print(f"\n{name}:")

            # Find in output
            person_data = next((p for p in people if p.get('name') == name), None)
            if person_data:
                print(f"  Current gender: '{person_data.get('gender', '')}'")
                print(f"  Has bio: {bool(person_data.get('bio'))}")
                print(f"  Has sources: {len(person_data.get('sources', []))}")

            # Check Wikipedia
            wiki = wiki_data.get(name)
            if wiki:
                extract = wiki.get('extract', '')
                print(f"  Wikipedia extract length: {len(extract)} chars")
                print(f"  Wikipedia chunks: {len(wiki.get('chunks', []))}")

                # Check if gender keywords exist in Wikipedia
                gender_keywords = ['he ', 'his ', 'him ', 'she ', 'her ', 'hers ']
                found_keywords = [kw for kw in gender_keywords if kw in extract.lower()[:2000]]
                print(f"  Gender keywords in first 2000 chars: {found_keywords[:3]}")

                # Show first 500 chars
                print(f"\n  Wikipedia excerpt (first 500 chars):")
                print(f"  {extract[:500]}")
            else:
                print("  No Wikipedia data found")

    # Check AI cache
    print("\n" + "="*80)
    print("\nAI CACHE CHECK:")
    print("-" * 80)

    cache_file = Path('data/cache/ai_responses_cache.json')
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache = json.load(f)

        print(f"Total cached responses: {len(cache)}")

        # Check for gender entries
        gender_entries = [k for k in cache.keys() if '_basic' in k]
        print(f"Basic info (gender) cached entries: {len(gender_entries)}")

        # Show sample
        for name in examples['gender'][:2]:
            cache_key = f"{name}_basic"
            if cache_key in cache:
                cached_data = cache[cache_key]
                print(f"\n{name} cached basic info:")
                print(f"  Gender: '{cached_data.get('gender', '')}'")
                print(f"  Date of birth: {cached_data.get('dateOfBirth')}")

if __name__ == '__main__':
    analyze_missing_data()
