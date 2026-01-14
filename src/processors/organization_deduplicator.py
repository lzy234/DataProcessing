"""AI-powered organization deduplication and normalization."""
import json
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from src.utils.logger import logger
from src.utils.rate_limiter import RateLimiter
from src.config.settings import Settings


class OrganizationDeduplicator:
    """Uses AI to detect and merge duplicate organizations with different names."""

    def __init__(self):
        """Initialize deduplicator with AI client."""
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

        self.rate_limiter = RateLimiter(
            max_calls=Settings.MAX_CLAUDE_REQUESTS_PER_MINUTE,
            period=60
        )
        self.model = "deepseek-chat"

        # Load cache
        self.cache_file = Settings.INTERMEDIATE_DIR / "organization_dedup_cache.json"
        self.cache = self._load_cache()

        logger.info("Initialized OrganizationDeduplicator")

    def _load_cache(self) -> Dict:
        """Load cached deduplication mappings."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached deduplication mappings")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load dedup cache: {e}")
        return {}

    def _save_cache(self):
        """Save deduplication cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self.cache)} deduplication mappings to cache")
        except Exception as e:
            logger.error(f"Failed to save dedup cache: {e}")

    def deduplicate_organizations(
        self,
        organizations: Dict[str, Dict]
    ) -> Tuple[Dict[str, Dict], Dict[str, str]]:
        """
        Deduplicate organizations using AI to identify variants of the same organization.

        Args:
            organizations: Dictionary of organization data keyed by name

        Returns:
            Tuple of:
            - Deduplicated organizations dictionary (canonical names only)
            - Mapping from original names to canonical names
        """
        if len(organizations) <= 1:
            # No need to deduplicate
            mapping = {name: name for name in organizations.keys()}
            return organizations, mapping

        logger.info(f"Deduplicating {len(organizations)} organizations using AI")

        # Get all organization names
        org_names = list(organizations.keys())

        # Build deduplication mapping
        canonical_mapping = {}  # original_name -> canonical_name

        # Batch process organization names to find duplicates
        duplicate_groups = self._find_duplicate_groups(org_names)

        # Build mapping from each variant to its canonical name
        # Also track which variants exist in the original organizations dict
        variant_to_source = {}  # canonical_name -> first existing variant in organizations
        for canonical_name, variants in duplicate_groups.items():
            # Find first variant that exists in organizations
            source_variant = None
            for variant in variants:
                if variant in organizations:
                    source_variant = variant
                    break

            if source_variant:
                variant_to_source[canonical_name] = source_variant
                for variant in variants:
                    canonical_mapping[variant] = canonical_name

        # Add non-duplicate organizations to mapping (map to themselves)
        for name in org_names:
            if name not in canonical_mapping:
                canonical_mapping[name] = name
                variant_to_source[name] = name

        # Create deduplicated organizations dict with only canonical names
        deduplicated = {}
        for original_name, canonical_name in canonical_mapping.items():
            if canonical_name not in deduplicated:
                # Use the data from the source variant that exists in organizations
                source_name = variant_to_source.get(canonical_name, original_name)
                if source_name in organizations:
                    deduplicated[canonical_name] = organizations[source_name].copy()
                    deduplicated[canonical_name]['name'] = canonical_name

        logger.info(
            f"Deduplication complete: {len(organizations)} -> {len(deduplicated)} "
            f"(merged {len(organizations) - len(deduplicated)} duplicates)"
        )

        return deduplicated, canonical_mapping

    def _find_duplicate_groups(self, org_names: List[str]) -> Dict[str, List[str]]:
        """
        Use AI to identify groups of organization names that refer to the same entity.

        Args:
            org_names: List of organization names to check for duplicates

        Returns:
            Dictionary mapping canonical name -> list of variant names (including canonical)
        """
        # Check cache first
        cache_key = "|".join(sorted(org_names))
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Build prompt for AI
        org_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(org_names)])

        prompt = f"""Analyze the following list of organization names and identify which ones refer to the same organization.

Organization Names:
{org_list}

Task: Identify groups of names that refer to the same organization. Common patterns:
- Full name vs abbreviation (e.g., "Central Intelligence Agency" vs "CIA")
- With/without country prefix (e.g., "Department of State" vs "U.S. Department of State")
- Variations in punctuation/spacing (e.g., "U.S. Senate" vs "US Senate")
- Different but equivalent names (e.g., "White House" vs "Executive Residence")

Respond with ONLY a JSON object in this exact format:
{{
  "duplicateGroups": [
    {{
      "canonicalName": "Official full name to use",
      "variants": ["variant1", "variant2", "variant3"]
    }}
  ]
}}

IMPORTANT:
- Only group names if they DEFINITELY refer to the same organization
- Choose the most official/formal name as the canonical name
- Include the canonical name in the variants list
- If no duplicates found, return empty duplicateGroups array
- Be conservative - when in doubt, do NOT merge
- U.S. Department of X and Department of X are the same (prefer "U.S. Department of X")
- Abbreviations and full names of the same org should be merged (prefer full name)
"""

        try:
            with self.rate_limiter:
                response = self._call_ai(prompt)
                result = json.loads(response)

                # Convert to dict format: canonical_name -> [variants]
                duplicate_groups = {}
                for group in result.get('duplicateGroups', []):
                    canonical = group.get('canonicalName', '')
                    variants = group.get('variants', [])
                    if canonical and variants:
                        duplicate_groups[canonical] = variants

                logger.info(f"Found {len(duplicate_groups)} duplicate groups")
                for canonical, variants in duplicate_groups.items():
                    logger.debug(f"  {canonical}: {len(variants)} variants")

                # Cache the result
                self.cache[cache_key] = duplicate_groups
                self._save_cache()

                return duplicate_groups

        except Exception as e:
            logger.warning(f"Failed to deduplicate organizations: {e}")
            # Return empty dict (no duplicates found)
            self.cache[cache_key] = {}
            self._save_cache()
            return {}

    def _call_ai(self, prompt: str) -> str:
        """
        Call AI API for deduplication analysis.

        Args:
            prompt: Analysis prompt

        Returns:
            AI response text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.1,  # Very low temperature for factual analysis
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


def test_deduplicator():
    """Test function for organization deduplicator."""
    test_orgs = {
        "U.S. Department of State": {
            "name": "U.S. Department of State",
            "sector": "Government - Executive",
            "parentOrganization": "U.S. Federal Government"
        },
        "Department of State": {
            "name": "Department of State",
            "sector": "Government - Executive",
            "parentOrganization": None
        },
        "State Department": {
            "name": "State Department",
            "sector": "Government - Executive",
            "parentOrganization": None
        },
        "CIA": {
            "name": "CIA",
            "sector": "Government - Intelligence",
            "parentOrganization": "U.S. Federal Government"
        },
        "Central Intelligence Agency": {
            "name": "Central Intelligence Agency",
            "sector": "Government - Intelligence",
            "parentOrganization": "U.S. Federal Government"
        },
        "White House": {
            "name": "White House",
            "sector": "Government - Executive",
            "parentOrganization": None
        },
        "U.S. Senate": {
            "name": "U.S. Senate",
            "sector": "Government - Legislative",
            "parentOrganization": None
        },
        "United States Senate": {
            "name": "United States Senate",
            "sector": "Government - Legislative",
            "parentOrganization": None
        }
    }

    deduplicator = OrganizationDeduplicator()
    deduplicated, mapping = deduplicator.deduplicate_organizations(test_orgs)

    print("\n=== Deduplication Results ===")
    print(f"Original count: {len(test_orgs)}")
    print(f"Deduplicated count: {len(deduplicated)}")
    print(f"\n=== Deduplicated Organizations ===")
    for org_name in sorted(deduplicated.keys()):
        print(f"- {org_name}")

    print(f"\n=== Name Mappings ===")
    for original, canonical in sorted(mapping.items()):
        if original != canonical:
            print(f"{original} -> {canonical}")


if __name__ == "__main__":
    test_deduplicator()
