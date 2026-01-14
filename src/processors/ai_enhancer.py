"""AI-powered data enhancement using Claude API via OpenAI-compatible endpoint."""
import json
from typing import Dict, List, Optional
from openai import OpenAI
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

        if not Settings.ANTHROPIC_BASE_URL:
            raise ValueError("ANTHROPIC_BASE_URL not set in environment. This is required for OpenAI-compatible endpoint.")

        # Initialize OpenAI client with custom endpoint
        self.client = OpenAI(
            api_key=Settings.ANTHROPIC_API_KEY,
            base_url=Settings.ANTHROPIC_BASE_URL + "/v1",
            timeout=120.0  # Increase timeout for slower endpoints
        )
        logger.info(f"Using OpenAI-compatible API endpoint: {Settings.ANTHROPIC_BASE_URL}/v1")

        self.rate_limiter = RateLimiter(
            max_calls=Settings.MAX_CLAUDE_REQUESTS_PER_MINUTE,
            period=60
        )
        # Use AI model from settings (default: deepseek-reasoner for better reasoning)
        self.model = Settings.AI_MODEL

        # Load cache if exists
        self.cache_file = Settings.AI_RESPONSES_CACHE_FILE
        self.cache = self._load_cache()

        logger.info(f"Initialized ClaudeAIEnhancer with model {self.model}")
        logger.info(f"Using API endpoint: {Settings.ANTHROPIC_BASE_URL}")

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

        Routes to either new section-selection mode or legacy multi-stage mode
        based on Settings.USE_SECTION_SELECTION configuration.

        Args:
            people: List of person dictionaries (up to 10)
            wikipedia_data: Optional Wikipedia data keyed by person name

        Returns:
            List of enhanced person dictionaries with completed fields
        """
        # Check if USE_SECTION_SELECTION is enabled
        use_section_selection = getattr(Settings, 'USE_SECTION_SELECTION', False)

        if use_section_selection:
            # Use new section selection mode
            logger.info("Using AI section selection mode")
            return self._enhance_batch_with_sections(people, wikipedia_data)
        else:
            # Use legacy multi-stage mode
            logger.info("Using legacy multi-stage mode")
            return self._enhance_batch_legacy(people, wikipedia_data)

    def _enhance_batch_with_sections(self, people: List[Dict], wikipedia_data: Dict = None) -> List[Dict]:
        """
        Enhance batch using new section selection approach.

        Args:
            people: List of person dictionaries
            wikipedia_data: Wikipedia data with sections field

        Returns:
            List of enhanced person dictionaries
        """
        try:
            from src.processors.ai_enhancer_with_sections import ClaudeAIEnhancerWithSections
            enhancer = ClaudeAIEnhancerWithSections()
            return enhancer.enhance_batch(people, wikipedia_data)
        except Exception as e:
            logger.error(f"Section selection mode failed: {e}, falling back to legacy mode")
            return self._enhance_batch_legacy(people, wikipedia_data)

    def _enhance_batch_legacy(self, people: List[Dict], wikipedia_data: Dict = None) -> List[Dict]:
        """
        Legacy: Enhance a batch of people with AI-completed data using multiple specialized requests.

        This method splits the enhancement into 5 separate API calls:
        1. Basic info (dateOfBirth, gender, party) - lightweight fields
        2. Education - detailed educational background
        3. Career History - professional timeline
        4. Biography - comprehensive bio text
        5. Organization - extract organization from Wikipedia

        Args:
            people: List of person dictionaries (up to 10)
            wikipedia_data: Optional Wikipedia data keyed by person name

        Returns:
            List of enhanced person dictionaries with completed fields
        """
        if len(people) > Settings.BATCH_SIZE:
            logger.warning(f"Batch size {len(people)} exceeds limit {Settings.BATCH_SIZE}")

        logger.info(f"Enhancing batch of {len(people)} people with Claude API (multi-stage legacy mode)")

        enhanced_results = []

        for person in people:
            name = person.get('name', '')
            wiki = (wikipedia_data or {}).get(name, {})

            # Initialize result with existing data
            enhanced = {
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

            all_sources = []

            try:
                # Stage 1: Basic Info (dateOfBirth, gender, party)
                basic_info = self._enhance_basic_info(person, wiki)
                enhanced["dateOfBirth"] = basic_info.get("dateOfBirth")
                enhanced["gender"] = basic_info.get("gender", "")
                enhanced["party"] = basic_info.get("party", "")
                all_sources.extend(basic_info.get("sources", []))

                # Stage 2: Education
                education_info = self._enhance_education(person, wiki)
                enhanced["education"] = education_info.get("education", "")
                all_sources.extend(education_info.get("sources", []))

                # Stage 3: Career History
                career_info = self._enhance_career_history(person, wiki)
                enhanced["careerHistory"] = career_info.get("careerHistory", "")
                all_sources.extend(career_info.get("sources", []))

                # Stage 4: Biography
                bio_info = self._enhance_biography(person, wiki)
                enhanced["bio"] = bio_info.get("bio", "")
                all_sources.extend(bio_info.get("sources", []))

                # Stage 5: Organization (from Wikipedia)
                org_info = self._extract_organization(person, wiki)
                enhanced["organization"] = org_info.get("organization", "")
                all_sources.extend(org_info.get("sources", []))

            except Exception as e:
                logger.error(f"Failed to enhance {name}: {e}")
                # Keep empty values for reliability

            # Deduplicate sources by URL
            seen_urls = set()
            unique_sources = []
            for source in all_sources:
                url = source.get("sourceUrl", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_sources.append(source)
                elif not url:
                    unique_sources.append(source)

            enhanced["sources"] = unique_sources
            enhanced_results.append(enhanced)

        return enhanced_results

    def _get_cache_key(self, people: List[Dict]) -> str:
        """Generate cache key from people list."""
        names = [p.get('name', '') for p in people]
        return "|".join(names)

    def _get_relevant_text(self, wiki: Dict, keywords: List[str] = None, max_chars: int = 3000) -> str:
        """
        Get relevant text from Wikipedia data, preferring chunks if available.

        Args:
            wiki: Wikipedia data dictionary
            keywords: Keywords to prioritize chunks (e.g., ['education', 'university'])
            max_chars: Maximum characters to return

        Returns:
            Relevant text string
        """
        # If chunks are available, use prioritized chunks
        if wiki.get('chunks'):
            chunks = wiki['chunks']

            # Filter out chunks that are mostly navigation/table of contents
            # Real biographical content usually contains "born" or full sentences
            filtered_chunks = []
            for chunk in chunks:
                text = chunk['text']
                # Check if this looks like actual content (not TOC)
                # TOC chunks have lots of short lines and few full sentences
                lines = text.strip().split('\n')
                short_lines = sum(1 for line in lines if len(line.strip()) < 50)
                long_content = any('born' in text.lower() or len(line) > 100 for line in lines)

                # Keep chunks that have substantial content
                if long_content or (len(lines) - short_lines) > 3:
                    filtered_chunks.append(chunk)

            if not filtered_chunks:
                filtered_chunks = chunks  # Fallback to all chunks

            # Always score and sort chunks to prioritize biographical content
            scored_chunks = []
            for chunk in filtered_chunks:
                score = chunk.get('is_intro', False) * 100  # Intro always high priority
                text_lower = chunk['text'].lower()

                # Bonus for biographical indicators
                if 'born' in text_lower:
                    score += 50
                if ' is an american' in text_lower or ' is a ' in text_lower:
                    score += 30

                # If keywords provided, add keyword scoring
                if keywords:
                    for keyword in keywords:
                        if keyword.lower() in text_lower:
                            score += 10

                scored_chunks.append((score, chunk))

            scored_chunks.sort(reverse=True, key=lambda x: x[0])
            filtered_chunks = [chunk for score, chunk in scored_chunks]

            # Combine chunks up to max_chars
            combined_text = ""
            for chunk in filtered_chunks:
                chunk_text = chunk['text']
                if len(combined_text) + len(chunk_text) + 10 <= max_chars:
                    section_header = f"\n\n=== {chunk['section']} ===\n" if chunk['section'] != 'Introduction' else ""
                    combined_text += section_header + chunk_text
                else:
                    break

            return combined_text.strip()

        # Fallback to full extract (truncated)
        extract = wiki.get('extract', '')
        if len(extract) > max_chars:
            return extract[:max_chars] + "..."
        return extract

    def _enhance_basic_info(self, person: Dict, wiki: Dict) -> Dict:
        """
        Extract basic info (dateOfBirth, gender, party) from Wikipedia data only.
        No AI inference - only use reliable sources.
        """
        cache_key = f"{person.get('name', '')}_basic"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = {
            "dateOfBirth": None,
            "gender": "",
            "party": "",
            "sources": []
        }

        # Extract dateOfBirth from Wikipedia structured data
        if wiki.get('birth_date'):
            result["dateOfBirth"] = wiki['birth_date']
            result["sources"].append({
                "sourceName": "Wikipedia",
                "sourceUrl": wiki.get('url', ''),
                "reliability": "high"
            })

        # For gender and party, we extract from Wikipedia text using AI
        if wiki:
            # Get relevant text from chunks (intro preferred)
            # Use 3000 chars for better coverage of biographical info
            wiki_extract = self._get_relevant_text(wiki, max_chars=3000)
            if wiki_extract:
                # Extract gender, party, and potentially dateOfBirth from Wikipedia text
                prompt = f"""Based ONLY on the following Wikipedia text, extract basic biographical information.

