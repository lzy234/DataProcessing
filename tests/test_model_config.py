"""Test script to verify AI model configuration."""
from src.config.settings import Settings
from src.processors.ai_enhancer import ClaudeAIEnhancer
from src.utils.logger import logger


def test_model_configuration():
    """Test that the model is correctly configured."""
    print("=" * 80)
    print("AI MODEL CONFIGURATION TEST")
    print("=" * 80)

    # Display current settings
    print("\nCurrent Configuration:")
    print("-" * 80)
    print(f"API Endpoint: {Settings.ANTHROPIC_BASE_URL}")
    print(f"API Key: {Settings.ANTHROPIC_API_KEY[:15]}..." if Settings.ANTHROPIC_API_KEY else "Not Set")
    print(f"AI Model: {Settings.AI_MODEL}")
    print(f"Max Requests/Min: {Settings.MAX_CLAUDE_REQUESTS_PER_MINUTE}")

    # Try to initialize the enhancer
    print("\n" + "=" * 80)
    print("INITIALIZING AI ENHANCER")
    print("=" * 80)

    try:
        enhancer = ClaudeAIEnhancer()
        print(f"\n[SUCCESS] AI Enhancer initialized with model '{enhancer.model}'")
        print(f"   Cache loaded: {len(enhancer.cache)} entries")

    except Exception as e:
        print(f"\n[FAILED] Could not initialize AI Enhancer")
        print(f"   Error: {e}")
        return False

    # Test model information
    print("\n" + "=" * 80)
    print("MODEL INFORMATION")
    print("=" * 80)

    model_info = {
        "deepseek-chat": {
            "name": "Deepseek Chat",
            "type": "General Purpose",
            "strengths": "Fast, cost-effective",
            "best_for": "Simple extraction tasks"
        },
        "deepseek-reasoner": {
            "name": "Deepseek Reasoner",
            "type": "Advanced Reasoning",
            "strengths": "Complex reasoning, better data extraction",
            "best_for": "Biography generation, complex text analysis"
        },
        "claude-3-5-sonnet-20241022": {
            "name": "Claude 3.5 Sonnet",
            "type": "High Performance",
            "strengths": "Excellent text understanding, large context",
            "best_for": "High-quality content generation"
        }
    }

    current_model = Settings.AI_MODEL
    info = model_info.get(current_model, {
        "name": current_model,
        "type": "Unknown",
        "strengths": "N/A",
        "best_for": "N/A"
    })

    print(f"\nCurrent Model: {current_model}")
    print(f"  Name: {info['name']}")
    print(f"  Type: {info['type']}")
    print(f"  Strengths: {info['strengths']}")
    print(f"  Best For: {info['best_for']}")

    # Recommendations based on system improvements
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS FOR YOUR SYSTEM")
    print("=" * 80)

    print("\nBased on recent improvements (increased context sizes):")
    print("  - Basic Info: 1,600 chars")
    print("  - Education: 6,000 chars")
    print("  - Career: 8,000 chars")
    print("  - Biography: 10,000 chars")
    print("  - Organization: 4,000 chars")

    if current_model == "deepseek-reasoner":
        print("\n[EXCELLENT CHOICE!]")
        print("   'deepseek-reasoner' is optimal for your improved system.")
        print("   It handles long context and complex reasoning very well.")
    elif current_model == "deepseek-chat":
        print("\n[CONSIDER UPGRADING]")
        print("   'deepseek-chat' works, but 'deepseek-reasoner' would be better")
        print("   for handling the increased context sizes (up to 10K chars).")
        print("\n   To upgrade, set in config/.env:")
        print("   AI_MODEL=deepseek-reasoner")
    else:
        print(f"\n[OK] Using: {current_model}")
        print("   Make sure this model can handle long context windows.")

    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = test_model_configuration()
    exit(0 if success else 1)
