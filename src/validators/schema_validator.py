"""Data validation and quality checking."""
import json
import re
from typing import Dict, List, Set, Tuple
from datetime import datetime
from src.utils.logger import logger
from src.config.settings import Settings


class SchemaValidator:
    """
    Validates data completeness and schema compliance.

    Checks:
    - Required fields presence
    - Date format validation
    - Referential integrity
    - Organization hierarchy (no circular references)
    - Data quality metrics
    """

    def __init__(self):
        """Initialize schema validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict = {}

        logger.info("Initialized SchemaValidator")

    def validate_all(self, entities: Dict) -> Dict:
        """
        Validate all entities and generate quality report.

        Args:
            entities: Dictionary with people, organizations, parties, sectors

        Returns:
            Validation report with errors, warnings, and statistics
        """
        logger.info("Starting validation")

        self.errors = []
        self.warnings = []
        self.stats = {}

        # Validate each entity type
        self._validate_people(entities['people'])
        self._validate_organizations(entities['organizations'])
        self._validate_parties(entities['parties'])
        self._validate_sectors(entities['sectors'])

        # Check referential integrity
        self._validate_references(entities)

        # Generate quality statistics
        self._generate_quality_stats(entities)

        report = {
            'errors': self.errors,
            'warnings': self.warnings,
            'statistics': self.stats,
            'passed': len(self.errors) == 0
        }

        logger.info(
            f"Validation complete: {len(self.errors)} errors, "
            f"{len(self.warnings)} warnings"
        )

        return report

    def _validate_people(self, people: List[Dict]):
        """
        Validate People data.

        Required fields: id, name, currentRole
        Optional but tracked: dateOfBirth, gender, education, careerHistory, bio
        """
        logger.debug(f"Validating {len(people)} people")

        for person in people:
            person_id = person.get('id', 'UNKNOWN')

            # Required fields
            if not person.get('name'):
                self.errors.append(f"Person {person_id}: Missing required field 'name'")

            if not person.get('currentRole'):
                self.errors.append(f"Person {person_id}: Missing required field 'currentRole'")

            # Date format validation
            dob = person.get('dateOfBirth')
            if dob and not self._is_valid_date(dob):
                self.errors.append(f"Person {person_id}: Invalid date format '{dob}'")

            # Gender validation
            gender = person.get('gender')
            if gender and gender not in ['male', 'female', 'other']:
                self.warnings.append(f"Person {person_id}: Invalid gender value '{gender}'")

            # Sources validation
            sources = person.get('sources')
            if isinstance(sources, str):
                try:
                    json.loads(sources)
                except json.JSONDecodeError:
                    self.errors.append(f"Person {person_id}: Invalid JSON in sources field")

    def _validate_organizations(self, organizations: List[Dict]):
        """
        Validate Organizations data.

        Required fields: id, name, sector
        """
        logger.debug(f"Validating {len(organizations)} organizations")

        for org in organizations:
            org_id = org.get('id', 'UNKNOWN')

            # Required fields
            if not org.get('name'):
                self.errors.append(f"Organization {org_id}: Missing required field 'name'")

            if not org.get('sector'):
                self.warnings.append(f"Organization {org_id}: Missing sector assignment")

    def _validate_parties(self, parties: List[Dict]):
        """
        Validate Parties data.

        Required fields: id, name, abbreviation, color
        """
        logger.debug(f"Validating {len(parties)} parties")

        for party in parties:
            party_id = party.get('id', 'UNKNOWN')

            # Required fields
            if not party.get('name'):
                self.errors.append(f"Party {party_id}: Missing required field 'name'")

            if not party.get('abbreviation'):
                self.errors.append(f"Party {party_id}: Missing required field 'abbreviation'")

            # Color format validation
            color = party.get('color')
            if color and not self._is_valid_color(color):
                self.errors.append(f"Party {party_id}: Invalid color format '{color}'")

    def _validate_sectors(self, sectors: List[Dict]):
        """
        Validate Sectors data.

        Required fields: id, name, category
        """
        logger.debug(f"Validating {len(sectors)} sectors")

        for sector in sectors:
            sector_id = sector.get('id', 'UNKNOWN')

            # Required fields
            if not sector.get('name'):
                self.errors.append(f"Sector {sector_id}: Missing required field 'name'")

            if not sector.get('category'):
                self.errors.append(f"Sector {sector_id}: Missing required field 'category'")

    def _validate_references(self, entities: Dict):
        """
        Validate referential integrity.

        Checks:
        - Person -> Organization references valid
        - Person -> Party references valid
        - Organization -> Sector references valid
        - Organization -> Parent Organization valid (no circular refs)
        """
        logger.debug("Validating referential integrity")

        people = entities['people']
        organizations = entities['organizations']
        parties = entities['parties']
        sectors = entities['sectors']

        # Build ID sets for lookup
        org_ids = {org['id'] for org in organizations if org.get('id')}
        party_ids = {party['id'] for party in parties if party.get('id')}
        sector_ids = {sector['id'] for sector in sectors if sector.get('id')}

        # Check person references
        for person in people:
            person_id = person.get('id', 'UNKNOWN')

            org_ref = person.get('organization')
            if org_ref and org_ref not in org_ids:
                self.errors.append(
                    f"Person {person_id}: References non-existent organization '{org_ref}'"
                )

            party_ref = person.get('party')
            if party_ref and party_ref not in party_ids:
                self.errors.append(
                    f"Person {person_id}: References non-existent party '{party_ref}'"
                )

        # Check organization references
        for org in organizations:
            org_id = org.get('id', 'UNKNOWN')

            sector_ref = org.get('sector')
            if sector_ref and sector_ref not in sector_ids:
                self.errors.append(
                    f"Organization {org_id}: References non-existent sector '{sector_ref}'"
                )

            parent_ref = org.get('parentOrganization')
            if parent_ref and parent_ref not in org_ids:
                self.errors.append(
                    f"Organization {org_id}: References non-existent parent '{parent_ref}'"
                )

        # Check for circular references in organization hierarchies
        self._check_circular_org_references(organizations)

    def _check_circular_org_references(self, organizations: List[Dict]):
        """Check for circular references in organization hierarchies."""
        org_map = {org['id']: org for org in organizations if org.get('id')}

        for org in organizations:
            org_id = org.get('id')
            if not org_id:
                continue

            visited = set()
            current = org_id

            # Follow parent chain
            while current:
                if current in visited:
                    self.errors.append(
                        f"Circular reference in organization hierarchy: {org_id}"
                    )
                    break

                visited.add(current)

                # Get parent
                current_org = org_map.get(current)
                if not current_org:
                    break

                current = current_org.get('parentOrganization')

    def _generate_quality_stats(self, entities: Dict):
        """
        Generate data quality statistics.

        Metrics:
        - Field completeness percentages
        - Total counts
        - Quality scores
        """
        people = entities['people']
        total_people = len(people)

        if total_people == 0:
            self.stats = {'error': 'No people to analyze'}
            return

        # Count field completeness
        stats = {
            'total_people': total_people,
            'total_organizations': len(entities['organizations']),
            'total_parties': len(entities['parties']),
            'total_sectors': len(entities['sectors']),
            'field_completeness': {}
        }

        # Check key fields
        fields_to_check = [
            'name', 'ChineseName', 'dateOfBirth', 'gender',
            'currentRole', 'organization', 'party',
            'education', 'careerHistory', 'bio'
        ]

        for field in fields_to_check:
            count = sum(1 for p in people if p.get(field) and str(p.get(field)).strip())
            percentage = (count / total_people) * 100
            stats['field_completeness'][field] = {
                'count': count,
                'percentage': round(percentage, 2)
            }

        # Overall quality score (average of key fields)
        key_fields = ['name', 'dateOfBirth', 'education', 'careerHistory', 'bio']
        quality_scores = [
            stats['field_completeness'][f]['percentage']
            for f in key_fields
            if f in stats['field_completeness']
        ]
        stats['overall_quality_score'] = round(sum(quality_scores) / len(quality_scores), 2)

        self.stats = stats

    def _is_valid_date(self, date_str: str) -> bool:
        """
        Validate date format (YYYY-MM-DD).

        Args:
            date_str: Date string

        Returns:
            True if valid format
        """
        if not date_str:
            return False

        # Check format
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return False

        # Try to parse
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _is_valid_color(self, color: str) -> bool:
        """
        Validate hex color format (#RRGGBB).

        Args:
            color: Color string

        Returns:
            True if valid hex color
        """
        if not color:
            return False

        return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))

    def save_report(self, report: Dict, filename: str = "quality_report.json"):
        """
        Save validation report to file.

        Args:
            report: Validation report dictionary
            filename: Output filename
        """
        output_file = Settings.INTERMEDIATE_DIR / filename

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved validation report to {output_file}")


def test_schema_validator():
    """Test function for schema validator."""
    # Sample test data
    test_data = {
        'people': [
            {
                'id': 'P001',
                'name': 'Nancy Pelosi',
                'ChineseName': '南希·佩洛西',
                'dateOfBirth': '1940-03-26',
                'gender': 'female',
                'currentRole': 'Speaker',
                'organization': 'O001',
                'party': 'PTY001',
                'education': 'Trinity College',
                'careerHistory': 'Speaker 2019-2023',
                'bio': 'American politician...'
            },
            {
                'id': 'P002',
                'name': '',  # Missing name (error)
                'dateOfBirth': '1990-13-45',  # Invalid date (error)
                'currentRole': 'Senator'
            }
        ],
        'organizations': [
            {
                'id': 'O001',
                'name': 'U.S. House',
                'sector': 'SEC001'
            }
        ],
        'parties': [
            {
                'id': 'PTY001',
                'name': 'Democratic Party',
                'abbreviation': 'D',
                'color': '#0015BC'
            }
        ],
        'sectors': [
            {
                'id': 'SEC001',
                'name': 'Government - Legislative',
                'category': 'gov'
            }
        ]
    }

    validator = SchemaValidator()
    report = validator.validate_all(test_data)

    print("\n=== Validation Report ===")
    print(f"Passed: {report['passed']}")
    print(f"\nErrors ({len(report['errors'])}):")
    for error in report['errors']:
        print(f"  - {error}")

    print(f"\nWarnings ({len(report['warnings'])}):")
    for warning in report['warnings']:
        print(f"  - {warning}")

    print("\n=== Quality Statistics ===")
    print(json.dumps(report['statistics'], indent=2))


if __name__ == "__main__":
    test_schema_validator()