Person: {person.get('name', '')}

Wikipedia text:
{wiki_extract}

Respond with ONLY a JSON object in this exact format:
{{
  "gender": "male" or "female" or "" (empty string if not explicitly mentioned),
  "party": "Republican" or "Democratic" or "Independent" or "" (empty string if not mentioned or not a politician),
  "dateOfBirth": "YYYY-MM-DD format" or null (if birth date is mentioned but not already provided)
}}

IMPORTANT:
- For gender: Look for pronouns (he/she/his/her) or explicit mentions. Only use if clear.
- For party: Look for "Republican Party", "Democratic Party", "Democrat", "member of the Republican/Democratic Party", etc.
  - Use "Republican" or "Democratic" (singular form)
  - Only extract if the person is a current or former member of a political party
  - If the person switched parties, use the CURRENT party affiliation
- For dateOfBirth: Only extract if explicitly mentioned and in a clear date format (e.g., "born June 14, 1946")
- If uncertain about any field, use empty string "" or null
- Do not infer or guess"""

                try:
                    with self.rate_limiter:
                        response = self._call_claude_simple(prompt)
                        basic_data = json.loads(response)

                        # Extract gender
                        if basic_data.get('gender'):
                            result["gender"] = basic_data['gender']

                        # Extract party
                        if basic_data.get('party'):
                            result["party"] = basic_data['party']

                        # Extract dateOfBirth if not already set
                        if not result["dateOfBirth"] and basic_data.get('dateOfBirth'):
                            result["dateOfBirth"] = basic_data['dateOfBirth']

                except Exception as e:
                    logger.warning(f"Failed to extract basic info for {person.get('name', '')}: {e}")

        self.cache[cache_key] = result
        self._save_cache()
        return result

    def _enhance_education(self, person: Dict, wiki: Dict) -> Dict:
        """
        Extract education information from Wikipedia data only.
        No AI inference - only use reliable sources.
        """
        cache_key = f"{person.get('name', '')}_education"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = {
            "education": "",
            "sources": []
        }

        if not wiki:
            self.cache[cache_key] = result
            self._save_cache()
            return result

        # Get relevant text chunks prioritizing education-related content
        # Increased from 3000 to 6000 for better coverage of educational background
        wiki_extract = self._get_relevant_text(
            wiki,
            keywords=['education', 'university', 'college', 'graduated', 'degree', 'studied'],
            max_chars=6000
        )

        if not wiki_extract:
            self.cache[cache_key] = result
            self._save_cache()
            return result

        # Use AI to extract education from Wikipedia text
        prompt = f"""Based ONLY on the following Wikipedia text, extract educational background information.

