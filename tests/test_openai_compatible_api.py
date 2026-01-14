"""Test OpenAI-compatible API endpoint."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from src.config.settings import Settings


def test_openai_compatible_api():
    """Test if the OpenAI-compatible API endpoint is working."""
    print("=" * 80)
    print("TESTING OPENAI-COMPATIBLE API ENDPOINT")
    print("=" * 80)

    # Check configuration
    if not Settings.ANTHROPIC_API_KEY:
        print("\n[FAIL] API key not found")
        return False

    if not Settings.ANTHROPIC_BASE_URL:
        print("\n[FAIL] ANTHROPIC_BASE_URL not set")
        print("Please set it in config/.env")
        return False

    masked_key = Settings.ANTHROPIC_API_KEY[:10] + "..." + Settings.ANTHROPIC_API_KEY[-4:]
    print(f"\n[OK] API key found: {masked_key}")
    print(f"[OK] Base URL: {Settings.ANTHROPIC_BASE_URL}")

    # Initialize OpenAI client with custom endpoint
    try:
        print("\n[TEST] Initializing OpenAI client with custom endpoint...")
        client = OpenAI(
            api_key=Settings.ANTHROPIC_API_KEY,
            base_url=Settings.ANTHROPIC_BASE_URL + "/v1",  # Add /v1 for OpenAI compatibility
            timeout=120.0  # Increase timeout to 120 seconds
        )
        print("[OK] Client initialized successfully")
    except Exception as e:
        print(f"[FAIL] Failed to initialize client: {e}")
        return False

    # List available models
    try:
        print("\n[TEST] Listing available models...")
        models = client.models.list()
        claude_models = [m.id for m in models.data if 'claude' in m.id.lower()]
        print(f"[OK] Found {len(claude_models)} Claude models:")
        for model in claude_models[:5]:
            print(f"  - {model}")
        if len(claude_models) > 5:
            print(f"  ... and {len(claude_models) - 5} more")
    except Exception as e:
        print(f"[WARN] Could not list models: {e}")

    # Test API call with Sonnet 4.5
    try:
        print("\n[TEST] Making test API call with claude-sonnet-4-5-20250929...")
        print("(This will consume a small amount of tokens)")

        response = client.chat.completions.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with just 'API test successful' and nothing else."
                }
            ]
        )

        response_text = response.choices[0].message.content
        print(f"[OK] API call successful!")
        print(f"Response: {response_text}")

        # Show usage stats
        print(f"\nToken usage:")
        print(f"  Prompt tokens: {response.usage.prompt_tokens}")
        print(f"  Completion tokens: {response.usage.completion_tokens}")
        print(f"  Total tokens: {response.usage.total_tokens}")

        print("\n" + "=" * 80)
        print("[OK] API ENDPOINT IS WORKING!")
        print("=" * 80)
        print("\nNote: This endpoint uses OpenAI-compatible API format.")
        print("You'll need to adapt the code to use OpenAI SDK instead of Anthropic SDK.")

        return True

    except Exception as e:
        print(f"\n[FAIL] API call failed: {e}")
        print(f"\nError type: {type(e).__name__}")

        if hasattr(e, 'response'):
            print(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")

        return False


if __name__ == "__main__":
    try:
        success = test_openai_compatible_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
