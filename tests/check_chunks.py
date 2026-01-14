"""Check the structure of Wikipedia chunks."""
import json
from pathlib import Path

cache_file = Path("d:/Project/DataProcessing/data/intermediate/wikipedia_cache.json")
with open(cache_file, 'r', encoding='utf-8') as f:
    wiki_data = json.load(f)

for name in ["Donald J. Trump", "Tulsi Gabbard"]:
    person = wiki_data.get(name)
    if person:
        print(f"\n{'='*80}")
        print(f"Person: {name}")
        print(f"Total chunks: {len(person.get('chunks', []))}")

        chunks = person.get('chunks', [])
        for i, chunk in enumerate(chunks[:5]):
            print(f"\nChunk {i}:")
            print(f"  Section: {chunk['section']}")
            print(f"  Is intro: {chunk.get('is_intro', False)}")
            print(f"  Length: {len(chunk['text'])} chars")
            print(f"  First 200 chars: {chunk['text'][:200]}")