Wikipedia text:
{wiki_extract}

Respond with ONLY a JSON object in this exact format:
{{
  "education": "Summarize universities, degrees, and graduation years if mentioned. Empty string if no education info found."
}}

IMPORTANT:
- Only extract information explicitly mentioned in the Wikipedia text
- Do not infer or add information not present
- If no education information is found, return empty string ""
- Keep the summary concise (1-2 sentences max)"""

        try:
            with self.rate_limiter:
                response = self._call_claude_simple(prompt)
                edu_data = json.loads(response)
                if edu_data.get('education'):
                    result["education"] = edu_data['education']
                    result["sources"].append({
                        "sourceName": "Wikipedia",
                        "sourceUrl": wiki.get('url', ''),
                        "reliability": "high"
                    })
        except Exception as e:
            logger.warning(f"Failed to extract education for {person.get('name', '')}: {e}")

        self.cache[cache_key] = result
        self._save_cache()
        return result

    def _enhance_career_history(self, person: Dict, wiki: Dict) -> Dict:
        """
        Extract career history from Wikipedia data only.
        No AI inference - only use reliable sources.
        """
        cache_key = f"{person.get('name', '')}_career"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = {
            "careerHistory": "",
            "sources": []
        }

        if not wiki:
            self.cache[cache_key] = result
            self._save_cache()
            return result

        # Get relevant text chunks prioritizing career-related content
        # Increased from 3500 to 8000 for better coverage of career history
        wiki_extract = self._get_relevant_text(
            wiki,
            keywords=['career', 'elected', 'appointed', 'served', 'position', 'founded', 'work'],
            max_chars=8000
        )

        if not wiki_extract:
            self.cache[cache_key] = result
            self._save_cache()
            return result

        # Use AI to extract career timeline from Wikipedia text
        prompt = f"""Based ONLY on the following Wikipedia text, create a career history timeline.

