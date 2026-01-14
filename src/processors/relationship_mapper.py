"""Relationship mapping and ID assignment for all entities."""
from typing import Dict, List, Optional, Set
from src.utils.logger import logger


class RelationshipMapper:
    """
    Assigns unique IDs to all entities and establishes relationships.

    ID formats:
    - People: P001, P002, ..., P100
    - Organizations: O001, O002, ...
    - Parties: PTY001, PTY002, ...
    - Sectors: SEC001, SEC002, ...
    """

    def __init__(self):
        """Initialize relationship mapper."""
        # ID mappings: entity_name -> id
        self.person_ids: Dict[str, str] = {}
        self.organization_ids: Dict[str, str] = {}
        self.party_ids: Dict[str, str] = {}
        self.sector_ids: Dict[str, str] = {}

        # Reverse mappings for lookups
        self.id_to_person: Dict[str, str] = {}
        self.id_to_organization: Dict[str, str] = {}
        self.id_to_party: Dict[str, str] = {}
        self.id_to_sector: Dict[str, str] = {}

        logger.info("Initialized RelationshipMapper")

    def assign_all_ids(
        self,
        people: List[Dict],
        organizations: Dict[str, Dict],
        parties: Dict[str, Dict],
        sectors: Dict[str, Dict]
    ) -> Dict:
        """
        Assign unique IDs to all entities.

        Args:
            people: List of person dictionaries
            organizations: Dict of organization data
            parties: Dict of party data
            sectors: Dict of sector data

        Returns:
            Dictionary with ID-assigned entities
        """
        logger.info("Assigning IDs to all entities")

        # Assign IDs
        people_with_ids = self._assign_people_ids(people)
        orgs_with_ids = self._assign_organization_ids(organizations)
        parties_with_ids = self._assign_party_ids(parties)
        sectors_with_ids = self._assign_sector_ids(sectors)

        logger.info(
            f"Assigned IDs: {len(people_with_ids)} people, "
            f"{len(orgs_with_ids)} organizations, "
            f"{len(parties_with_ids)} parties, "
            f"{len(sectors_with_ids)} sectors"
        )

        return {
            'people': people_with_ids,
            'organizations': orgs_with_ids,
            'parties': parties_with_ids,
            'sectors': sectors_with_ids
        }

    def _assign_people_ids(self, people: List[Dict]) -> List[Dict]:
        """
        Assign P### IDs to people.

        Args:
            people: List of person dictionaries

        Returns:
            List of people with assigned IDs
        """
        result = []

        for idx, person in enumerate(people, 1):
            person_id = f"P{idx:03d}"
            name = person.get('name', '')

            # Store mapping
            self.person_ids[name] = person_id
            self.id_to_person[person_id] = name

            # Add ID to person data
            person_with_id = person.copy()
            person_with_id['id'] = person_id

            result.append(person_with_id)

        return result

    def _assign_organization_ids(self, organizations: Dict[str, Dict]) -> List[Dict]:
        """
        Assign O### IDs to organizations.

        Args:
            organizations: Dict of organization data keyed by name

        Returns:
            List of organizations with assigned IDs
        """
        result = []

        for idx, (org_name, org_data) in enumerate(sorted(organizations.items()), 1):
            org_id = f"O{idx:03d}"

            # Store mapping
            self.organization_ids[org_name] = org_id
            self.id_to_organization[org_id] = org_name

            # Add ID to organization data
            org_with_id = org_data.copy()
            org_with_id['id'] = org_id

            result.append(org_with_id)

        return result

    def _assign_party_ids(self, parties: Dict[str, Dict]) -> List[Dict]:
        """
        Assign PTY### IDs to parties.

        Args:
            parties: Dict of party data keyed by name

        Returns:
            List of parties with assigned IDs
        """
        result = []

        for idx, (party_name, party_data) in enumerate(sorted(parties.items()), 1):
            party_id = f"PTY{idx:03d}"

            # Store mapping
            self.party_ids[party_name] = party_id
            self.id_to_party[party_id] = party_name

            # Add ID to party data
            party_with_id = party_data.copy()
            party_with_id['id'] = party_id

            result.append(party_with_id)

        return result

    def _assign_sector_ids(self, sectors: Dict[str, Dict]) -> List[Dict]:
        """
        Assign SEC### IDs to sectors.

        Args:
            sectors: Dict of sector data keyed by name

        Returns:
            List of sectors with assigned IDs
        """
        result = []

        for idx, (sector_name, sector_data) in enumerate(sorted(sectors.items()), 1):
            sector_id = f"SEC{idx:03d}"

            # Store mapping
            self.sector_ids[sector_name] = sector_id
            self.id_to_sector[sector_id] = sector_name

            # Add ID to sector data
            sector_with_id = sector_data.copy()
            sector_with_id['id'] = sector_id

            result.append(sector_with_id)

        return result

    def map_relationships(self, entities: Dict) -> Dict:
        """
        Map relationships between entities using IDs.

        Args:
            entities: Dictionary with people, organizations, parties, sectors

        Returns:
            Updated entities with relationship IDs mapped
        """
        logger.info("Mapping entity relationships")

        people = entities['people']
        organizations = entities['organizations']
        parties = entities['parties']
        sectors = entities['sectors']

        # Map person -> organization
        people = self._map_person_organizations(people)

        # Map person -> party
        people = self._map_person_parties(people)

        # Map organization -> sector
        organizations = self._map_organization_sectors(organizations)

        # Map organization -> parent organization
        organizations = self._map_organization_hierarchies(organizations)

        logger.info("Completed relationship mapping")

        return {
            'people': people,
            'organizations': organizations,
            'parties': parties,
            'sectors': sectors
        }

    def _map_person_organizations(self, people: List[Dict]) -> List[Dict]:
        """
        Map person -> organization relationships.

        Args:
            people: List of people with organization field (from AI extraction)

        Returns:
            Updated people with organization ID field
        """
        result = []

        for person in people:
            person_copy = person.copy()
            # Use AI-extracted organization name directly
            org_name = person.get('organization', '').strip()

            if org_name and org_name in self.organization_ids:
                person_copy['organization'] = self.organization_ids[org_name]
            else:
                person_copy['organization'] = None

            result.append(person_copy)

        return result

    def _map_person_parties(self, people: List[Dict]) -> List[Dict]:
        """
        Map person -> party relationships.

        Args:
            people: List of people with currentRole field

        Returns:
            Updated people with party ID field
        """
        result = []

        for person in people:
            person_copy = person.copy()
            title = person.get('currentRole', '')

            if title:
                # Extract party
                from src.processors.entity_recognizer import EntityRecognizer
                recognizer = EntityRecognizer()
                party = recognizer.extract_party(title)

                if party and party['name'] in self.party_ids:
                    person_copy['party'] = self.party_ids[party['name']]
                else:
                    person_copy['party'] = None
            else:
                person_copy['party'] = None

            result.append(person_copy)

        return result

    def _map_organization_sectors(self, organizations: List[Dict]) -> List[Dict]:
        """
        Map organization -> sector relationships.

        Args:
            organizations: List of organizations with sector field (name)

        Returns:
            Updated organizations with sector ID field
        """
        result = []

        for org in organizations:
            org_copy = org.copy()
            sector_name = org.get('sector')

            if sector_name and sector_name in self.sector_ids:
                org_copy['sector'] = self.sector_ids[sector_name]
            else:
                org_copy['sector'] = None

            result.append(org_copy)

        return result

    def _map_organization_hierarchies(self, organizations: List[Dict]) -> List[Dict]:
        """
        Map organization -> parent organization relationships.

        Args:
            organizations: List of organizations with parentOrganization field (name)

        Returns:
            Updated organizations with parent organization ID field
        """
        result = []

        for org in organizations:
            org_copy = org.copy()
            parent_name = org.get('parentOrganization')

            if parent_name and parent_name in self.organization_ids:
                org_copy['parentOrganization'] = self.organization_ids[parent_name]
            else:
                org_copy['parentOrganization'] = None

            result.append(org_copy)

        return result

    def get_person_id(self, name: str) -> Optional[str]:
        """Get person ID by name."""
        return self.person_ids.get(name)

    def get_organization_id(self, name: str) -> Optional[str]:
        """Get organization ID by name."""
        return self.organization_ids.get(name)

    def get_party_id(self, name: str) -> Optional[str]:
        """Get party ID by name."""
        return self.party_ids.get(name)

    def get_sector_id(self, name: str) -> Optional[str]:
        """Get sector ID by name."""
        return self.sector_ids.get(name)

    def validate_references(self, entities: Dict) -> List[str]:
        """
        Validate that all ID references are valid.

        Args:
            entities: Dictionary with all entities

        Returns:
            List of validation error messages
        """
        errors = []

        people = entities['people']
        organizations = entities['organizations']

        # Check person -> organization references
        for person in people:
            org_id = person.get('organization')
            if org_id and org_id not in self.id_to_organization:
                errors.append(
                    f"Person {person.get('id')} references invalid organization ID: {org_id}"
                )

        # Check person -> party references
        for person in people:
            party_id = person.get('party')
            if party_id and party_id not in self.id_to_party:
                errors.append(
                    f"Person {person.get('id')} references invalid party ID: {party_id}"
                )

        # Check organization -> sector references
        for org in organizations:
            sector_id = org.get('sector')
            if sector_id and sector_id not in self.id_to_sector:
                errors.append(
                    f"Organization {org.get('id')} references invalid sector ID: {sector_id}"
                )

        # Check organization -> parent organization references
        for org in organizations:
            parent_id = org.get('parentOrganization')
            if parent_id and parent_id not in self.id_to_organization:
                errors.append(
                    f"Organization {org.get('id')} references invalid parent ID: {parent_id}"
                )

        # Check for circular references in organization hierarchies
        circular_refs = self._detect_circular_references(organizations)
        errors.extend(circular_refs)

        return errors

    def _detect_circular_references(self, organizations: List[Dict]) -> List[str]:
        """
        Detect circular references in organization hierarchies.

        Args:
            organizations: List of organizations

        Returns:
            List of error messages for circular references
        """
        errors = []

        for org in organizations:
            org_id = org.get('id')
            visited = set()
            current = org_id

            # Follow parent chain
            while current:
                if current in visited:
                    errors.append(
                        f"Circular reference detected in organization hierarchy: {org_id}"
                    )
                    break

                visited.add(current)

                # Find parent
                parent = None
                for o in organizations:
                    if o.get('id') == current:
                        parent = o.get('parentOrganization')
                        break

                current = parent

        return errors


