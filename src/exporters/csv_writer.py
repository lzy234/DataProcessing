"""CSV export functionality for all entity types."""
import csv
import json
from pathlib import Path
from typing import Dict, List
from src.utils.logger import logger
from src.config.settings import Settings


class CSVWriter:
    """
    Write entities to CSV files matching Payload CMS schema.

    Generates 4 CSV files:
    - People.csv
    - Organizations.csv
    - Parties.csv
    - Sectors.csv
    """

    def __init__(self, output_dir: Path = None):
        """
        Initialize CSV writer.

        Args:
            output_dir: Directory for output files (defaults to Settings.OUTPUT_DIR)
        """
        self.output_dir = output_dir or Settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.encoding = Settings.OUTPUT_ENCODING

        logger.info(f"Initialized CSVWriter with output dir: {self.output_dir}")

    def write_all(self, entities: Dict) -> Dict[str, Path]:
        """
        Write all entity types to CSV files.

        Args:
            entities: Dictionary with people, organizations, parties, sectors

        Returns:
            Dictionary mapping entity type to output file path
        """
        logger.info("Writing all entities to CSV files")

        output_files = {}

        output_files['people'] = self.write_people(entities['people'])
        output_files['organizations'] = self.write_organizations(entities['organizations'])
        output_files['parties'] = self.write_parties(entities['parties'])
        output_files['sectors'] = self.write_sectors(entities['sectors'])

        logger.info(f"Successfully wrote {len(output_files)} CSV files")
        return output_files

    def write_people(self, people: List[Dict]) -> Path:
        """
        Write People.csv with full schema.

        Schema:
        - id: P001, P002, etc.
        - name: English name
        - ChineseName: Chinese name
        - dateOfBirth: YYYY-MM-DD or empty
        - gender: male/female/other
        - currentRole: Current position/title
        - organization: Organization ID (O001, etc.)
        - party: Party ID (PTY001, etc.)
        - education: Education summary
        - careerHistory: Career timeline
        - bio: English biography
        - sources: JSON string with source array
        - slug: URL-friendly slug (generated from name)

        Args:
            people: List of person dictionaries

        Returns:
            Path to written CSV file
        """
        output_file = self.output_dir / "People.csv"

        fieldnames = [
            'id',
            'name',
            'ChineseName',
            'dateOfBirth',
            'gender',
            'currentRole',
            'organization',
            'party',
            'education',
            'careerHistory',
            'bio',
            'sources',
            'slug'
        ]

        with open(output_file, 'w', newline='', encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for person in people:
                row = self._prepare_person_row(person, fieldnames)
                writer.writerow(row)

        logger.info(f"Wrote {len(people)} people to {output_file}")
        return output_file

    def _prepare_person_row(self, person: Dict, fieldnames: List[str]) -> Dict:
        """
        Prepare person data for CSV row.

        Args:
            person: Person dictionary
            fieldnames: Expected CSV field names

        Returns:
            Dictionary with CSV row data
        """
        row = {}

        for field in fieldnames:
            if field == 'sources':
                # Convert sources to JSON string
                sources = person.get('sources', [])
                if sources:
                    row['sources'] = json.dumps(sources, ensure_ascii=False)
                else:
                    row['sources'] = '[]'

            elif field == 'slug':
                # Generate slug from name
                name = person.get('name', '')
                row['slug'] = self._generate_slug(name)

            elif field == 'dateOfBirth':
                # Ensure proper format or empty string
                dob = person.get('dateOfBirth')
                row['dateOfBirth'] = dob if dob else ''

            else:
                # Use value or empty string
                value = person.get(field, '')
                row[field] = value if value is not None else ''

        return row

    def write_organizations(self, organizations: List[Dict]) -> Path:
        """
        Write Organizations.csv.

        Schema:
        - id: O001, O002, etc.
        - name: Organization name
        - parentOrganization: Parent organization ID or empty
        - sector: Sector ID (SEC001, etc.)
        - description: Organization description

        Args:
            organizations: List of organization dictionaries

        Returns:
            Path to written CSV file
        """
        output_file = self.output_dir / "Organizations.csv"

        fieldnames = [
            'id',
            'name',
            'parentOrganization',
            'sector',
            'description'
        ]

        with open(output_file, 'w', newline='', encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for org in organizations:
                row = self._prepare_organization_row(org, fieldnames)
                writer.writerow(row)

        logger.info(f"Wrote {len(organizations)} organizations to {output_file}")
        return output_file

    def _prepare_organization_row(self, org: Dict, fieldnames: List[str]) -> Dict:
        """Prepare organization data for CSV row."""
        row = {}

        for field in fieldnames:
            value = org.get(field, '')
            row[field] = value if value is not None else ''

        return row

    def write_parties(self, parties: List[Dict]) -> Path:
        """
        Write Parties.csv.

        Schema:
        - id: PTY001, PTY002, etc.
        - name: Party name
        - abbreviation: R, D, I, etc.
        - color: Hex color code (#RRGGBB)

        Args:
            parties: List of party dictionaries

        Returns:
            Path to written CSV file
        """
        output_file = self.output_dir / "Parties.csv"

        fieldnames = [
            'id',
            'name',
            'abbreviation',
            'color'
        ]

        with open(output_file, 'w', newline='', encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for party in parties:
                row = self._prepare_party_row(party, fieldnames)
                writer.writerow(row)

        logger.info(f"Wrote {len(parties)} parties to {output_file}")
        return output_file

    def _prepare_party_row(self, party: Dict, fieldnames: List[str]) -> Dict:
        """Prepare party data for CSV row."""
        row = {}

        for field in fieldnames:
            value = party.get(field, '')
            row[field] = value if value is not None else ''

        return row

    def write_sectors(self, sectors: List[Dict]) -> Path:
        """
        Write Sectors.csv.

        Schema:
        - id: SEC001, SEC002, etc.
        - name: Sector name
        - category: gov, finance, tech, etc.
        - description: Sector description

        Args:
            sectors: List of sector dictionaries

        Returns:
            Path to written CSV file
        """
        output_file = self.output_dir / "Sectors.csv"

        fieldnames = [
            'id',
            'name',
            'category',
            'description'
        ]

        with open(output_file, 'w', newline='', encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for sector in sectors:
                row = self._prepare_sector_row(sector, fieldnames)
                writer.writerow(row)

        logger.info(f"Wrote {len(sectors)} sectors to {output_file}")
        return output_file

    def _prepare_sector_row(self, sector: Dict, fieldnames: List[str]) -> Dict:
        """Prepare sector data for CSV row."""
        row = {}

        for field in fieldnames:
            value = sector.get(field, '')
            row[field] = value if value is not None else ''

        return row

    def _generate_slug(self, name: str) -> str:
        """
        Generate URL-friendly slug from name.

        Args:
            name: Person or entity name

        Returns:
            Lowercase slug with hyphens
        """
        if not name:
            return ''

        # Convert to lowercase and replace spaces with hyphens
        slug = name.lower()
        slug = slug.replace(' ', '-')

        # Remove special characters except hyphens
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')

        # Remove consecutive hyphens
        while '--' in slug:
            slug = slug.replace('--', '-')

        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        return slug


def test_csv_writer():
    """Test function for CSV writer."""
    # Sample test data
    test_data = {
        'people': [
            {
                'id': 'P001',
                'name': 'Nancy Pelosi',
                'ChineseName': '南希·佩洛西',
                'dateOfBirth': '1940-03-26',
                'gender': 'female',
                'currentRole': 'Speaker of the House (D-CA)',
                'organization': 'O001',
                'party': 'PTY001',
                'education': 'Trinity College',
                'careerHistory': 'Speaker 2019-2023, Minority Leader 2011-2019',
                'bio': 'American politician serving as Speaker...',
                'sources': [
                    {
                        'sourceName': 'Wikipedia',
                        'sourceUrl': 'https://en.wikipedia.org/wiki/Nancy_Pelosi',
                        'reliability': 'high'
                    }
                ]
            }
        ],
        'organizations': [
            {
                'id': 'O001',
                'name': 'U.S. House of Representatives',
                'parentOrganization': None,
                'sector': 'SEC001',
                'description': 'Lower chamber of Congress'
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
                'category': 'gov',
                'description': 'Legislative branch of government'
            }
        ]
    }

    writer = CSVWriter()
    output_files = writer.write_all(test_data)

    print("\n=== Output Files ===")
    for entity_type, filepath in output_files.items():
        print(f"{entity_type}: {filepath}")
        print(f"  Exists: {filepath.exists()}")


if __name__ == "__main__":
    test_csv_writer()