Person: {person.get('name', '')}
Current Role: {person.get('currentRole', '')}

Wikipedia text:
{wiki_extract}

Respond with ONLY a JSON object in this exact format:
{{
  "careerHistory": "Create a chronological timeline of major positions held. Empty string if no career info found."
}}

IMPORTANT:
- Only extract positions and dates explicitly mentioned in the Wikipedia text
- Do not infer or add information not present
- If no career information is found, return empty string ""
- Focus on political and professional career
- Keep it concise (3-5 sentences max)"""

        try:
            with self.rate_limiter:
                response = self._call_claude_simple(prompt)
                career_data = json.loads(response)
                if career_data.get('careerHistory'):
                    result["careerHistory"] = career_data['careerHistory']
                    result["sources"].append({
                        "sourceName": "Wikipedia",
                        "sourceUrl": wiki.get('url', ''),
                        "reliability": "high"
                    })
        except Exception as e:
            logger.warning(f"Failed to extract career history for {person.get('name', '')}: {e}")

        self.cache[cache_key] = result
        self._save_cache()
        return result

    def _enhance_biography(self, person: Dict, wiki: Dict) -> Dict:
        """
        Create English biography from Wikipedia data only.
        No AI inference - only use reliable sources.
        """
        cache_key = f"{person.get('name', '')}_bio"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = {
            "bio": "",
            "sources": []
        }

        if not wiki:
            self.cache[cache_key] = result
            self._save_cache()
            return result

        # Get relevant text chunks - prioritize biographical sections
        # Increased from 4000 to 10000 for comprehensive biography generation
        wiki_extract = self._get_relevant_text(
            wiki,
            keywords=['born', 'early life', 'career', 'education', 'political'],
            max_chars=10000  # Larger for biography
        )

        if not wiki_extract:
            self.cache[cache_key] = result
            self._save_cache()
            return result

        # Use AI to create English biography from Wikipedia text
        prompt = f"""Based ONLY on the following Wikipedia text, write an English biography.

