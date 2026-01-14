"""Debug which chunks are being selected."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.ai_enhancer import ClaudeAIEnhancer
from src.config.settings import Settings

cache_file = Settings.WIKIPEDIA_CACHE_FILE
with open(cache_file, 'r', encoding='utf-8') as f:
    wiki_data = json.load(f)

enhancer = ClaudeAIEnhancer()

name = "Donald J. Trump"
wiki = wiki_data.get(name)

if wiki:
    chunks = wiki['chunks']
    print(f"Total chunks: {len(chunks)}\n")

    # Check each chunk
    for i, chunk in enumerate(chunks):
        text = chunk['text']
        lines = text.strip().split('\n')
        short_lines = sum(1 for line in lines if len(line.strip()) < 50)
        long_content = any('born' in text.lower() or len(line) > 100 for line in lines)

        print(f"Chunk {i}: {chunk['section']}")
        print(f"  is_intro: {chunk.get('is_intro', False)}")
        print(f"  Length: {len(text)} chars")
        print(f"  Lines: {len(lines)}, Short: {short_lines}, Long content: {long_content}")
        print(f"  Passes filter: {long_content or (len(lines) - short_lines) > 3}")

        # Check for key content
        has_born = 'born' in text.lower()
        has_republican = 'Republican' in text
        has_is_american = ' is an American' in text

        print(f"  Contains 'born': {has_born}")
        print(f"  Contains 'Republican': {has_republican}")
        print(f"  Contains 'is an American': {has_is_american}")

        if i < 5:
            print(f"  Preview: {text[:150]}")
        print()
