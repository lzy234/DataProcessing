"""Check what data is available in Wikipedia cache."""
import json
from pathlib import Path

# Load Wikipedia cache
cache_file = Path("d:/Project/DataProcessing/data/intermediate/wikipedia_cache.json")
with open(cache_file, 'r', encoding='utf-8') as f:
    wiki_data = json.load(f)

# Check a few people
test_names = ["Donald J. Trump", "J.D. Vance", "Tulsi Gabbard"]

for name in test_names:
    person = wiki_data.get(name)
    if person:
        print(f"\n{'='*60}")
        print(f"Name: {name}")
        print(f"Birth date: {person.get('birth_date', 'N/A')}")
        print(f"Has chunks: {len(person.get('chunks', []))} chunks")

        # Check if party info is in extract
        extract = person.get('extract', '')
        if 'Republican' in extract or 'Democratic' in extract or 'Democrat' in extract:
            print("Party info found in extract!")
            # Find the party mention
            for line in extract.split('\n')[:20]:
                if 'Republican' in line or 'Democratic' in line or 'Democrat' in line:
                    print(f"  -> {line.strip()}")

        # Check chunks for party info
        chunks = person.get('chunks', [])
        for i, chunk in enumerate(chunks[:5]):
            text = chunk['text']
            if 'Republican' in text or 'Democratic' in text or 'Democrat' in text or 'Party' in text:
                print(f"\nChunk {i} ({chunk['section']}):")
                # Print lines with party mentions
                for line in text.split('\n'):
                    if 'Republican' in line or 'Democratic' in line or 'Democrat' in line or 'Party' in line:
                        print(f"  -> {line.strip()[:100]}")
