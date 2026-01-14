"""AI-powered data enhancement using section selection strategy."""
import json
from typing import Dict, List
from openai import OpenAI
from src.utils.logger import logger
from src.utils.rate_limiter import RateLimiter
from src.config.settings import Settings


class ClaudeAIEnhancerWithSections:
    """
    AI enhancer that lets AI choose which Wikipedia sections to read.

    Uses a two-round conversation approach:
    1. AI reviews table of contents and selects sections
    2. AI reads selected sections and extracts information
    """

    def __init__(self):
        """Initialize AI enhancer with section selection capability."""
        if not Settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        if not Settings.ANTHROPIC_BASE_URL:
            raise ValueError("ANTHROPIC_BASE_URL not set in environment")

        # Initialize OpenAI client with custom endpoint
        self.client = OpenAI(
            api_key=Settings.ANTHROPIC_API_KEY,
            base_url=Settings.ANTHROPIC_BASE_URL + "/v1",
            timeout=120.0
        )

        self.model = Settings.AI_MODEL
        self.rate_limiter = RateLimiter(
            max_calls=Settings.MAX_CLAUDE_REQUESTS_PER_MINUTE,
            period=60
        )

        # Load cache
        self.cache_file = Settings.AI_RESPONSES_CACHE_FILE
        self.cache = self._load_cache()

        logger.info(f"Initialized ClaudeAIEnhancerWithSections with model {self.model}")

    def _load_cache(self) -> Dict:
        """Load cached AI responses from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached AI responses")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return {}

    def _save_cache(self):
        """Save AI responses cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self.cache)} responses to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _select_sections(self, person: Dict, wiki: Dict) -> List[str]:
        """
        Round 1: Let AI select which sections to read.

        Args:
            person: Person dictionary with name, role, etc.
            wiki: Wikipedia data with table_of_contents

        Returns:
            List of selected section names
        """
        cache_key = f"{person['name']}_section_selection"
        if cache_key in self.cache:
            logger.debug(f"Using cached section selection for {person['name']}")
            return self.cache[cache_key]

        toc = wiki.get('table_of_contents', '')
        if not toc:
            logger.warning(f"No table of contents for {person['name']}")
            return []

        prompt = f"""You need to extract biographical information for {person['name']}.

Required fields to extract:
- dateOfBirth (YYYY-MM-DD format)
- gender (male/female)
- party (political party if applicable)
- education (universities, degrees)
- careerHistory (timeline of positions)
- bio (200-500 word biography)
- organization (current organization/employer)

Here is the Wikipedia table of contents:

{toc}

Based on this table of contents, select the sections you need to read to extract the required information.

IMPORTANT:
- Choose sections likely to contain biographical information (Introduction, Early life, Education, Career, etc.)
- Avoid sections like References, See also, External links, Notes
- You can select multiple sections
- Be strategic - prioritize the most relevant sections

Respond with ONLY a JSON object in this format:
{{
  "selected_sections": ["Section Name 1", "Section Name 2", ...]
}}

Choose wisely - you'll only get the sections you request."""

        try:
            with self.rate_limiter:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=500,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )

            response_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                # Remove first and last lines (```json and ```)
                response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text

            result = json.loads(response_text)
            selected = result.get('selected_sections', [])

            self.cache[cache_key] = selected
            self._save_cache()

            logger.info(f"{person['name']}: AI selected {len(selected)} sections: {selected}")
            return selected

        except Exception as e:
            logger.error(f"Failed to select sections for {person['name']}: {e}")
            return []

    def _get_section_content(self, section_names: List[str], sections: List[Dict]) -> str:
        """
        Get content of requested sections.

        Args:
            section_names: List of section names to retrieve
            sections: All available sections from Wikipedia

        Returns:
            Formatted section content string
        """
        result = []
        for name in section_names:
            # Try exact match first, then case-insensitive match
            section = next(
                (s for s in sections if s['name'] == name),
                next(
                    (s for s in sections if s['name'].lower() == name.lower()),
                    None
                )
            )

            if section:
                result.append(f"=== {section['name']} ===\n{section['text']}")
            else:
                logger.warning(f"Section '{name}' not found in available sections")

        return "\n\n".join(result)

    def _extract_from_sections(self, person: Dict, wiki: Dict, section_content: str) -> Dict:
        """
        Round 2: Extract information from selected sections.

        Args:
            person: Person dictionary
            wiki: Wikipedia data
            section_content: Content of selected sections

        Returns:
            Extracted biographical data
        """
        cache_key = f"{person['name']}_extraction_v2"
        if cache_key in self.cache:
            logger.debug(f"Using cached extraction for {person['name']}")
            return self.cache[cache_key]

        prompt = f"""Based on the following Wikipedia sections for {person['name']}, extract biographical information.

Person context:
- Name: {person.get('name', '')}
- Chinese Name: {person.get('ChineseName', '')}
- Current Role: {person.get('currentRole', '')}

Wikipedia sections:

{section_content}

Extract the following information and respond with ONLY a JSON object:

{{
  "dateOfBirth": "YYYY-MM-DD format or null if not found",
  "gender": "male or female or empty string if not clear",
  "party": "Republican or Democratic or Independent or empty string if not a politician or not mentioned",
  "education": "Summary of education background (1-2 sentences) or empty string",
  "careerHistory": "Timeline of major positions (3-5 sentences) or empty string",
  "bio": "Comprehensive English biography (200-500 words) or empty string if insufficient info",
  "organization": "Current organization/employer (official English name) or empty string",
  "need_more_sections": false,
  "additional_sections": []
}}

IMPORTANT:
- Only use information explicitly stated in the text
- Do not infer, assume, or guess any information
- If information is missing, use empty string "" or null
- For party: only "Republican", "Democratic", or "Independent" (no other values)
- If you need more sections to extract complete information, set need_more_sections to true and list them in additional_sections
- For bio: write 200-500 words in neutral, encyclopedic tone. If sections don't have enough info, use empty string."""

        try:
            with self.rate_limiter:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )

            response_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text

            result = json.loads(response_text)

            self.cache[cache_key] = result
            self._save_cache()

            return result

        except Exception as e:
            logger.error(f"Failed to extract information for {person['name']}: {e}")
            return self._empty_extraction_result()

    def _empty_extraction_result(self) -> Dict:
        """Return empty extraction result."""
        return {
            "dateOfBirth": None,
            "gender": "",
            "party": "",
            "education": "",
            "careerHistory": "",
            "bio": "",
            "organization": "",
            "need_more_sections": False,
            "additional_sections": []
        }

    def enhance_single(self, person: Dict, wiki: Dict) -> Dict:
        """
        Enhance a single person using two-round section selection.

        Args:
            person: Person dictionary
            wiki: Wikipedia data with sections and table_of_contents

        Returns:
            Enhanced person data with extracted fields
        """
        name = person.get('name', '')
        sections = wiki.get('sections', [])

        if not sections:
            logger.warning(f"No sections available for {name}")
            return self._empty_result(name)

        # Round 1: AI selects sections
        selected_sections = self._select_sections(person, wiki)

        if not selected_sections:
            logger.warning(f"No sections selected for {name}")
            return self._empty_result(name)

        # Get content of selected sections
        section_content = self._get_section_content(selected_sections, sections)

        if not section_content:
            logger.warning(f"No section content retrieved for {name}")
            return self._empty_result(name)

        # Round 2: Extract information from sections
        result = self._extract_from_sections(person, wiki, section_content)

        # Optional Round 3: If AI requests more sections
        if result.get('need_more_sections') and result.get('additional_sections'):
            additional_sections = result['additional_sections']
            logger.info(f"{name}: AI requesting {len(additional_sections)} more sections: {additional_sections}")

            additional_content = self._get_section_content(additional_sections, sections)
            if additional_content:
                combined_content = section_content + "\n\n" + additional_content
                # Re-extract with more content
                result = self._extract_from_sections(person, wiki, combined_content)

        # Add source information
        result['name'] = name
        result['sources'] = [{
            'sourceName': 'Wikipedia',
            'sourceUrl': wiki.get('url', ''),
            'reliability': 'high'
        }]

        # Remove internal fields
        result.pop('need_more_sections', None)
        result.pop('additional_sections', None)

        return result

    def enhance_batch(self, people: List[Dict], wikipedia_data: Dict = None) -> List[Dict]:
        """
        Enhance a batch of people using section selection.

        Args:
            people: List of person dictionaries
            wikipedia_data: Wikipedia data keyed by name

        Returns:
            List of enhanced person data
        """
        logger.info(f"Enhancing batch of {len(people)} people with section selection")

        results = []
        for person in people:
            name = person.get('name', '')
            wiki = (wikipedia_data or {}).get(name, {})

            if not wiki or not wiki.get('sections'):
                logger.warning(f"No Wikipedia sections for {name}, skipping")
                results.append(self._empty_result(name))
                continue

            try:
                result = self.enhance_single(person, wiki)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to enhance {name}: {e}")
                results.append(self._empty_result(name))

        return results

    def _empty_result(self, name: str) -> Dict:
        """Return empty result for a person."""
        return {
            "name": name,
            "dateOfBirth": None,
            "gender": "",
            "party": "",
            "education": "",
            "careerHistory": "",
            "bio": "",
            "organization": "",
            "sources": []
        }


def test_section_selection():
    """Test function for section selection enhancer."""
    test_person = {
        'name': 'Donald J. Trump',
        'ChineseName': '唐纳德·特朗普',
        'currentRole': '第45任美国总统'
    }

    try:
        from src.extractors.wikipedia_extractor import WikipediaExtractor

        # Get Wikipedia data
        extractor = WikipediaExtractor()
        wiki_data = extractor.fetch_person_data(test_person['name'])

        if not wiki_data:
            print("Failed to fetch Wikipedia data")
            return

        print(f"\n=== Table of Contents ===")
        print(wiki_data.get('table_of_contents', 'N/A'))

        # Test section selection
        enhancer = ClaudeAIEnhancerWithSections()
        result = enhancer.enhance_single(test_person, wiki_data)

        print(f"\n=== Extracted Data ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    test_section_selection()
