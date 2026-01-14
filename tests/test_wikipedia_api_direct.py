"""Test Wikipedia API directly to check what data we get."""
import requests
import json


def test_wikipedia_api():
    """Test different Wikipedia API parameters."""
    api_url = "https://en.wikipedia.org/w/api.php"
    page_title = "Alexandria Ocasio-Cortez"
    headers = {'User-Agent': 'DataProcessingBot/1.0 (Educational Project)'}

    print("=" * 80)
    print("Testing Wikipedia API Parameters")
    print("=" * 80)

    # Test 1: With exintro=False (should get full content)
    print("\n1. Testing with exintro=False (full content):")
    params_full = {
        'action': 'query',
        'prop': 'extracts',
        'exintro': False,  # Get FULL content
        'explaintext': True,
        'titles': page_title,
        'format': 'json'
    }

    response = requests.get(api_url, headers=headers, params=params_full, timeout=30)
    print(f"   Status: {response.status_code}")
    print(f"   Response length: {len(response.text)} chars")
    if response.status_code != 200:
        print(f"   Error: {response.text[:500]}")
        return
    data = response.json()
    pages = data.get('query', {}).get('pages', {})

    if pages:
        page = next(iter(pages.values()))
        extract = page.get('extract', '')
        print(f"   Length: {len(extract)} characters")
        print(f"   Preview: {extract[:200]}...")

        # Save to file
        with open('test_output/wiki_api_full.json', 'w', encoding='utf-8') as f:
            json.dump(page, f, ensure_ascii=False, indent=2)
        print(f"   Saved to: test_output/wiki_api_full.json")

    # Test 2: With exintro=True (intro only)
    print("\n2. Testing with exintro=True (intro only):")
    params_intro = {
        'action': 'query',
        'prop': 'extracts',
        'exintro': True,  # Intro only
        'explaintext': True,
        'titles': page_title,
        'format': 'json'
    }

    response = requests.get(api_url, headers=headers, params=params_intro, timeout=30)
    data = response.json()
    pages = data.get('query', {}).get('pages', {})

    if pages:
        page = next(iter(pages.values()))
        extract = page.get('extract', '')
        print(f"   Length: {len(extract)} characters")
        print(f"   Preview: {extract[:200]}...")

    print("\n" + "=" * 80)
    print("Comparison:")
    print("=" * 80)
    print("If both lengths are similar, the API might be limiting content.")
    print("Check the saved JSON file to see the full structure.")


if __name__ == "__main__":
    import os
    os.makedirs('test_output', exist_ok=True)
    test_wikipedia_api()
