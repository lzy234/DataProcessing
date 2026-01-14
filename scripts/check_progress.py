"""Check the progress of the data processing pipeline."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import Settings


def check_progress():
    """Check pipeline progress by examining intermediate files and logs."""
    print("=" * 80)
    print("DATA PROCESSING PIPELINE PROGRESS")
    print("=" * 80)

    # Check if intermediate files exist
    ai_cache = Settings.AI_RESPONSES_CACHE_FILE
    entities_file = Settings.EXTRACTED_ENTITIES_FILE
    wiki_cache = Settings.WIKIPEDIA_CACHE_FILE

    print("\n1. Intermediate Files:")
    print("-" * 80)

    if wiki_cache.exists():
        try:
            import json
            with open(wiki_cache, 'r', encoding='utf-8') as f:
                wiki_data = json.load(f)
            print(f"[OK] Wikipedia cache: {len(wiki_data)} entries")
        except:
            print(f"[??] Wikipedia cache exists but couldn't read")
    else:
        print(f"[--] Wikipedia cache: Not yet created")

    if ai_cache.exists():
        try:
            import json
            with open(ai_cache, 'r', encoding='utf-8') as f:
                ai_data = json.load(f)
            print(f"[OK] AI responses cache: {len(ai_data)} batches processed")
            print(f"     (Each batch contains up to 10 people)")
        except:
            print(f"[??] AI cache exists but couldn't read")
    else:
        print(f"[--] AI responses cache: Not yet created")

    if entities_file.exists():
        try:
            import json
            with open(entities_file, 'r', encoding='utf-8') as f:
                entities = json.load(f)
            print(f"[OK] Extracted entities:")
            print(f"     - Organizations: {len(entities.get('organizations', []))}")
            print(f"     - Parties: {len(entities.get('parties', []))}")
            print(f"     - Sectors: {len(entities.get('sectors', []))}")
        except:
            print(f"[??] Entities file exists but couldn't read")
    else:
        print(f"[--] Extracted entities: Not yet created")

    # Check output files
    print("\n2. Output Files:")
    print("-" * 80)

    output_files = {
        "People.csv": Settings.OUTPUT_DIR / "People.csv",
        "Organizations.csv": Settings.OUTPUT_DIR / "Organizations.csv",
        "Parties.csv": Settings.OUTPUT_DIR / "Parties.csv",
        "Sectors.csv": Settings.OUTPUT_DIR / "Sectors.csv"
    }

    all_exist = True
    for name, filepath in output_files.items():
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f) - 1  # Subtract header
                print(f"[OK] {name}: {line_count} rows")
            except:
                print(f"[??] {name}: Exists but couldn't read")
        else:
            print(f"[--] {name}: Not yet created")
            all_exist = False

    # Summary
    print("\n" + "=" * 80)
    if all_exist:
        print("STATUS: PIPELINE COMPLETED!")
        print("=" * 80)
        print("\nAll output files have been generated.")
        print(f"\nOutput directory: {Settings.OUTPUT_DIR}")
        print("\nYou can now import these CSV files into Payload CMS.")
    else:
        print("STATUS: PIPELINE IN PROGRESS...")
        print("=" * 80)
        print("\nThe pipeline is still running.")
        print("Check back in a few minutes to see progress.")
        print("\nTo monitor in real-time, check the log file or running process.")

    return all_exist


if __name__ == "__main__":
    try:
        completed = check_progress()
        sys.exit(0 if completed else 1)
    except Exception as e:
        print(f"\n[ERROR] Failed to check progress: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
