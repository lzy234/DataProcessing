"""Organization hierarchy analyzer using AI to determine parent-child relationships."""
import json
from typing import Dict, List, Optional
from openai import OpenAI
from src.utils.logger import logger
from src.utils.retry import retry_with_backoff
from src.utils.rate_limiter import RateLimiter
from src.config.settings import Settings


class OrganizationHierarchyAnalyzer:
    """Uses AI to analyze organization hierarchies based on Wikipedia data."""

    def __init__(self):
        """Initialize hierarchy analyzer with AI client."""
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
        self.cache_file = Settings.INTERMEDIATE_DIR / "organization_hierarchy_cache.json"
        self.cache = self._load_cache()

        logger.info("Initialized OrganizationHierarchyAnalyzer")

    def _load_cache(self) -> Dict:
        """Load cached hierarchy analysis."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached hierarchy analyses")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load hierarchy cache: {e}")
        return {}

    def _save_cache(self):
        """Save hierarchy cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self.cache)} hierarchy analyses to cache")
        except Exception as e:
            logger.error(f"Failed to save hierarchy cache: {e}")

    def analyze_batch_hierarchies(
        self,
        organizations: Dict[str, Dict],
        wikipedia_data: Dict[str, Dict]
    ) -> Dict[str, Optional[str]]:
        """
        Analyze hierarchies for a batch of organizations.

        Args:
            organizations: Dictionary of organization data keyed by name
            wikipedia_data: Wikipedia data for people (to infer org context)

        Returns:
            Dictionary mapping organization name to parent organization name (or None)
        """
        logger.info(f"Analyzing hierarchies for {len(organizations)} organizations")

        hierarchies = {}

        for org_name in organizations.keys():
            parent = self._analyze_organization_parent(org_name, wikipedia_data)
            hierarchies[org_name] = parent

        logger.info(f"Completed hierarchy analysis: {sum(1 for p in hierarchies.values() if p)} organizations have parents")

        return hierarchies

    def _analyze_organization_parent(
        self,
        org_name: str,
        wikipedia_data: Dict[str, Dict]
    ) -> Optional[str]:
        """
        Determine parent organization for a given organization using AI.

        Args:
            org_name: Organization name to analyze
            wikipedia_data: Wikipedia data for context

        Returns:
            Parent organization name or None if no parent exists
        """
        cache_key = f"parent_{org_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Build context from Wikipedia data about people in this organization
        context_text = self._build_organization_context(org_name, wikipedia_data)

        prompt = f"""Analyze the following organization and determine if it has a parent organization.

Organization: {org_name}

Context from Wikipedia:
{context_text}

Respond with ONLY a JSON object in this exact format:
{{
  "hasParent": true or false,
  "parentOrganization": "Official name of parent organization" or null,
  "reasoning": "Brief explanation of the relationship"
}}

Guidelines for determining parent organizations:
1. U.S. Federal Government is the top-level parent for all federal agencies, departments, and branches
2. Executive departments (State, Defense, Treasury, etc.) report to U.S. Federal Government
3. Independent agencies (CIA, FBI, EPA, etc.) typically report to U.S. Federal Government
4. Congressional bodies (Senate, House) are part of U.S. Congress, which is part of U.S. Federal Government
5. White House is part of Executive Office of the President, which is part of U.S. Federal Government
6. Committees (Senate Judiciary Committee) are part of their parent body (U.S. Senate)
7. Private companies, think tanks, NGOs, and media organizations typically have NO parent

IMPORTANT:
- Only return a parent if there is a clear hierarchical reporting relationship
- Use official English names for organizations
- Return null if the organization is top-level or independent
- Do not create artificial hierarchies - if uncertain, return null
- White House, U.S. Senate, U.S. House of Representatives are independent enough to not need parents
- Focus on governmental administrative hierarchies, not just "related to" relationships"""

        try:
            with self.rate_limiter:
                response = self._call_ai(prompt)
                hierarchy_data = json.loads(response)

                parent = None
                if hierarchy_data.get('hasParent') and hierarchy_data.get('parentOrganization'):
                    parent = hierarchy_data['parentOrganization']
                    logger.debug(f"{org_name} -> Parent: {parent} ({hierarchy_data.get('reasoning', '')})")
                else:
                    logger.debug(f"{org_name} -> No parent ({hierarchy_data.get('reasoning', '')})")

                self.cache[cache_key] = parent
                self._save_cache()
                return parent

        except Exception as e:
            logger.warning(f"Failed to analyze hierarchy for {org_name}: {e}")
            self.cache[cache_key] = None
            self._save_cache()
            return None

    def _build_organization_context(
        self,
        org_name: str,
        wikipedia_data: Dict[str, Dict]
    ) -> str:
        """
        Build context about an organization from Wikipedia data.

        Args:
            org_name: Organization name
            wikipedia_data: Wikipedia data for people

        Returns:
            Context text describing the organization
        """
        context_parts = []

        # Find people associated with this organization
        for person_name, wiki_info in wikipedia_data.items():
            extract = wiki_info.get('extract', '')
            if org_name.lower() in extract.lower():
                # Include relevant excerpt
                context_parts.append(f"From {person_name}'s Wikipedia: {extract[:500]}...")
                if len(context_parts) >= 3:  # Limit context to 3 examples
                    break

        if context_parts:
            return "\n\n".join(context_parts)
        else:
            return f"Organization mentioned: {org_name} (no additional context available)"

    def _call_ai(self, prompt: str) -> str:
        """
        Call AI API for hierarchy analysis.

        Args:
            prompt: Analysis prompt

        Returns:
            AI response text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1000,
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


def test_hierarchy_analyzer():
    """Test function for hierarchy analyzer."""
    test_orgs = {
        "U.S. Department of State": {},
        "White House": {},
        "U.S. Senate": {},
        "CIA": {},
        "Senate Judiciary Committee": {},
        "Google": {},
        "Brookings Institution": {}
    }

    test_wiki_data = {
        "Marco Rubio": {
            "extract": "Marco Rubio is an American politician serving as the 72nd United States Secretary of State. The Department of State is responsible for U.S. foreign policy."
        },
        "Chuck Schumer": {
            "extract": "Charles Ellis Schumer is an American politician serving as Senate Majority Leader. He is a member of the U.S. Senate."
        }
    }

    analyzer = OrganizationHierarchyAnalyzer()
    hierarchies = analyzer.analyze_batch_hierarchies(test_orgs, test_wiki_data)

    print("\n=== Organization Hierarchies ===")
    for org, parent in hierarchies.items():
        if parent:
            print(f"{org} -> {parent}")
        else:
            print(f"{org} -> (no parent)")


if __name__ == "__main__":
    test_hierarchy_analyzer()
