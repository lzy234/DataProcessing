"""Test the fixed Wikipedia extractor."""
import sys
from pathlib import Path

# Fix Windows console encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.wikipedia_extractor import WikipediaExtractor


def test_wikipedia_extractor():
    """Test Wikipedia extractor with real names from the dataset."""
    print("=" * 80)
    print("Testing Fixed Wikipedia Extractor (MediaWiki API)")
    print("=" * 80)

    test_cases = [
        "Donald Trump",
        "J.D. Vance",
        "Marco Rubio",
        "Pete Hegseth",
        "Tulsi Gabbard"
    ]

    extractor = WikipediaExtractor()
    success_count = 0
    has_birthdate_count = 0
    has_education_count = 0

    for name in test_cases:
        print(f"\n{'=' * 80}")
        print(f"Testing: {name}")
        print('=' * 80)

        try:
            data = extractor.fetch_person_data(name)

            if data:
                success_count += 1
                print(f"✓ SUCCESS")
                print(f"  Title: {data.get('wikipedia_title')}")
                print(f"  URL: {data.get('url')}")
                print(f"  Birth Date: {data.get('birth_date') or 'Not found'}")
                print(f"  Education: {data.get('education') or 'Not found'}")
                print(f"  Extract (first 150 chars):")
                print(f"    {data.get('extract', '')[:150]}...")

                if data.get('birth_date'):
                    has_birthdate_count += 1
                if data.get('education'):
                    has_education_count += 1
            else:
                print(f"✗ FAILED: No data found")

        except Exception as e:
            print(f"✗ ERROR: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(test_cases)}")
    print(f"Successful: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    print(f"With birth date: {has_birthdate_count}/{success_count} ({has_birthdate_count/success_count*100:.1f}%)")
    print(f"With education: {has_education_count}/{success_count} ({has_education_count/success_count*100:.1f}%)")

    if success_count == len(test_cases):
        print("\n✓ ALL TESTS PASSED - Wikipedia extractor is working!")
        return True
    else:
        print(f"\n✗ {len(test_cases) - success_count} TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = test_wikipedia_extractor()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
