"""Debug what Wikipedia text is being sent to AI."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.ai_enhancer import ClaudeAIEnhancer
from src.config.settings import Settings

# Load Wikipedia cache
cache_file = Settings.WIKIPEDIA_CACHE_FILE
with open(cache_file, 'r', encoding='utf-8') as f:
    wiki_data = json.load(f)

# Test with Trump
enhancer = ClaudeAIEnhancer()

for name in ["Donald J. Trump", "Tulsi Gabbard"]:
    wiki = wiki_data.get(name)
    if wiki:
        print(f"\n{'='*80}")
        print(f"Person: {name}")
        print(f"{'='*80}")

        # Get the text that would be sent to AI
        wiki_extract = enhancer._get_relevant_text(wiki, max_chars=3000)

        print(f"\nLength: {len(wiki_extract)} chars")

        # Save to file to avoid encoding issues
        output_file = Path(__file__).parent / f"wiki_extract_{name.replace(' ', '_')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(wiki_extract)
        print(f"Saved extract to: {output_file}")

        # Check for party mentions
        has_republican = 'Republican' in wiki_extract
        has_democratic = 'Democratic' in wiki_extract or 'Democrat' in wiki_extract
        has_male = ' he ' in wiki_extract.lower() or ' his ' in wiki_extract.lower()
        has_female = ' she ' in wiki_extract.lower() or ' her ' in wiki_extract.lower()

        print(f"Republican found: {has_republican}")
        print(f"Democratic/Democrat found: {has_democratic}")
        print(f"Male pronouns found: {has_male}")
        print(f"Female pronouns found: {has_female}")
