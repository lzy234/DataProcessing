"""Test script to verify Anthropic API key is working."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from anthropic import Anthropic
from src.config.settings import Settings


def test_api_key():
    """Test if the Anthropic API key is valid and working."""
    print("=" * 80)
    print("TESTING ANTHROPIC API KEY")
    print("=" * 80)

    # Check if API key is set
    if not Settings.ANTHROPIC_API_KEY:
        print("\n[FAIL] ANTHROPIC_API_KEY not found in environment")
        print("\nPlease create config/.env file with:")
        print("ANTHROPIC_API_KEY=sk-ant-your-api-key-here")
        return False

    # Mask API key for display
    masked_key = Settings.ANTHROPIC_API_KEY[:10] + "..." + Settings.ANTHROPIC_API_KEY[-4:]
    print(f"\n[OK] API key found: {masked_key}")

    # Try to initialize client
    try:
        print("\n[TEST] Initializing Anthropic client...")
        client_kwargs = {"api_key": Settings.ANTHROPIC_API_KEY}
        if Settings.ANTHROPIC_BASE_URL:
            client_kwargs["base_url"] = Settings.ANTHROPIC_BASE_URL
            print(f"[INFO] Using custom base URL: {Settings.ANTHROPIC_BASE_URL}")

        client = Anthropic(**client_kwargs)
        print("[OK] Client initialized successfully")
    except Exception as e:
        print(f"[FAIL] Failed to initialize client: {e}")
        return False

    # Try a simple API call
    try:
        print("\n[TEST] Making test API call...")
        print("(This will consume a small amount of tokens, approximately $0.001)")

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            timeout=60.0,  # Increase timeout to 60 seconds
            messages=[
                {
                    "role": "user",
                    "content": "Reply with just 'API test successful' and nothing else."
                }
            ]
        )

        response_text = response.content[0].text
        print(f"[OK] API call successful!")
        print(f"Response: {response_text}")

        # Show usage stats
        print(f"\nToken usage:")
        print(f"  Input tokens: {response.usage.input_tokens}")
        print(f"  Output tokens: {response.usage.output_tokens}")

        estimated_cost = (response.usage.input_tokens * 0.003 + response.usage.output_tokens * 0.015) / 1000
        print(f"  Estimated cost: ${estimated_cost:.6f}")

        print("\n" + "=" * 80)
        print("[OK] API KEY IS VALID AND WORKING!")
        print("=" * 80)
        print("\nYou can now run the full pipeline:")
        print("  python src/main.py")

        return True

    except Exception as e:
        print(f"\n[FAIL] API call failed: {e}")
        print(f"\nError type: {type(e).__name__}")

        # More detailed error information
        if hasattr(e, 'response'):
            print(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")
            print(f"Response text: {getattr(e.response, 'text', 'N/A')[:200]}")

        print("\nPossible reasons:")
        print("1. Invalid API key or custom endpoint configuration")
        print("2. API key doesn't have access to the model")
        print("3. Network connection issue or endpoint timeout")
        print("4. Rate limit exceeded")
        print("5. Custom base URL may not be compatible with Anthropic SDK")

        print("\nTroubleshooting:")
        print("- Verify the custom endpoint supports Anthropic API format")
        print("- Check if the endpoint requires /v1 prefix")
        print("- Try removing ANTHROPIC_BASE_URL to test with official API")

        return False


if __name__ == "__main__":
    try:
        success = test_api_key()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
