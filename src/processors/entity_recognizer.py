"""Entity recognition and extraction from raw text data."""
import re
from typing import Dict, List, Optional, Set
from src.utils.logger import logger
from src.config.settings import Settings


class EntityRecognizer:
    """
    Recognizes and extracts entities from person data.

    Extracts:
    - Organizations (standardized names)
    - Political parties (from title patterns)
    - Sectors (industry classifications)
    - Organization hierarchies
    """

    def __init__(self):
        """Initialize entity recognizer with configuration."""
        self.sector_config = Settings.get_sector_mappings()
        self.party_config = Settings.get_party_colors()

        # Track unique entities
        self.organizations: Dict[str, Dict] = {}
        self.parties: Dict[str, Dict] = {}
        self.sectors: Dict[str, Dict] = {}

        logger.info("Initialized EntityRecognizer")

    def process_all_people(self, people: List[Dict]) -> Dict:
        """
        Process all people and extract entities.

        Args:
            people: List of person dictionaries

        Returns:
            Dictionary with extracted entities:
            {
                'organizations': {...},
                'parties': {...},
                'sectors': {...}
            }
        """
        logger.info(f"Processing {len(people)} people for entity extraction")

        for person in people:
            # Extract organization
            org_text = person.get('organization_text', '')
            if org_text:
                org = self.extract_organization(org_text)
                if org:
                    org_name = org['name']
                    if org_name not in self.organizations:
                        self.organizations[org_name] = org

            # Extract party
            title = person.get('currentRole', '')
            if title:
                party = self.extract_party(title)
                if party:
                    party_name = party['name']
                    if party_name not in self.parties:
                        self.parties[party_name] = party

        # Infer sectors from organizations
        self._infer_sectors_from_organizations()

        logger.info(f"Extracted {len(self.organizations)} organizations, "
                   f"{len(self.parties)} parties, {len(self.sectors)} sectors")

        return {
            'organizations': self.organizations,
            'parties': self.parties,
            'sectors': self.sectors
        }

    def extract_organization(self, org_text: str) -> Optional[Dict]:
        """
        Extract and normalize organization information.

        Handles patterns like:
        - "白宫 (The White House)"
        - "U.S. Senate"
        - "美国众议院 (U.S. House of Representatives)"

        Args:
            org_text: Raw organization text

        Returns:
            Organization dictionary with name, sector, and description
        """
        if not org_text or org_text.strip() == '':
            return None

        # Try to extract English name from parentheses
        english_match = re.search(r'\(([^)]+)\)', org_text)
        if english_match:
            org_name = english_match.group(1).strip()
            chinese_name = re.sub(r'\s*\([^)]+\)', '', org_text).strip()
        else:
            org_name = org_text.strip()
            chinese_name = None

        # Infer sector
        sector = self.infer_sector(org_name)

        # Try to identify parent organization
        parent_org = self._identify_parent_organization(org_name)

        org_data = {
            'name': org_name,
            'chineseName': chinese_name,
            'sector': sector['name'] if sector else None,
            'parentOrganization': parent_org,
            'description': f"Political organization: {org_name}"
        }

        return org_data

    def infer_sector(self, org_name: str) -> Optional[Dict]:
        """
        Infer sector from organization name using keyword matching.

        Args:
            org_name: Organization name

        Returns:
            Sector dictionary with name, category, description
        """
        org_lower = org_name.lower()

        # Try to match against sector keywords
        for sector in self.sector_config['sectors']:
            keywords = sector.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in org_lower:
                    sector_data = {
                        'name': sector['name'],
                        'category': sector['category'],
                        'description': sector.get('description', '')
                    }

                    # Add to sectors dict
                    if sector['name'] not in self.sectors:
                        self.sectors[sector['name']] = sector_data

                    return sector_data

        # Default to Government - Other if no match
        default_sector = {
            'name': 'Government - Other',
            'category': 'gov',
            'description': 'Other government organizations'
        }

        if default_sector['name'] not in self.sectors:
            self.sectors[default_sector['name']] = default_sector

        return default_sector

    def _identify_parent_organization(self, org_name: str) -> Optional[str]:
        """
        Identify parent organization from hierarchical patterns.

        Examples:
        - "Senate Judiciary Committee" -> "U.S. Senate"
        - "House Ways and Means Committee" -> "U.S. House of Representatives"
        - "Department of State" -> "U.S. Federal Government"

        Args:
            org_name: Organization name

        Returns:
            Parent organization name or None
        """
        org_lower = org_name.lower()

        # Congressional committees
        if 'committee' in org_lower:
            if 'senate' in org_lower:
                return 'U.S. Senate'
            elif 'house' in org_lower or 'congress' in org_lower:
                return 'U.S. House of Representatives'

        # Executive departments
        if org_lower.startswith('department of'):
            return 'U.S. Federal Government'

        # Federal agencies
        agency_keywords = ['agency', 'bureau', 'administration', 'commission', 'board']
        if any(kw in org_lower for kw in agency_keywords):
            if 'federal' in org_lower or org_lower.startswith('u.s.'):
                return 'U.S. Federal Government'

        return None

    def extract_party(self, title: str) -> Optional[Dict]:
        """
        Extract political party from title/role.

        Patterns:
        - "Senator (R-TX)" -> Republican
        - "Representative (D-CA)" -> Democratic
        - "Governor (I)" -> Independent

        Args:
            title: Person's title/role

        Returns:
            Party dictionary with name, abbreviation, color
        """
        if not title:
            return None

        # Match party abbreviation in parentheses
        # Patterns: (R-TX), (D-CA), (I), etc.
        party_match = re.search(r'\(([RDI])(?:-[A-Z]{2})?\)', title, re.IGNORECASE)

        if party_match:
            abbr = party_match.group(1).upper()

            # Find matching party in config
            for party in self.party_config['parties']:
                if party['abbreviation'] == abbr:
                    return {
                        'name': party['name'],
                        'abbreviation': party['abbreviation'],
                        'color': party['color']
                    }

        return None

    def _infer_sectors_from_organizations(self):
        """Ensure all organizations have corresponding sectors in sectors dict."""
        for org_name, org in self.organizations.items():
            sector_name = org.get('sector')
            if sector_name and sector_name not in self.sectors:
                # Find sector definition from config
                for sector in self.sector_config['sectors']:
                    if sector['name'] == sector_name:
                        self.sectors[sector_name] = {
                            'name': sector['name'],
                            'category': sector['category'],
                            'description': sector.get('description', '')
                        }
                        break

    def get_organization_by_text(self, org_text: str) -> Optional[str]:
        """
        Get standardized organization name from raw text.

        Args:
            org_text: Raw organization text

        Returns:
            Standardized organization name or None
        """
        org = self.extract_organization(org_text)
        return org['name'] if org else None

    def get_party_by_title(self, title: str) -> Optional[str]:
        """
        Get party name from title.

        Args:
            title: Person's title

        Returns:
            Party name or None
        """
        party = self.extract_party(title)
        return party['name'] if party else None

    def get_all_entities(self) -> Dict:
        """
        Get all extracted entities.

        Returns:
            Dictionary with organizations, parties, and sectors
        """
        return {
            'organizations': list(self.organizations.values()),
            'parties': list(self.parties.values()),
            'sectors': list(self.sectors.values())
        }


