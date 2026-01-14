"""AI-powered data enhancement using Claude API."""
import json
from typing import Dict, List, Optional
from anthropic import Anthropic
from src.utils.logger import logger
from src.utils.retry import retry_with_backoff
from src.utils.rate_limiter import RateLimiter
from src.config.settings import Settings


class ClaudeAIEnhancer:
    """Uses Claude API to intelligently complete missing person data."""

    def __init__(self):
        """Initialize Claude API client and rate limiter."""
        if not Settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        self.client = Anthropic(api_key=Settings.ANTHROPIC_API_KEY)
        self.rate_limiter = RateLimiter(
            max_calls=Settings.MAX_CLAUDE_REQUESTS_PER_MINUTE,
            period=60
        )
        self.model = "claude-3-5-sonnet-20241022"

        # Load cache if exists
        self.cache_file = Settings.AI_RESPONSES_CACHE_FILE
        self.cache = self._load_cache()

        logger.info(f"Initialized ClaudeAIEnhancer with model {self.model}")

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

    def enhance_batch(self, people: List[Dict], wikipedia_data: Dict = None) -> List[Dict]:
        """
        Enhance a batch of people with AI-completed data.

        Args:
            people: List of person dictionaries (up to 10)
            wikipedia_data: Optional Wikipedia data keyed by person name

        Returns:
            List of enhanced person dictionaries with completed fields
        """
        if len(people) > Settings.BATCH_SIZE:
            logger.warning(f"Batch size {len(people)} exceeds limit {Settings.BATCH_SIZE}")

        # Check cache first
        cache_key = self._get_cache_key(people)
        if cache_key in self.cache:
            logger.info(f"Using cached response for batch of {len(people)} people")
            return self.cache[cache_key]

        logger.info(f"Enhancing batch of {len(people)} people with Claude API")

        try:
            # Build structured prompt
            prompt = self._build_batch_prompt(people, wikipedia_data or {})

            # Call Claude API with rate limiting
            with self.rate_limiter:
                enhanced_data = self._call_claude_api(prompt, len(people))

            # Cache the result
            self.cache[cache_key] = enhanced_data
            self._save_cache()

            return enhanced_data

        except Exception as e:
            logger.error(f"Failed to enhance batch: {e}")
            # Return degraded data (original data with minimal enhancements)
            return self._create_degraded_response(people)

    def _get_cache_key(self, people: List[Dict]) -> str:
        """Generate cache key from people list."""
        names = [p.get('name', '') for p in people]
        return "|".join(names)

    def _build_batch_prompt(self, people: List[Dict], wikipedia_data: Dict) -> str:
        """
        Build structured prompt for batch processing.

        The prompt asks Claude to complete missing fields for multiple people
        in a single request, returning structured JSON.
        """
        people_info = []

        for idx, person in enumerate(people, 1):
            name = person.get('name', '')
            wiki = wikipedia_data.get(name, {})

            person_section = f"""
Person {idx}:
- Chinese Name: {person.get('ChineseName', 'N/A')}
- English Name: {name}
- Current Role/Title: {person.get('currentRole', 'N/A')}
- Organization: {person.get('organization_text', 'N/A')}
- Chinese Biography: {person.get('bio_chinese', 'N/A')}
"""

            if wiki:
                person_section += f"""- Wikipedia Summary: {wiki.get('extract', 'N/A')}
- Wikipedia Birth Date: {wiki.get('birth_date', 'N/A')}
- Wikipedia URL: {wiki.get('url', 'N/A')}
"""

            people_info.append(person_section)

        prompt = f"""You are a data analyst helping complete biographical information for {len(people)} political figures in the United States.

Below is the available data for each person. Please analyze the information and provide the following fields in structured JSON format:

IMPORTANT INSTRUCTIONS:
1. For dateOfBirth: Use YYYY-MM-DD format. If exact date unknown, use null.
2. For gender: Infer from Chinese pronouns (他=male, 她=female) or context. Use "male", "female", or "other".
3. For education: Summarize their educational background (universities, degrees). If unknown, use empty string.
4. For careerHistory: Create a brief timeline of major positions held. Focus on political career.
5. For bio: Write a 200-500 word English biography in neutral, encyclopedic tone. Focus on political influence and career achievements.
6. For sources: List data sources used with reliability rating ("high", "medium", "low").

INPUT DATA:
{"".join(people_info)}

OUTPUT FORMAT (valid JSON array):
[
  {{
    "name": "English Name",
    "dateOfBirth": "YYYY-MM-DD or null",
    "gender": "male/female/other",
    "education": "Educational background summary",
    "careerHistory": "Career timeline with key positions",
    "bio": "English biography (200-500 words)",
    "sources": [
      {{
        "sourceName": "Source name",
        "sourceUrl": "URL if available",
        "reliability": "high/medium/low"
      }}
    ]
  }},
  ...
]

Please respond with ONLY the JSON array, no additional text."""

        return prompt

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def _call_claude_api(self, prompt: str, expected_count: int) -> List[Dict]:
        """
        Call Claude API and parse response.

        Args:
            prompt: The structured prompt
            expected_count: Expected number of people in response

        Returns:
            List of enhanced person data dictionaries
        """
        logger.debug(f"Calling Claude API (expecting {expected_count} people)")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            temperature=0.3,  # Lower temperature for more consistent structured output
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Extract text from response
        response_text = response.content[0].text.strip()

        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                # Extract content between ```json and ```
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            enhanced_data = json.loads(response_text)

            # Validate response structure
            if not isinstance(enhanced_data, list):
                raise ValueError("Response is not a JSON array")

            if len(enhanced_data) != expected_count:
                logger.warning(
                    f"Expected {expected_count} people, got {len(enhanced_data)}"
                )

            logger.info(f"Successfully parsed {len(enhanced_data)} enhanced records")
            return enhanced_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            raise

    def _create_degraded_response(self, people: List[Dict]) -> List[Dict]:
        """
        Create minimal response when API fails.

        Uses original data with basic transformations.
        """
        logger.warning("Creating degraded response due to API failure")

        degraded = []
        for person in people:
            enhanced = {
                "name": person.get('name', ''),
                "dateOfBirth": None,
                "gender": self._infer_gender_from_chinese(person.get('bio_chinese', '')),
                "education": "",
                "careerHistory": person.get('currentRole', ''),
                "bio": person.get('bio_chinese', ''),  # Use Chinese bio as fallback
                "sources": [{
                    "sourceName": "Original CSV Data",
                    "sourceUrl": "",
                    "reliability": "medium"
                }]
            }
            degraded.append(enhanced)

        return degraded

    def _infer_gender_from_chinese(self, text: str) -> str:
        """Infer gender from Chinese text based on pronouns."""
        if '她' in text:
            return 'female'
        elif '他' in text:
            return 'male'
        return 'other'

    def enhance_single(self, person: Dict, wikipedia_data: Dict = None) -> Dict:
        """
        Enhance a single person (convenience method).

        Args:
            person: Person dictionary
            wikipedia_data: Optional Wikipedia data for this person

        Returns:
            Enhanced person dictionary
        """
        wiki_dict = {person.get('name'): wikipedia_data} if wikipedia_data else {}
        result = self.enhance_batch([person], wiki_dict)
        return result[0] if result else self._create_degraded_response([person])[0]


def test_ai_enhancer():
    """Test function for AI enhancer."""
    # Sample test data
    test_person = {
        'name': 'Nancy Pelosi',
        'ChineseName': '南希·佩洛西',
        'currentRole': 'Former Speaker of the House (D-CA)',
        'organization_text': '美国众议院 (U.S. House of Representatives)',
        'bio_chinese': '美国民主党政治家,曾任美国众议院议长,是美国历史上首位女性众议院议长。'
    }

    try:
        enhancer = ClaudeAIEnhancer()
        result = enhancer.enhance_single(test_person)

        print("Enhanced data:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    test_ai_enhancer()
