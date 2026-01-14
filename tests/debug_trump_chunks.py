"""Debug Trump chunk selection."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import Settings

cache_file = Settings.WIKIPEDIA_CACHE_FILE
with open(cache_file, 'r', encoding='utf-8') as f:
    wiki_data = json.load(f)

wiki = wiki_data["Donald J. Trump"]
chunks = wiki['chunks']

print("Filtering chunks...")
filtered_chunks = []
for i, chunk in enumerate(chunks):
    text = chunk['text']
    lines = text.strip().split('\n')
    short_lines = sum(1 for line in lines if len(line.strip()) < 50)
    long_content = any('born' in text.lower() or len(line) > 100 for line in lines)

    passes = long_content or (len(lines) - short_lines) > 3

    print(f"Chunk {i}: section={chunk['section']}, passes={passes}, long_content={long_content}, lines={len(lines)}, short={short_lines}")

    if passes:
        filtered_chunks.append(chunk)

print(f"\nFiltered: {len(filtered_chunks)} chunks")

# Score chunks
print("\nScoring chunks...")
scored_chunks = []
for i, chunk in enumerate(filtered_chunks):
    score = chunk.get('is_intro', False) * 100
    text_lower = chunk['text'].lower()

    if 'born' in text_lower:
        score += 50
    if ' is an american' in text_lower or ' is a ' in text_lower:
        score += 30

    section = chunk['section']
    has_born = 'born' in text_lower
    has_republican = 'Republican' in chunk['text']

    print(f"  {section}: score={score}, is_intro={chunk.get('is_intro')}, has_born={has_born}, has_Republican={has_republican}")

    scored_chunks.append((score, chunk))

scored_chunks.sort(reverse=True, key=lambda x: x[0])

print("\nSorted chunks:")
for score, chunk in scored_chunks[:5]:
    print(f"  score={score}, section={chunk['section']}, length={len(chunk['text'])}")
