"""Test the enhanced AI functionality for extracting gender, party, and dateOfBirth."""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.ai_enhancer import ClaudeAIEnhancer
from src.config.settings import Settings

# Load Wikipedia cache
cache_file = Settings.WIKIPEDIA_CACHE_FILE
with open(cache_file, 'r', encoding='utf-8') as f:
    wiki_data = json.load(f)

# Test with a few people
test_people = [
    {"name": "Donald J. Trump"},
    {"name": "J.D. Vance"},
    {"name": "Tulsi Gabbard"}
]

print("Testing enhanced AI functionality...")
print("=" * 80)

enhancer = ClaudeAIEnhancer()

for person in test_people:
    name = person['name']
    wiki = wiki_data.get(name)

    if not wiki:
        print(f"\n{name}: No Wikipedia data found")
        continue

    print(f"\n{name}:")
    print(f"  Wikipedia birth_date: {wiki.get('birth_date', 'N/A')}")

    # Test basic info extraction
    try:
        result = enhancer._enhance_basic_info(person, wiki)
        print(f"  Extracted dateOfBirth: {result.get('dateOfBirth', 'N/A')}")
        print(f"  Extracted gender: {result.get('gender', 'N/A')}")
        print(f"  Extracted party: {result.get('party', 'N/A')}")
        print(f"  Sources: {len(result.get('sources', []))}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 80)
print("Test completed!")
