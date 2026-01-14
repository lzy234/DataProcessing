"""Test Wikipedia API endpoints to diagnose 404 errors."""
import requests
import json

def test_rest_api():
    """Test Wikipedia REST API v1."""
    print("=" * 80)
    print("Testing Wikipedia REST API v1")
    print("=" * 80)

    # Test 1: Search endpoint
    print("\n[TEST 1] Search API - Donald Trump")
    search_url = "https://en.wikipedia.org/api/rest_v1/page/search/Donald%20Trump"
    headers = {
        'User-Agent': 'DataProcessingBot/1.0 (Educational Project)',
        'Accept': 'application/json'
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"URL: {search_url}")

        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data.get('pages', []))} results")
            if data.get('pages'):
                print(f"First result: {data['pages'][0].get('title')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Summary endpoint
    print("\n[TEST 2] Summary API - Direct page")
    summary_url = "https://en.wikipedia.org/api/rest_v1/page/summary/Donald_Trump"

    try:
        response = requests.get(summary_url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"URL: {summary_url}")

        if response.status_code == 200:
            data = response.json()
            print(f"Success! Title: {data.get('title')}")
            print(f"Description: {data.get('description')}")
            print(f"Extract (first 100 chars): {data.get('extract', '')[:100]}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")


def test_mediawiki_api():
    """Test Wikipedia MediaWiki API."""
    print("\n" + "=" * 80)
    print("Testing Wikipedia MediaWiki API")
    print("=" * 80)

    # Test 1: Search
    print("\n[TEST 3] MediaWiki Search API")
    api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': 'Donald Trump',
        'format': 'json',
        'srlimit': 1
    }
    headers = {
        'User-Agent': 'DataProcessingBot/1.0 (Educational Project)'
    }

    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"URL: {response.url}")

        if response.status_code == 200:
            data = response.json()
            if data.get('query', {}).get('search'):
                result = data['query']['search'][0]
                print(f"Success! Found: {result.get('title')}")
                print(f"Page ID: {result.get('pageid')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Get page info
    print("\n[TEST 4] MediaWiki Page Info API")
    params = {
        'action': 'query',
        'prop': 'extracts|pageimages|info',
        'exintro': True,
        'explaintext': True,
        'titles': 'Donald Trump',
        'format': 'json',
        'inprop': 'url'
    }

    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                print(f"Success! Page ID: {page_id}")
                print(f"Title: {page_data.get('title')}")
                print(f"URL: {page_data.get('fullurl')}")
                extract = page_data.get('extract', '')
                print(f"Extract (first 200 chars): {extract[:200]}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")


def test_wikidata_api():
    """Test Wikidata API for structured data."""
    print("\n" + "=" * 80)
    print("Testing Wikidata API")
    print("=" * 80)

    print("\n[TEST 5] Wikidata Search")
    api_url = "https://www.wikidata.org/w/api.php"
    params = {
        'action': 'wbsearchentities',
        'search': 'Donald Trump',
        'language': 'en',
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'DataProcessingBot/1.0 (Educational Project)'
    }

    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('search'):
                result = data['search'][0]
                print(f"Success! Found: {result.get('label')}")
                print(f"Entity ID: {result.get('id')}")
                print(f"Description: {result.get('description')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    test_rest_api()
    test_mediawiki_api()
    test_wikidata_api()

    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print("Based on the tests above, the best approach is:")
    print("1. If REST API works → Keep current implementation")
    print("2. If REST API fails but MediaWiki works → Switch to MediaWiki API")
    print("3. If both fail → Check network/firewall, or use Wikidata as fallback")
