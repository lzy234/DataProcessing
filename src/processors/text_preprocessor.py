"""Text preprocessing for Wikipedia content."""
import re
from typing import Dict, List
from src.utils.logger import logger


class TextPreprocessor:
    """
    Preprocess Wikipedia text for AI consumption.

    Tasks:
    1. Clean up formatting artifacts
    2. Remove irrelevant sections
    3. Normalize whitespace
    4. Extract structured information
    """

    def __init__(self):
        """Initialize text preprocessor."""
        # Sections to skip (not biographical)
        self.skip_sections = {
            'see also', 'references', 'external links', 'notes',
            'bibliography', 'further reading', 'gallery', 'filmography',
            'discography', 'awards and nominations', 'electoral history'
        }

    def preprocess(self, wiki_data: Dict) -> Dict:
        """
        Preprocess Wikipedia data.

        Args:
            wiki_data: Raw Wikipedia data with 'extract' field

        Returns:
            Preprocessed Wikipedia data with cleaned and structured text
        """
        if not wiki_data or 'extract' not in wiki_data:
            return wiki_data

        extract = wiki_data['extract']

        # Clean the text
        cleaned_text = self._clean_text(extract)

        # Split into sections
        sections = self._parse_sections(cleaned_text)

        # Filter out irrelevant sections
        filtered_sections = self._filter_sections(sections)

        # Reconstruct text
        processed_text = self._reconstruct_text(filtered_sections)

        # Update wiki_data
        processed_wiki_data = wiki_data.copy()
        processed_wiki_data['extract'] = processed_text
        processed_wiki_data['sections'] = filtered_sections
        processed_wiki_data['section_count'] = len(filtered_sections)

        logger.debug(f"Preprocessed Wikipedia text: {len(extract)} -> {len(processed_text)} chars, "
                    f"{len(filtered_sections)} sections")

        return processed_wiki_data

    def _clean_text(self, text: str) -> str:
        """
        Clean up text formatting.

        Args:
            text: Raw Wikipedia text

        Returns:
            Cleaned text
        """
        if not text:
            return text

        # Remove citation markers like [1], [citation needed]
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\[citation needed\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[clarification needed\]', '', text, flags=re.IGNORECASE)

        # Remove pronunciation guides like /ˈbɑːrək huːˈseɪn oʊˈbɑːmə/
        text = re.sub(r'/[^/]+/', '', text)

        # Normalize whitespace (preserve single newlines for section parsing)
        # First normalize multiple newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Remove multiple spaces within lines (but preserve newlines)
        lines = text.split('\n')
        lines = [re.sub(r' +', ' ', line.strip()) for line in lines]
        text = '\n'.join(lines)

        return text.strip()

    def _parse_sections(self, text: str) -> List[Dict]:
        """
        Parse text into sections.

        Args:
            text: Cleaned text

        Returns:
            List of section dictionaries
        """
        sections = []

        # Split by section headers (== Header ==)
        # Pattern matches == Header == with optional leading newline
        section_pattern = r'==\s*([^=]+?)\s*=='
        matches = list(re.finditer(section_pattern, text))

        if not matches:
            # No sections, treat as single section
            return [{
                'name': 'Introduction',
                'text': text.strip(),
                'is_intro': True
            }]

        # Extract intro
        first_match = matches[0]
        intro_text = text[:first_match.start()].strip()
        if intro_text:
            sections.append({
                'name': 'Introduction',
                'text': intro_text,
                'is_intro': True
            })

        # Extract other sections
        for i, match in enumerate(matches):
            section_name = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()

            if section_text:
                sections.append({
                    'name': section_name,
                    'text': section_text,
                    'is_intro': False
                })

        return sections

    def _filter_sections(self, sections: List[Dict]) -> List[Dict]:
        """
        Filter out irrelevant sections.

        Args:
            sections: All sections

        Returns:
            Filtered sections (biographical only)
        """
        filtered = []

        for section in sections:
            section_name_lower = section['name'].lower()

            # Always keep intro
            if section['is_intro']:
                filtered.append(section)
                continue

            # Skip non-biographical sections
            if section_name_lower in self.skip_sections:
                logger.debug(f"Skipping section: {section['name']}")
                continue

            # Skip sections that are just lists of works/awards
            if self._is_list_section(section['text']):
                logger.debug(f"Skipping list section: {section['name']}")
                continue

            filtered.append(section)

        return filtered

    def _is_list_section(self, text: str) -> bool:
        """
        Check if a section is primarily a list (awards, filmography, etc.).

        Args:
            text: Section text

        Returns:
            True if this is a list section
        """
        lines = text.split('\n')

        # Count lines that look like list items
        list_lines = 0
        for line in lines:
            line = line.strip()
            # List indicators: starts with -, *, number, or is very short
            if (line.startswith('-') or line.startswith('*') or
                re.match(r'^\d+\.?\s', line) or
                (len(line) < 50 and ':' in line)):
                list_lines += 1

        # If more than 50% are list lines, consider it a list section
        return len(lines) > 3 and list_lines / len(lines) > 0.5

    def _reconstruct_text(self, sections: List[Dict]) -> str:
        """
        Reconstruct text from filtered sections.

        Args:
            sections: Filtered sections

        Returns:
            Reconstructed text with section headers
        """
        parts = []

        for section in sections:
            if section['is_intro']:
                parts.append(section['text'])
            else:
                parts.append(f"\n\n== {section['name']} ==\n\n{section['text']}")

        return '\n'.join(parts).strip()

    def extract_key_info(self, wiki_data: Dict) -> Dict:
        """
        Extract key biographical information from preprocessed text.

        Args:
            wiki_data: Preprocessed Wikipedia data

        Returns:
            Dictionary with extracted key info
        """
        text = wiki_data.get('extract', '')

        key_info = {
            'dates': self._extract_dates(text),
            'education_mentions': self._extract_education_mentions(text),
            'career_mentions': self._extract_career_mentions(text),
            'locations': self._extract_locations(text)
        }

        return key_info

    def _extract_dates(self, text: str) -> List[str]:
        """Extract year mentions."""
        dates = re.findall(r'\b(1\d{3}|20\d{2})\b', text)
        return list(set(dates))[:10]  # Top 10 unique dates

    def _extract_education_mentions(self, text: str) -> List[str]:
        """Extract education-related sentences."""
        sentences = re.split(r'[.!?]+', text)
        edu_keywords = ['university', 'college', 'school', 'graduated', 'degree',
                        'studied', 'attended', 'education']

        edu_mentions = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in edu_keywords):
                edu_mentions.append(sentence.strip())

        return edu_mentions[:5]  # Top 5 mentions

    def _extract_career_mentions(self, text: str) -> List[str]:
        """Extract career-related sentences."""
        sentences = re.split(r'[.!?]+', text)
        career_keywords = ['elected', 'appointed', 'served', 'position', 'career',
                          'work', 'job', 'founded', 'became', 'joined']

        career_mentions = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in career_keywords):
                career_mentions.append(sentence.strip())

        return career_mentions[:5]  # Top 5 mentions

    def _extract_locations(self, text: str) -> List[str]:
        """Extract location mentions (simple pattern matching)."""
        # This is a simple implementation
        # For production, consider using NER (Named Entity Recognition)
        location_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        locations = re.findall(location_pattern, text)
        return list(set(locations))[:10]  # Top 10 unique locations


def test_preprocessor():
    """Test the preprocessor."""
    sample_data = {
        'name': 'John Smith',
        'extract': '''John Smith [1] (born January 15, 1970) is an American politician.

== Early life ==
Smith was born in Boston, Massachusetts. He attended Harvard University [2] where he graduated in 1992.

== Career ==
He was elected to the Senate in 2000.

== See also ==
- List of politicians
- Boston politics

== References ==
[1] Citation here
[2] Another citation'''
    }

    preprocessor = TextPreprocessor()
    processed = preprocessor.preprocess(sample_data)

    print("=== Preprocessed Text ===")
    print(processed['extract'])
    print(f"\n=== Sections ({processed['section_count']}) ===")
    for section in processed['sections']:
        print(f"- {section['name']} (intro={section['is_intro']})")

    print("\n=== Key Info ===")
    key_info = preprocessor.extract_key_info(processed)
    print(f"Dates: {key_info['dates']}")
    print(f"Education: {key_info['education_mentions']}")
    print(f"Career: {key_info['career_mentions']}")


if __name__ == "__main__":
    test_preprocessor()