Person: {person.get('name', '')}
Chinese Name: {person.get('ChineseName', '')}
Current Role: {person.get('currentRole', '')}

Wikipedia text:
{wiki_extract}

Respond with ONLY a JSON object in this exact format:
{{
  "bio": "Write a 200-500 word English biography. Empty string if insufficient information."
}}

IMPORTANT:
- Only use information explicitly mentioned in the Wikipedia text
- Do not infer, assume, or add information not present
- Write in neutral, encyclopedic tone
- Focus on political career and achievements
- If Wikipedia text is too short or lacks information, return empty string ""
- Keep between 200-500 words"""

        try:
            with self.rate_limiter:
                response = self._call_claude_simple(prompt)
                bio_data = json.loads(response)
                if bio_data.get('bio'):
                    result["bio"] = bio_data['bio']
                    result["sources"].append({
                        "sourceName": "Wikipedia",
                        "sourceUrl": wiki.get('url', ''),
                        "reliability": "high"
                    })
        except Exception as e:
            logger.warning(f"Failed to create biography for {person.get('name', '')}: {e}")

        self.cache[cache_key] = result
        self._save_cache()
        return result

    def _extract_organization(self, person: Dict, wiki: Dict) -> Dict:
        """
        Extract current organization from Wikipedia data only.
        No AI inference - only use reliable sources.
        """
        cache_key = f"{person.get('name', '')}_organization"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = {
            "organization": "",
            "sources": []
        }

        current_role = person.get('currentRole', '')

        if not wiki:
            self.cache[cache_key] = result
            self._save_cache()
            return result

        # Get relevant text chunks - prioritize intro and recent career sections
        # Increased from 2000 to 4000 for better organization extraction
        wiki_extract = self._get_relevant_text(
            wiki,
            keywords=['current', 'serves', 'member', 'senator', 'representative', current_role.lower()],
            max_chars=4000
        )

        if not wiki_extract:
            self.cache[cache_key] = result
            self._save_cache()
            return result

        # Use AI to extract organization from Wikipedia text
        prompt = f"""Based ONLY on the following Wikipedia text, extract the current organization/institution this person works for.

Person: {person.get('name', '')}
Current Role: {current_role}

Wikipedia text:
{wiki_extract}

Respond with ONLY a JSON object in this exact format:
{{
  "organization": "Full official name of the organization (e.g., 'White House', 'U.S. Department of State', 'U.S. Senate'). Empty string if no current organization found."
}}

IMPORTANT:
- Extract the CURRENT organization where this person works
- Use the official English name of the organization
- Only extract information explicitly mentioned in the Wikipedia text
- Common organizations: White House, U.S. Senate, U.S. House of Representatives, U.S. Department of [Name], CIA, FBI, etc.
- If the person is retired or no current position mentioned, return empty string ""
- Do not infer or guess - only extract what is clearly stated"""

        try:
            with self.rate_limiter:
                response = self._call_claude_simple(prompt)
                org_data = json.loads(response)
                if org_data.get('organization'):
                    result["organization"] = org_data['organization']
                    result["sources"].append({
                        "sourceName": "Wikipedia",
                        "sourceUrl": wiki.get('url', ''),
                        "reliability": "high"
                    })
        except Exception as e:
            logger.warning(f"Failed to extract organization for {person.get('name', '')}: {e}")

        self.cache[cache_key] = result
        self._save_cache()
        return result

    def _call_claude_simple(self, prompt: str) -> str:
        """
        Simple API call for single-stage processing.
        Returns raw text response.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.1,  # Very low temperature for factual extraction
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        response_text = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        return response_text

    # Legacy methods - kept for reference but no longer used
    # The new implementation uses _enhance_basic_info, _enhance_education,
    # _enhance_career_history, and _enhance_biography instead

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
        return result[0] if result else {
            "name": person.get('name', ''),
            "dateOfBirth": None,
            "gender": "",
            "party": "",
            "education": "",
            "careerHistory": "",
            "bio": "",
            "sources": []
        }


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
