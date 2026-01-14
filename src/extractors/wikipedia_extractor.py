"""Wikipedia data extraction using the REST API."""
import json
import requests
from typing import Dict, Optional, List
from src.utils.logger import logger
from src.utils.retry import retry_with_backoff
from src.utils.rate_limiter import RateLimiter
from src.config.settings import Settings


class WikipediaExtractor:
    """
    Extract biographical data from Wikipedia using the REST API.

    Uses:
    - Search API to find person pages
    - Summary API to get biographical info
    """

    def __init__(self):
        """Initialize Wikipedia extractor with rate limiter."""
        self.base_url = "https://en.wikipedia.org/api/rest_v1"
        self.rate_limiter = RateLimiter(
            max_calls=Settings.MAX_WIKIPEDIA_REQUESTS_PER_MINUTE,
            period=60
        )

        # Load cache
        self.cache_file = Settings.WIKIPEDIA_CACHE_FILE
        self.cache = self._load_cache()

        # User agent for Wikipedia API (required by their terms)
        self.headers = {
            'User-Agent': 'DataProcessingBot/1.0 (Educational Project)',
            'Accept': 'application/json'
        }

        logger.info("Initialized WikipediaExtractor")

    def _load_cache(self) -> Dict:
        """Load cached Wikipedia data."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached Wikipedia entries")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load Wikipedia cache: {e}")
        return {}

    def _save_cache(self):
        """Save Wikipedia cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self.cache)} Wikipedia entries to cache")
        except Exception as e:
            logger.error(f"Failed to save Wikipedia cache: {e}")

    def fetch_person_data(self, name: str) -> Optional[Dict]:
        """
        Fetch biographical data for a person.

        Args:
            name: Person's name (English)

        Returns:
            Dictionary with Wikipedia data or None if not found
        """
        if not name:
            return None

        # Check cache
        if name in self.cache:
            logger.debug(f"Using cached Wikipedia data for {name}")
            return self.cache[name]

        logger.info(f"Fetching Wikipedia data for {name}")

        try:
            # Step 1: Search for the person
            page_title = self._search_person(name)
            if not page_title:
                logger.warning(f"No Wikipedia page found for {name}")
                self.cache[name] = None
                self._save_cache()
                return None

            # Step 2: Get page summary
            summary = self._get_page_summary(page_title)
            if not summary:
                logger.warning(f"Failed to get summary for {page_title}")
                self.cache[name] = None
                self._save_cache()
                return None

            # Extract relevant information
            wiki_data = self._extract_bio_data(summary, name)

            # Cache the result
            self.cache[name] = wiki_data
            self._save_cache()

            return wiki_data

        except Exception as e:
            logger.error(f"Error fetching Wikipedia data for {name}: {e}")
            return None

    @retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
    def _search_person(self, name: str) -> Optional[str]:
        """
        Search Wikipedia for a person's page.

        Args:
            name: Person's name

        Returns:
            Page title if found, None otherwise
        """
        search_url = f"{self.base_url}/page/search/{requests.utils.quote(name)}"

        with self.rate_limiter:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()

        data = response.json()

        # Get first result
        if data.get('pages') and len(data['pages']) > 0:
            page_title = data['pages'][0]['title']
            logger.debug(f"Found Wikipedia page: {page_title}")
            return page_title

        return None

    @retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
    def _get_page_summary(self, page_title: str) -> Optional[Dict]:
        """
        Get page summary data.

        Args:
            page_title: Wikipedia page title

        Returns:
            Summary data dictionary
        """
        summary_url = f"{self.base_url}/page/summary/{requests.utils.quote(page_title)}"

        with self.rate_limiter:
            response = requests.get(summary_url, headers=self.headers, timeout=10)
            response.raise_for_status()

        data = response.json()
        return data

    def _extract_bio_data(self, summary: Dict, person_name: str) -> Dict:
        """
        Extract relevant biographical data from Wikipedia summary.

        Args:
            summary: Wikipedia summary data
            person_name: Person's name

        Returns:
            Dictionary with extracted biographical information
        """
        bio_data = {
            'name': person_name,
            'wikipedia_title': summary.get('title', ''),
            'url': summary.get('content_urls', {}).get('desktop', {}).get('page', ''),
            'extract': summary.get('extract', ''),  # First paragraph
            'description': summary.get('description', ''),
            'birth_date': None,
            'education': None
        }

        # Try to extract birth date from description or extract
        birth_date = self._extract_birth_date(summary)
        if birth_date:
            bio_data['birth_date'] = birth_date

        return bio_data

    def _extract_birth_date(self, summary: Dict) -> Optional[str]:
        """
        Try to extract birth date from Wikipedia data.

        Common patterns:
        - "born January 15, 1970"
        - "b. 1970"
        - "(1970-01-15)"

        Args:
            summary: Wikipedia summary data

        Returns:
            Birth date string in YYYY-MM-DD format or None
        """
        import re
        from datetime import datetime

        text = summary.get('extract', '') + ' ' + summary.get('description', '')

        # Pattern 1: "born Month Day, Year" or "b. Month Day, Year"
        pattern1 = r'born?\s+([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            try:
                month_name, day, year = match.groups()
                date_str = f"{month_name} {day} {year}"
                dt = datetime.strptime(date_str, "%B %d %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Pattern 2: "(YYYY-MM-DD)"
        pattern2 = r'\((\d{4})-(\d{2})-(\d{2})\)'
        match = re.search(pattern2, text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"

        # Pattern 3: "born YYYY"
        pattern3 = r'born?\s+(\d{4})'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            year = match.group(1)
            return f"{year}-01-01"  # Default to January 1st

        return None

    def fetch_batch(self, people: List[Dict]) -> Dict[str, Dict]:
        """
        Fetch Wikipedia data for a batch of people.

        Args:
            people: List of person dictionaries with 'name' field

        Returns:
            Dictionary mapping names to Wikipedia data
        """
        results = {}

        for person in people:
            name = person.get('name', '')
            if name:
                wiki_data = self.fetch_person_data(name)
                if wiki_data:
                    results[name] = wiki_data

        logger.info(f"Fetched Wikipedia data for {len(results)}/{len(people)} people")
        return results


def test_wikipedia_extractor():
    """Test function for Wikipedia extractor."""
    test_names = [
        "Nancy Pelosi",
        "Joe Biden",
        "Kamala Harris"
    ]

    extractor = WikipediaExtractor()

    for name in test_names:
        print(f"\n=== {name} ===")
        data = extractor.fetch_person_data(name)

        if data:
            print(f"Title: {data.get('wikipedia_title')}")
            print(f"URL: {data.get('url')}")
            print(f"Birth Date: {data.get('birth_date')}")
            print(f"Description: {data.get('description')}")
            print(f"Extract: {data.get('extract')[:200]}...")
        else:
            print("No data found")


if __name__ == "__main__":
    test_wikipedia_extractor()
