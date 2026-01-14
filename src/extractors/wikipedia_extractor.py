"""Wikipedia data extraction using the MediaWiki API."""
import json
import requests
from typing import Dict, Optional, List
from src.utils.logger import logger
from src.utils.retry import retry_with_backoff
from src.utils.rate_limiter import RateLimiter
from src.config.settings import Settings
from src.processors.text_preprocessor import TextPreprocessor
from src.processors.text_chunker import TextChunker


class WikipediaExtractor:
    """
    Extract biographical data from Wikipedia using the MediaWiki API.

    Uses:
    - MediaWiki Search API to find person pages
    - MediaWiki Query API to get biographical info
    """

    def __init__(self):
        """Initialize Wikipedia extractor with rate limiter."""
        self.api_url = "https://en.wikipedia.org/w/api.php"
        self.rate_limiter = RateLimiter(
            max_calls=Settings.MAX_WIKIPEDIA_REQUESTS_PER_MINUTE,
            period=60
        )

        # Load cache
        self.cache_file = Settings.WIKIPEDIA_CACHE_FILE
        self.cache = self._load_cache()

        # User agent for Wikipedia API (required by their terms)
        self.headers = {
            'User-Agent': 'DataProcessingBot/1.0 (Educational Project)'
        }

        # Initialize preprocessor and chunker
        self.preprocessor = TextPreprocessor()
        self.chunker = TextChunker(
            max_chunk_size=2000,  # 2000 chars per chunk
            min_chunk_size=500,
            overlap=100
        )

        logger.info("Initialized WikipediaExtractor (MediaWiki API)")

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

            # Step 2: Get page full content
            page_data = self._get_page_summary(page_title)
            if not page_data:
                logger.warning(f"Failed to get content for {page_title}")
                self.cache[name] = None
                self._save_cache()
                return None

            # Extract and preprocess biographical data
            wiki_data = self._extract_bio_data(page_data, name)

            # Preprocess the text (clean and structure)
            wiki_data = self.preprocessor.preprocess(wiki_data)

            # Create intelligent chunks
            chunks = self.chunker.chunk_text(wiki_data['extract'], name)

            # Prioritize most relevant chunks
            prioritized_chunks = self.chunker.prioritize_chunks(chunks, max_chunks=5)

            # Add chunks to wiki_data
            wiki_data['chunks'] = prioritized_chunks
            wiki_data['total_chunks'] = len(chunks)
            wiki_data['text_length'] = len(wiki_data['extract'])

            # Cache the result
            self.cache[name] = wiki_data
            self._save_cache()

            logger.info(f"Fetched Wikipedia data for {name}: {len(chunks)} chunks, "
                       f"{wiki_data['text_length']} chars")

            return wiki_data

        except Exception as e:
            logger.error(f"Error fetching Wikipedia data for {name}: {e}")
            return None

    @retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
    def _search_person(self, name: str) -> Optional[str]:
        """
        Search Wikipedia for a person's page using MediaWiki API.

        Args:
            name: Person's name

        Returns:
            Page title if found, None otherwise
        """
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': name,
            'format': 'json',
            'srlimit': 1
        }

        with self.rate_limiter:
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()

        data = response.json()

        # Get first search result
        search_results = data.get('query', {}).get('search', [])
        if search_results:
            page_title = search_results[0]['title']
            logger.debug(f"Found Wikipedia page: {page_title}")
            return page_title

        return None

    @retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
    def _get_page_summary(self, page_title: str) -> Optional[Dict]:
        """
        Get page FULL content using MediaWiki Parse API.

        The extracts API is limited and only returns intro text.
        We use the parse API to get the full parsed content.

        Args:
            page_title: Wikipedia page title

        Returns:
            Page data dictionary with full extract, description, url
        """
        # Step 1: Get page info and URL
        info_params = {
            'action': 'query',
            'prop': 'info',
            'titles': page_title,
            'format': 'json',
            'inprop': 'url'
        }

        with self.rate_limiter:
            response = requests.get(self.api_url, params=info_params, headers=self.headers, timeout=30)
            response.raise_for_status()

        data = response.json()
        pages = data.get('query', {}).get('pages', {})

        if not pages:
            return None

        page_info = next(iter(pages.values()))
        page_id = page_info.get('pageid')
        full_url = page_info.get('fullurl', '')

        # Step 2: Use parse API to get full text content
        parse_params = {
            'action': 'parse',
            'pageid': page_id,
            'prop': 'text|sections',
            'format': 'json',
            'formatversion': 2  # Use newer format
        }

        with self.rate_limiter:
            response = requests.get(self.api_url, params=parse_params, headers=self.headers, timeout=30)
            response.raise_for_status()

        parse_data = response.json()

        if 'parse' not in parse_data:
            logger.warning(f"No parse data for {page_title}")
            return None

        parse_result = parse_data['parse']
        html_content = parse_result.get('text', '')

        # Convert HTML to plain text
        import re
        from html.parser import HTMLParser

        class HTMLToText(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.skip = False
                self.in_heading = False
                self.heading_level = 0

            def handle_starttag(self, tag, attrs):
                # Skip navigation, references, tables, etc.
                if tag in ['table', 'style', 'script']:
                    self.skip = True
                # Check for class attributes to skip
                for attr, value in attrs:
                    if attr == 'class' and any(skip_class in value for skip_class in
                                              ['navbox', 'reflist', 'references', 'infobox',
                                               'mbox', 'ambox', 'catlinks', 'printfooter']):
                        self.skip = True
                        break
                # Mark headings with == markers for section parsing
                if tag == 'h2':
                    self.text.append('\n\n== ')
                    self.in_heading = True
                    self.heading_level = 2
                elif tag == 'h3':
                    self.text.append('\n\n=== ')
                    self.in_heading = True
                    self.heading_level = 3

            def handle_endtag(self, tag):
                if tag in ['table', 'style', 'script']:
                    self.skip = False
                elif tag in ['p', 'div', 'li']:
                    self.text.append('\n')
                elif tag == 'h2' and self.in_heading:
                    self.text.append(' ==\n')
                    self.in_heading = False
                elif tag == 'h3' and self.in_heading:
                    self.text.append(' ===\n')
                    self.in_heading = False

            def handle_data(self, data):
                if not self.skip:
                    # Clean up text
                    cleaned = data.strip()
                    if cleaned:
                        self.text.append(cleaned)
                        if not self.in_heading:
                            self.text.append(' ')

        parser = HTMLToText()
        parser.feed(html_content)
        plain_text = ''.join(parser.text)

        # Clean up text
        plain_text = re.sub(r'\n{3,}', '\n\n', plain_text)  # Remove excess newlines
        plain_text = re.sub(r'  +', ' ', plain_text)  # Remove excess spaces
        plain_text = plain_text.strip()

        # Build result similar to old format
        result = {
            'pageid': page_id,
            'title': page_title,
            'extract': plain_text,
            'fullurl': full_url
        }

        logger.debug(f"Fetched full content for {page_title}: {len(plain_text)} chars")

        return result

    def _extract_bio_data(self, summary: Dict, person_name: str) -> Dict:
        """
        Extract relevant biographical data from Wikipedia summary.

        Args:
            summary: Wikipedia summary data from MediaWiki API
            person_name: Person's name

        Returns:
            Dictionary with extracted biographical information
        """
        bio_data = {
            'name': person_name,
            'wikipedia_title': summary.get('title', ''),
            'url': summary.get('fullurl', ''),
            'extract': summary.get('extract', ''),  # Full intro section
            'description': '',  # MediaWiki doesn't provide short description in this endpoint
            'birth_date': None,
            'education': None
        }

        # Try to extract birth date from extract text
        birth_date = self._extract_birth_date(summary)
        if birth_date:
            bio_data['birth_date'] = birth_date

        # Try to extract education info
        education = self._extract_education(summary)
        if education:
            bio_data['education'] = education

        return bio_data

    def _extract_birth_date(self, summary: Dict) -> Optional[str]:
        """
        Try to extract birth date from Wikipedia data.

        Common patterns in Wikipedia extracts:
        - "born January 15, 1970"
        - "born 15 January 1970" (British format)
        - "(born January 15, 1970)"
        - "b. 1970"

        Args:
            summary: Wikipedia summary data

        Returns:
            Birth date string in YYYY-MM-DD format or None
        """
        import re
        from datetime import datetime

        text = summary.get('extract', '')

        # Pattern 1: "born Month Day, Year" (American format)
        pattern1 = r'born\s+([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            try:
                month_name, day, year = match.groups()
                date_str = f"{month_name} {day} {year}"
                dt = datetime.strptime(date_str, "%B %d %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Pattern 2: "born Day Month Year" (British format)
        pattern2 = r'born\s+(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            try:
                day, month_name, year = match.groups()
                date_str = f"{month_name} {day} {year}"
                dt = datetime.strptime(date_str, "%B %d %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Pattern 3: "born YYYY"
        pattern3 = r'born\s+(\d{4})'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            year = match.group(1)
            return f"{year}-01-01"  # Default to January 1st

        return None

    def _extract_education(self, summary: Dict) -> Optional[str]:
        """
        Try to extract education information from Wikipedia data.

        Args:
            summary: Wikipedia summary data

        Returns:
            Education summary string or None
        """
        import re

        text = summary.get('extract', '')

        # Look for education-related keywords
        education_keywords = [
            r'graduated from ([^.,;]+)',
            r'attended ([^.,;]+)',
            r'studied at ([^.,;]+)',
            r'degree from ([^.,;]+)',
            r'education at ([^.,;]+)',
            r'alma mater[:\s]+([^.,;]+)'
        ]

        education_info = []
        for pattern in education_keywords:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                school = match.group(1).strip()
                if school and len(school) < 100:  # Reasonable length
                    education_info.append(school)

        if education_info:
            # Remove duplicates while preserving order
            unique_education = []
            seen = set()
            for edu in education_info:
                edu_lower = edu.lower()
                if edu_lower not in seen:
                    seen.add(edu_lower)
                    unique_education.append(edu)

            return "; ".join(unique_education)

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
