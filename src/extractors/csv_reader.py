"""CSV reader for loading the original person data."""
import pandas as pd
from typing import List, Dict
from pathlib import Path
from src.utils.logger import logger
from src.config.settings import Settings


class CSVReader:
    """Read and parse the original person CSV file."""

    def __init__(self, filepath: str = None):
        """
        Initialize CSV reader.

        Args:
            filepath: Path to CSV file (defaults to data/input/人物信息.csv)
        """
        if filepath is None:
            filepath = Settings.INPUT_DIR / "人物信息.csv"
        self.filepath = Path(filepath)

    def read_people_data(self) -> List[Dict]:
        """
        Read CSV with BOM handling.

        Returns:
            List of person dictionaries

        Raises:
            FileNotFoundError: If CSV file doesn't exist
        """
        if not self.filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {self.filepath}")

        logger.info(f"Reading CSV from {self.filepath}")

        # Read CSV with UTF-8-sig encoding to handle BOM
        df = pd.read_csv(self.filepath, encoding='utf-8-sig')

        logger.info(f"Loaded {len(df)} records from CSV")
        logger.info(f"Columns: {list(df.columns)}")

        # Convert to list of dictionaries
        people = df.to_dict('records')

        # Extract basic fields
        processed_people = []
        for idx, row in enumerate(people, 1):
            try:
                person = self.extract_basic_fields(row, idx)
                processed_people.append(person)
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                logger.debug(f"Row data: {row}")

        logger.info(f"Successfully processed {len(processed_people)} people")
        return processed_people

    def extract_basic_fields(self, row: Dict, idx: int) -> Dict:
        """
        Extract structured data from CSV row.

        Args:
            row: CSV row as dictionary
            idx: Row index

        Returns:
            Structured person data

        Expected CSV columns:
        - 序号: ID number
        - 中文名: Chinese name
        - 英文名: English name
        - 头衔: Title/current role
        - 所属组织: Organization
        - 核心影响力: Biography/influence description
        """
        # Map CSV columns to our schema
        person = {
            'id': idx,
            'ChineseName': str(row.get('中文名', '')).strip(),
            'name': str(row.get('英文名', '')).strip(),
            'currentRole': str(row.get('头衔', '')).strip(),
            'organization_text': str(row.get('所属组织', '')).strip(),
            'bio_chinese': str(row.get('核心影响力', '')).strip(),
        }

        # Validate required fields
        if not person['name']:
            logger.warning(f"Row {idx}: Missing English name")

        if not person['currentRole']:
            logger.warning(f"Row {idx}: Missing title/role")

        return person


def test_csv_reader():
    """Test function to verify CSV reading."""
    reader = CSVReader()
    people = reader.read_people_data()

    print(f"Loaded {len(people)} people")
    if people:
        print("\nFirst person:")
        for key, value in people[0].items():
            print(f"  {key}: {value[:100] if isinstance(value, str) and len(value) > 100 else value}")


if __name__ == "__main__":
    test_csv_reader()
