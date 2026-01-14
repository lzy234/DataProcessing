"""Test AI enhancer with actual API call."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.processors.ai_enhancer import ClaudeAIEnhancer
from src.config.settings import Settings
from src.utils.logger import logger


def test_ai_enhancer_with_api():
    """Test AI enhancer with a real API call."""
    print("=" * 80)
    print("TESTING AI ENHANCER WITH OPENAI-COMPATIBLE API")
    print("=" * 80)

    # Check configuration
    if not Settings.ANTHROPIC_API_KEY:
        print("\n[FAIL] ANTHROPIC_API_KEY not set")
        return False

    if not Settings.ANTHROPIC_BASE_URL:
        print("\n[FAIL] ANTHROPIC_BASE_URL not set")
        return False

    masked_key = Settings.ANTHROPIC_API_KEY[:10] + "..." + Settings.ANTHROPIC_API_KEY[-4:]
    print(f"\n[OK] API key found: {masked_key}")
    print(f"[OK] Base URL: {Settings.ANTHROPIC_BASE_URL}")

    # Sample test person (smaller than full dataset for quick testing)
    test_person = {
        'name': 'Nancy Pelosi',
        'ChineseName': '南希·佩洛西',
        'currentRole': 'Former Speaker of the House (D-CA)',
        'organization_text': '美国众议院 (U.S. House of Representatives)',
        'bio_chinese': '美国民主党政治家,曾任美国众议院议长,是美国历史上首位女性众议院议长。她在2007年至2011年以及2019年至2023年两度担任众议院议长。佩洛西在推动奥巴马医改、应对金融危机等重大政策议题上发挥了关键作用。'
    }

    try:
        print("\n[TEST] Initializing AI enhancer...")
        enhancer = ClaudeAIEnhancer()
        print("[OK] AI enhancer initialized")

        print("\n[TEST] Calling AI API to enhance person data...")
        print("(This will consume tokens - approximately $0.01-0.02)")
        print("(May take 30-60 seconds due to endpoint response time)")

        result = enhancer.enhance_single(test_person)

        print("\n[OK] API call successful!")
        print("\nEnhanced data:")
        print(f"  Name: {result.get('name', 'N/A')}")
        print(f"  Date of Birth: {result.get('dateOfBirth', 'N/A')}")
        print(f"  Gender: {result.get('gender', 'N/A')}")
        print(f"  Education: {result.get('education', 'N/A')[:100]}...")
        print(f"  Career History: {result.get('careerHistory', 'N/A')[:100]}...")
        print(f"  Bio (first 200 chars): {result.get('bio', 'N/A')[:200]}...")
        print(f"  Sources: {len(result.get('sources', []))} sources")

        print("\n" + "=" * 80)
        print("[OK] AI ENHANCER IS WORKING WITH OPENAI-COMPATIBLE API!")
        print("=" * 80)

        print("\nYou can now run the full pipeline:")
        print("  python src/main.py")

        return True

    except Exception as e:
        print(f"\n[FAIL] AI enhancer test failed: {e}")
        print(f"\nError type: {type(e).__name__}")

        import traceback
        traceback.print_exc()

        print("\nPossible reasons:")
        print("1. API endpoint configuration issue")
        print("2. Network timeout or slow response")
        print("3. API response format changed")
        print("4. Rate limit exceeded")

        return False


if __name__ == "__main__":
    try:
        success = test_ai_enhancer_with_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
