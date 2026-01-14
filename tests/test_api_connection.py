"""Test Deepseek API connection."""
from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables and OVERRIDE system env vars
config_dir = Path(__file__).parent / "config"
env_file = config_dir / ".env"
load_dotenv(env_file, override=True)  # Add override=True to override system env vars

api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_BASE_URL")

print(f"API Key: {api_key[:20]}...")
print(f"Base URL: {base_url}")

try:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url + "/v1",
        timeout=120.0
    )

    print("\nTesting API connection...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=100,
        temperature=0.1,
        messages=[{
            "role": "user",
            "content": "Say 'Hello World' in JSON format: {\"message\": \"...\"}"
        }]
    )

    response_text = response.choices[0].message.content.strip()
    print(f"\nAPI Response: {response_text}")
    print("\n[SUCCESS] API connection successful!")

except Exception as e:
    print(f"\n[FAILED] API connection failed: {e}")
