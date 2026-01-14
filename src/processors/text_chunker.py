"""Intelligent text chunking for long Wikipedia articles."""
import re
from typing import List, Dict
from src.utils.logger import logger


class TextChunker:
    """
    Intelligent text chunker that splits long articles into manageable chunks.

    Strategy:
    1. Split by sections (## headings)
    2. Combine small sections together
    3. Split large sections by paragraphs
    4. Ensure each chunk is within token limits
    """

    def __init__(self,
                 max_chunk_size: int = 2000,
                 min_chunk_size: int = 500,
                 overlap: int = 100):
        """
        Initialize text chunker.

        Args:
            max_chunk_size: Maximum characters per chunk
            min_chunk_size: Minimum characters per chunk
            overlap: Number of characters to overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, person_name: str = "") -> List[Dict]:
        """
        Split text into intelligent chunks.

        Args:
            text: Full Wikipedia text
            person_name: Person's name for context

        Returns:
            List of chunk dictionaries with:
            - text: chunk content
            - section: section name (if any)
            - chunk_index: position in sequence
            - is_intro: whether this is the intro section
        """
        if not text or len(text) < self.max_chunk_size:
            return [{
                'text': text,
                'section': 'Full Article',
                'chunk_index': 0,
                'is_intro': True,
                'person_name': person_name
            }]

        # Parse sections
        sections = self._parse_sections(text)

        # Create chunks
        chunks = []
        chunk_index = 0

        for section in sections:
            section_name = section['name']
            section_text = section['text']
            is_intro = section['is_intro']

            # If section is small enough, keep it as one chunk
            if len(section_text) <= self.max_chunk_size:
                chunks.append({
                    'text': section_text,
                    'section': section_name,
                    'chunk_index': chunk_index,
                    'is_intro': is_intro,
                    'person_name': person_name
                })
                chunk_index += 1
            else:
                # Split large section into paragraphs
                para_chunks = self._chunk_by_paragraphs(
                    section_text,
                    section_name,
                    is_intro
                )
                for para_chunk in para_chunks:
                    para_chunk['chunk_index'] = chunk_index
                    para_chunk['person_name'] = person_name
                    chunks.append(para_chunk)
                    chunk_index += 1

        logger.info(f"Split article into {len(chunks)} chunks for {person_name}")
        return chunks

    def _parse_sections(self, text: str) -> List[Dict]:
        """
        Parse Wikipedia text into sections.

        Looks for common section markers like:
        == Section Name ==

        Args:
            text: Full Wikipedia text

        Returns:
            List of section dictionaries
        """
        sections = []

        # Split by section headers (== Header ==)
        section_pattern = r'\n==\s*([^=]+)\s*==\n'
        matches = list(re.finditer(section_pattern, text))

        if not matches:
            # No sections found, treat as single intro
            return [{
                'name': 'Introduction',
                'text': text.strip(),
                'is_intro': True
            }]

        # Extract intro (before first section)
        first_match = matches[0]
        intro_text = text[:first_match.start()].strip()
        if intro_text:
            sections.append({
                'name': 'Introduction',
                'text': intro_text,
                'is_intro': True
            })

        # Extract all other sections
        for i, match in enumerate(matches):
            section_name = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()

            # Skip empty or very short sections
            if len(section_text) > 50:
                sections.append({
                    'name': section_name,
                    'text': section_text,
                    'is_intro': False
                })

        return sections

    def _chunk_by_paragraphs(self, text: str, section_name: str, is_intro: bool) -> List[Dict]:
        """
        Split text by paragraphs while maintaining chunk size limits.

        Args:
            text: Section text
            section_name: Name of the section
            is_intro: Whether this is intro section

        Returns:
            List of chunk dictionaries
        """
        # Split by paragraphs (double newline or single newline)
        paragraphs = re.split(r'\n\n+', text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds max size
            if len(current_chunk) + len(para) + 2 > self.max_chunk_size:
                # Save current chunk if it's substantial
                if len(current_chunk) > self.min_chunk_size:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'section': section_name,
                        'is_intro': is_intro
                    })
                    # Start new chunk with overlap
                    current_chunk = self._get_overlap(current_chunk) + "\n\n" + para
                else:
                    # Current chunk too small, just add paragraph
                    current_chunk += "\n\n" + para if current_chunk else para
            else:
                # Add paragraph to current chunk
                current_chunk += "\n\n" + para if current_chunk else para

        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'section': section_name,
                'is_intro': is_intro
            })

        return chunks

    def _get_overlap(self, text: str) -> str:
        """
        Get overlap text from the end of a chunk.

        Args:
            text: Text to get overlap from

        Returns:
            Last N characters for overlap
        """
        if len(text) <= self.overlap:
            return text

        # Try to break at sentence boundary
        overlap_text = text[-self.overlap:]
        sentence_end = overlap_text.rfind('. ')

        if sentence_end > 0:
            return overlap_text[sentence_end + 2:]

        return overlap_text

    def prioritize_chunks(self, chunks: List[Dict], max_chunks: int = 5) -> List[Dict]:
        """
        Prioritize most relevant chunks for AI processing.

        Strategy:
        1. Always include intro
        2. Prefer sections with biographical info (Early life, Education, Career)
        3. Include sections with dates, education keywords

        Args:
            chunks: All chunks
            max_chunks: Maximum number of chunks to return

        Returns:
            Prioritized list of chunks
        """
        if len(chunks) <= max_chunks:
            return chunks

        # Score each chunk
        scored_chunks = []
        for chunk in chunks:
            score = self._score_chunk(chunk)
            scored_chunks.append((score, chunk))

        # Sort by score (descending)
        scored_chunks.sort(reverse=True, key=lambda x: x[0])

        # Always include intro
        result = []
        for score, chunk in scored_chunks:
            if chunk['is_intro']:
                result.insert(0, chunk)  # Intro first
            else:
                result.append(chunk)

        return result[:max_chunks]

    def _score_chunk(self, chunk: Dict) -> float:
        """
        Score a chunk based on relevance for biographical extraction.

        Args:
            chunk: Chunk dictionary

        Returns:
            Relevance score (higher is better)
        """
        score = 0.0
        text = chunk['text'].lower()
        section = chunk['section'].lower()

        # Intro gets highest priority
        if chunk['is_intro']:
            score += 100

        # Biographical sections
        bio_sections = ['early life', 'education', 'career', 'personal life',
                        'biography', 'background', 'youth']
        for bio_sec in bio_sections:
            if bio_sec in section:
                score += 50
                break

        # Keywords indicating biographical content
        bio_keywords = ['born', 'graduated', 'attended', 'studied', 'degree',
                        'university', 'college', 'school', 'family', 'married',
                        'raised', 'childhood', 'parents']
        for keyword in bio_keywords:
            if keyword in text:
                score += 5

        # Dates indicate biographical content
        date_pattern = r'\b\d{4}\b'
        dates = re.findall(date_pattern, text)
        score += len(dates) * 2

        # Length factor (prefer substantial chunks)
        if len(text) > 500:
            score += 10

        return score


def test_text_chunker():
    """Test the text chunker."""
    sample_text = """
John Smith (born January 15, 1970) is an American politician and businessman.

== Early life ==
Smith was born in Boston, Massachusetts. He attended Harvard University where he graduated with honors in 1992.

== Career ==
Smith began his career in the technology sector. He founded TechCorp in 1995.

In 2000, he entered politics and was elected to the state senate.

== Personal life ==
Smith is married with three children. He lives in Boston.
"""

    chunker = TextChunker(max_chunk_size=200, min_chunk_size=50)
    chunks = chunker.chunk_text(sample_text, "John Smith")

    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"\n--- Chunk {chunk['chunk_index']}: {chunk['section']} (intro={chunk['is_intro']}) ---")
        print(f"Length: {len(chunk['text'])}")
        print(f"Text: {chunk['text'][:100]}...")

    print("\n\n=== Prioritized Chunks ===")
    prioritized = chunker.prioritize_chunks(chunks, max_chunks=3)
    for chunk in prioritized:
        print(f"\nSection: {chunk['section']}")
        print(f"Text: {chunk['text'][:150]}...")


if __name__ == "__main__":
    test_text_chunker()