def test_entity_recognizer():
    """Test function for entity recognizer."""
    # Sample test data
    test_people = [
        {
            'name': 'Nancy Pelosi',
            'currentRole': 'Speaker of the House (D-CA)',
            'organization_text': '美国众议院 (U.S. House of Representatives)'
        },
        {
            'name': 'Mitch McConnell',
            'currentRole': 'Senate Minority Leader (R-KY)',
            'organization_text': '美国参议院 (U.S. Senate)'
        },
        {
            'name': 'Janet Yellen',
            'currentRole': 'Secretary of the Treasury',
            'organization_text': '美国财政部 (Department of the Treasury)'
        }
    ]

    recognizer = EntityRecognizer()
    entities = recognizer.process_all_people(test_people)

    print("\n=== Organizations ===")
    for org_name, org in entities['organizations'].items():
        print(f"- {org_name}")
        print(f"  Sector: {org.get('sector')}")
        print(f"  Parent: {org.get('parentOrganization')}")

    print("\n=== Parties ===")
    for party_name, party in entities['parties'].items():
        print(f"- {party_name} ({party.get('abbreviation')})")
        print(f"  Color: {party.get('color')}")

    print("\n=== Sectors ===")
    for sector_name, sector in entities['sectors'].items():
        print(f"- {sector_name} ({sector.get('category')})")


if __name__ == "__main__":
    test_entity_recognizer()