def test_relationship_mapper():
    """Test function for relationship mapper."""
    # Sample test data
    test_people = [
        {
            'name': 'Nancy Pelosi',
            'currentRole': 'Speaker (D-CA)',
            'organization_text': 'U.S. House of Representatives'
        },
        {
            'name': 'Joe Biden',
            'currentRole': 'President (D)',
            'organization_text': 'The White House'
        }
    ]

    test_orgs = {
        'U.S. House of Representatives': {
            'name': 'U.S. House of Representatives',
            'sector': 'Government - Legislative',
            'parentOrganization': None
        },
        'The White House': {
            'name': 'The White House',
            'sector': 'Government - Executive',
            'parentOrganization': None
        }
    }

    test_parties = {
        'Democratic Party': {
            'name': 'Democratic Party',
            'abbreviation': 'D',
            'color': '#0015BC'
        }
    }

    test_sectors = {
        'Government - Legislative': {
            'name': 'Government - Legislative',
            'category': 'gov',
            'description': 'Legislative branch'
        },
        'Government - Executive': {
            'name': 'Government - Executive',
            'category': 'gov',
            'description': 'Executive branch'
        }
    }

    mapper = RelationshipMapper()

    # Assign IDs
    entities = mapper.assign_all_ids(test_people, test_orgs, test_parties, test_sectors)

    # Map relationships
    entities = mapper.map_relationships(entities)

    # Validate
    errors = mapper.validate_references(entities)

    print("\n=== People ===")
    for person in entities['people']:
        print(f"{person.get('id')}: {person.get('name')}")
        print(f"  Organization: {person.get('organization')}")
        print(f"  Party: {person.get('party')}")

    print("\n=== Validation Errors ===")
    if errors:
        for error in errors:
            print(f"- {error}")
    else:
        print("No errors found!")


if __name__ == "__main__":
    test_relationship_mapper()
