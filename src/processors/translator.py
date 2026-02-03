"""Translation engine using Deepseek API for English to Chinese translation."""
import json
from typing import Dict, List, Optional
from openai import OpenAI
from pathlib import Path
from src.utils.logger import logger
from src.utils.retry import retry_with_backoff
from src.utils.rate_limiter import RateLimiter
from src.config.settings import Settings


class DeepseekTranslator:
    """Uses Deepseek API to translate English text to Simplified Chinese."""

    def __init__(self):
        """Initialize Deepseek API client and rate limiter."""
        if not Settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        if not Settings.ANTHROPIC_BASE_URL:
            raise ValueError("ANTHROPIC_BASE_URL not set in environment")

        # Initialize OpenAI client with Deepseek endpoint
        self.client = OpenAI(
            api_key=Settings.ANTHROPIC_API_KEY,
            base_url=Settings.ANTHROPIC_BASE_URL + "/v1",
            timeout=120.0
        )
        logger.info(f"Using Deepseek API endpoint: {Settings.ANTHROPIC_BASE_URL}/v1")

        self.rate_limiter = RateLimiter(
            max_calls=Settings.MAX_CLAUDE_REQUESTS_PER_MINUTE,
            period=60
        )

        # Use AI model from settings (deepseek-chat for structured data)
        self.model = Settings.AI_MODEL

        # Load cache if exists
        self.cache_file = Settings.INTERMEDIATE_DIR / "translation_cache.json"
        self.cache = self._load_cache()

        # Statistics tracking
        self.stats = {
            "api_calls": 0,
            "cache_hits": 0,
            "translations": 0,
            "failures": 0
        }

        logger.info(f"Initialized DeepseekTranslator with model {self.model}")

    def _load_cache(self) -> Dict:
        """Load cached translations from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached translations")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load translation cache: {e}")
        return {}

    def _save_cache(self):
        """Save translation cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self.cache)} translations to cache")
        except Exception as e:
            logger.error(f"Failed to save translation cache: {e}")

    def _generate_cache_key(self, text: str, field_name: str, entity_type: str) -> str:
        """Generate unique cache key for translation."""
        # Use hash of text + field + type for shorter keys
        import hashlib
        content = f"{entity_type}:{field_name}:{text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()

    @retry_with_backoff(max_retries=3, initial_delay=2.0)
    def _call_api(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Call Deepseek API with retry logic.

        Args:
            prompt: Translation prompt
            max_tokens: Maximum tokens in response

        Returns:
            API response text
        """
        self.rate_limiter.wait_if_needed()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator specializing in political and governmental terminology. Translate English to Simplified Chinese accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent translations
                max_tokens=max_tokens
            )

            self.stats["api_calls"] += 1
            result = response.choices[0].message.content.strip()
            logger.debug(f"API call successful, response length: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise

    def translate_field(
        self,
        text: str,
        field_name: str,
        entity_type: str,
        entity_name: str = ""
    ) -> str:
        """
        Translate a single field from English to Chinese.

        Args:
            text: English text to translate
            field_name: Name of the field (e.g., "bio", "currentRole")
            entity_type: Type of entity (e.g., "Person", "Organization")
            entity_name: Name of the entity for context

        Returns:
            Chinese translation
        """
        # Handle non-string values (e.g., pandas NaN)
        if not isinstance(text, str):
            return ""

        if not text or not text.strip():
            return ""

        # Check cache first
        cache_key = self._generate_cache_key(text, field_name, entity_type)
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            logger.debug(f"Cache hit for {entity_type}.{field_name}")
            return self.cache[cache_key]

        # Build context-aware prompt
        prompt = f"""Translate the following English text to Simplified Chinese.

Context:
- Entity Type: {entity_type}
- Field Name: {field_name}
{f'- Entity Name: {entity_name}' if entity_name else ''}

English Text:
{text}

Translation Requirements:
1. Use Simplified Chinese (简体中文)
2. Maintain professional tone and accuracy
3. Preserve ALL formatting (line breaks, bullet points, numbers)
4. Keep proper nouns in English where appropriate (e.g., "CIA", "FBI", "MIT")
5. For titles/roles, use standard Chinese governmental terminology
6. For organization names, use official Chinese names if they exist
7. Do NOT add explanations or notes
8. Return ONLY the Chinese translation

Chinese Translation:
"""

        try:
            translation = self._call_api(prompt)

            # Cache the translation
            self.cache[cache_key] = translation
            self._save_cache()

            self.stats["translations"] += 1
            logger.debug(f"Translated {entity_type}.{field_name}")
            return translation

        except Exception as e:
            logger.error(f"Translation failed for {entity_type}.{field_name}: {e}")
            self.stats["failures"] += 1
            return ""

    def translate_batch(
        self,
        items: List[Dict],
        fields_to_translate: List[str],
        entity_type: str
    ) -> List[Dict]:
        """
        Translate multiple items in a single API call for efficiency.

        Args:
            items: List of dictionaries containing fields to translate
            fields_to_translate: List of field names to translate
            entity_type: Type of entity (e.g., "Person", "Organization")

        Returns:
            List of dictionaries with translated fields added (field_name_zh)
        """
        if not items:
            return []

        # Prepare batch data for translation
        batch_data = []
        for idx, item in enumerate(items):
            item_data = {"_index": idx}
            for field in fields_to_translate:
                field_value = item.get(field, "")
                # Check if value is string and not empty (handle pandas NaN)
                if field_value and isinstance(field_value, str) and field_value.strip():
                    item_data[field] = field_value
            batch_data.append(item_data)

        # Build batch translation prompt
        prompt = f"""You are a professional translator specializing in political and governmental terminology. Translate the following fields from English to Simplified Chinese.

Respond with ONLY a JSON array of objects with Chinese translations. Keep the exact same structure.

Input JSON:
{json.dumps(batch_data, ensure_ascii=False, indent=2)}

Translation Requirements:
1. Use Simplified Chinese (简体中文)
2. Maintain professional tone and accuracy
3. Preserve formatting (line breaks, bullets)
4. Keep proper nouns in English where appropriate (CIA, FBI, MIT)
5. Use standard Chinese governmental terminology
6. Use official Chinese names for organizations if they exist
7. For each field in the input, create a corresponding field with "_zh" suffix containing the Chinese translation
8. Keep the "_index" field unchanged
9. If a field is empty or not present, omit it or leave empty

Example output structure:
[
  {{
    "_index": 0,
    "fieldName": "original English text",
    "fieldName_zh": "中文翻译"
  }}
]

Respond with the JSON array:
"""

        try:
            response = self._call_api(prompt, max_tokens=8000)

            # Parse JSON response
            # Clean response in case there's markdown code blocks
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            translated_data = json.loads(response)

            # Merge translations back to original items
            results = []
            for item in items:
                result = item.copy()
                results.append(result)

            # Add translated fields to results
            for trans_item in translated_data:
                idx = trans_item.get("_index", -1)
                if idx >= 0 and idx < len(results):
                    for field in fields_to_translate:
                        zh_field = f"{field}_zh"
                        if zh_field in trans_item:
                            results[idx][zh_field] = trans_item[zh_field]
                        else:
                            results[idx][zh_field] = ""

            self.stats["translations"] += len(items) * len(fields_to_translate)
            logger.info(f"Batch translated {len(items)} {entity_type} items")
            return results

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse batch translation JSON: {e}")
            logger.error(f"Response was: {response[:500]}")
            # Fallback to individual field translation
            return self._translate_batch_fallback(items, fields_to_translate, entity_type)
        except Exception as e:
            logger.error(f"Batch translation failed: {e}")
            # Fallback to individual field translation
            return self._translate_batch_fallback(items, fields_to_translate, entity_type)

    def _translate_batch_fallback(
        self,
        items: List[Dict],
        fields_to_translate: List[str],
        entity_type: str
    ) -> List[Dict]:
        """
        Fallback method: translate fields individually if batch translation fails.

        Args:
            items: List of dictionaries containing fields to translate
            fields_to_translate: List of field names to translate
            entity_type: Type of entity

        Returns:
            List of dictionaries with translated fields added
        """
        logger.warning(f"Using fallback individual translation for {len(items)} items")
        results = []

        for item in items:
            result = item.copy()
            entity_name = item.get("name", "") or item.get("ChineseName", "")

            for field in fields_to_translate:
                field_value = item.get(field, "")
                zh_field = f"{field}_zh"

                # Convert to string and check if not empty
                if field_value and isinstance(field_value, str) and field_value.strip():
                    translation = self.translate_field(
                        field_value,
                        field,
                        entity_type,
                        entity_name
                    )
                    result[zh_field] = translation
                else:
                    result[zh_field] = ""

            results.append(result)

        return results

    def translate_organization_name(self, org_name: str, sector: str = "") -> str:
        """
        Translate organization name using official Chinese names where available.

        Args:
            org_name: English organization name
            sector: Organization sector for context

        Returns:
            Chinese translation
        """
        if not org_name or not org_name.strip():
            return ""

        # Check cache first
        cache_key = self._generate_cache_key(org_name, "organization_name", "Organization")
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[cache_key]

        prompt = f"""Translate the following organization name to Chinese. If an official Chinese name exists, use it. Otherwise, provide a natural Chinese translation.

Organization: {org_name}
{f'Context: This is a {sector} organization in the United States.' if sector else ''}

Examples:
- "White House" → "白宫"
- "U.S. Senate" → "美国参议院"
- "CIA" → "中央情报局"
- "Department of State" → "国务院"
- "FBI" → "联邦调查局"
- "Pentagon" → "五角大楼"

Respond with ONLY the Chinese name, no explanations:
"""

        try:
            translation = self._call_api(prompt, max_tokens=100)

            # Cache the translation
            self.cache[cache_key] = translation
            self._save_cache()

            self.stats["translations"] += 1
            return translation

        except Exception as e:
            logger.error(f"Organization name translation failed for '{org_name}': {e}")
            self.stats["failures"] += 1
            return ""

    def get_stats(self) -> Dict:
        """
        Get translation statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "api_calls": self.stats["api_calls"],
            "cache_hits": self.stats["cache_hits"],
            "translations": self.stats["translations"],
            "failures": self.stats["failures"],
            "cache_size": len(self.cache)
        }
