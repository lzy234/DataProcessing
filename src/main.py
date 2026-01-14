"""Main pipeline orchestrating the data processing workflow."""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm

# Add project root to path if running from src directory
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils.logger import logger, setup_logger
from src.config.settings import Settings
from src.extractors.csv_reader import CSVReader
from src.extractors.wikipedia_extractor import WikipediaExtractor
from src.processors.entity_recognizer import EntityRecognizer
from src.processors.ai_enhancer import ClaudeAIEnhancer
from src.processors.relationship_mapper import RelationshipMapper
from src.validators.schema_validator import SchemaValidator
from src.exporters.csv_writer import CSVWriter


class DataProcessingPipeline:
    """
    Main data processing pipeline.

    Phases:
    1. Data Extraction - CSV reading, entity recognition, Wikipedia data
    2. AI Enhancement - Claude API for data completion
    3. Entity Normalization - ID assignment, relationship mapping
    4. Validation & Export - Schema validation, CSV generation
    """

    def __init__(self, input_file: Path = None, output_dir: Path = None):
        """
        Initialize pipeline.

        Args:
            input_file: Input CSV file path
            output_dir: Output directory for CSVs
        """
        self.input_file = input_file or Settings.INPUT_DIR / "人物信息.csv"
        self.output_dir = output_dir or Settings.OUTPUT_DIR

        # Initialize components
        self.csv_reader = CSVReader(self.input_file)
        self.entity_recognizer = EntityRecognizer()
        self.relationship_mapper = RelationshipMapper()
        self.validator = SchemaValidator()
        self.csv_writer = CSVWriter(self.output_dir)

        # Optional components
        self.wikipedia_extractor = None
        if Settings.ENABLE_WIKIPEDIA:
            self.wikipedia_extractor = WikipediaExtractor()

        self.ai_enhancer = None
        if Settings.ANTHROPIC_API_KEY:
            self.ai_enhancer = ClaudeAIEnhancer()

        # Setup detailed logging
        log_file = Settings.INTERMEDIATE_DIR / f"processing_{self._get_timestamp()}.log"
        setup_logger('pipeline', log_file)

        logger.info("=" * 80)
        logger.info("Data Processing Pipeline Initialized")
        logger.info(f"Input: {self.input_file}")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Wikipedia enabled: {Settings.ENABLE_WIKIPEDIA}")
        logger.info(f"AI enhancement enabled: {self.ai_enhancer is not None}")
        logger.info("=" * 80)

    def run(self) -> Dict:
        """
        Run the complete pipeline.

        Returns:
            Dictionary with processing results and statistics
        """
        try:
            logger.info("\n" + "=" * 80)
            logger.info("PHASE 1: DATA EXTRACTION")
            logger.info("=" * 80)
            people, entities = self._phase1_extraction()

            logger.info("\n" + "=" * 80)
            logger.info("PHASE 2: AI ENHANCEMENT")
            logger.info("=" * 80)
            enhanced_people = self._phase2_ai_enhancement(people)

            logger.info("\n" + "=" * 80)
            logger.info("PHASE 3: ENTITY NORMALIZATION")
            logger.info("=" * 80)
            normalized_entities = self._phase3_normalization(enhanced_people, entities)

            logger.info("\n" + "=" * 80)
            logger.info("PHASE 4: VALIDATION & EXPORT")
            logger.info("=" * 80)
            validation_report, output_files = self._phase4_validation_export(normalized_entities)

            # Generate final summary
            summary = self._generate_summary(validation_report, output_files)

            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            logger.info(f"Processed {summary['total_people']} people")
            logger.info(f"Generated {len(output_files)} CSV files")
            logger.info(f"Quality score: {summary['quality_score']}%")

            return summary

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise

    def _phase1_extraction(self) -> tuple[List[Dict], Dict]:
        """
        Phase 1: Extract data from CSV and external sources.

        Returns:
            Tuple of (people_list, extracted_entities)
        """
        logger.info("Step 1.1: Reading CSV file")
        people = self.csv_reader.read_people_data()
        logger.info(f"Loaded {len(people)} people from CSV")

        logger.info("\nStep 1.2: Entity recognition")
        entities = self.entity_recognizer.process_all_people(people)
        logger.info(f"Extracted {len(entities['organizations'])} organizations, "
                   f"{len(entities['parties'])} parties, "
                   f"{len(entities['sectors'])} sectors")

        # Save intermediate entities
        self._save_intermediate('extracted_entities.json', entities)

        logger.info("\nStep 1.3: Wikipedia data extraction")
        wikipedia_data = {}
        if self.wikipedia_extractor and Settings.ENABLE_WIKIPEDIA:
            wikipedia_data = self.wikipedia_extractor.fetch_batch(people)
            logger.info(f"Fetched Wikipedia data for {len(wikipedia_data)} people")
            self._save_intermediate('wikipedia_data.json', wikipedia_data)
        else:
            logger.info("Wikipedia extraction disabled")

        # Merge Wikipedia data into people
        for person in people:
            name = person.get('name', '')
            if name in wikipedia_data:
                wiki = wikipedia_data[name]
                person['wikipedia_extract'] = wiki.get('extract', '')
                person['wikipedia_url'] = wiki.get('url', '')
                person['wikipedia_birth_date'] = wiki.get('birth_date')

        return people, entities

    def _phase2_ai_enhancement(self, people: List[Dict]) -> List[Dict]:
        """
        Phase 2: Use AI to complete missing data.

        Args:
            people: List of people with basic data

        Returns:
            List of enhanced people with completed fields
        """
        if not self.ai_enhancer:
            logger.warning("AI enhancement disabled - using original data")
            return people

        batch_size = Settings.BATCH_SIZE
        total_batches = (len(people) + batch_size - 1) // batch_size

        logger.info(f"Processing {len(people)} people in {total_batches} batches of {batch_size}")

        enhanced_people = []

        # Process in batches with progress bar
        for i in tqdm(range(0, len(people), batch_size), desc="AI Enhancement"):
            batch = people[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            logger.info(f"\nProcessing batch {batch_num}/{total_batches} "
                       f"({len(batch)} people)")

            try:
                # Prepare Wikipedia data for batch
                wiki_data = {}
                for person in batch:
                    name = person.get('name', '')
                    if person.get('wikipedia_extract'):
                        wiki_data[name] = {
                            'extract': person.get('wikipedia_extract'),
                            'url': person.get('wikipedia_url'),
                            'birth_date': person.get('wikipedia_birth_date')
                        }

                # Enhance batch
                enhanced_batch = self.ai_enhancer.enhance_batch(batch, wiki_data)

                # Merge AI data with original data
                for idx, person in enumerate(batch):
                    if idx < len(enhanced_batch):
                        enhanced_data = enhanced_batch[idx]
                        merged = self._merge_person_data(person, enhanced_data)
                        enhanced_people.append(merged)
                    else:
                        enhanced_people.append(person)

            except Exception as e:
                logger.error(f"Error enhancing batch {batch_num}: {e}")
                # Use original data for failed batch
                enhanced_people.extend(batch)

        # Save intermediate enhanced data
        self._save_intermediate('enhanced_people.json', enhanced_people)

        logger.info(f"\nAI enhancement complete: {len(enhanced_people)} people")
        return enhanced_people

    def _merge_person_data(self, original: Dict, enhanced: Dict) -> Dict:
        """
        Merge original and AI-enhanced data.

        Args:
            original: Original person data
            enhanced: AI-enhanced data

        Returns:
            Merged person dictionary
        """
        merged = original.copy()

        # Update with AI-enhanced fields
        ai_fields = [
            'dateOfBirth', 'gender', 'education',
            'careerHistory', 'bio', 'organization', 'sources'
        ]

        for field in ai_fields:
            if field in enhanced and enhanced[field]:
                merged[field] = enhanced[field]

        return merged

    def _phase3_normalization(self, people: List[Dict], entities: Dict) -> Dict:
        """
        Phase 3: Normalize entities and establish relationships.

        Args:
            people: Enhanced people list
            entities: Extracted entities

        Returns:
            Normalized entities with IDs and relationships
        """
        # Step 3.0: Extract organizations from AI-enhanced people data
        logger.info("Step 3.0: Extracting organizations from AI-enhanced data")
        organizations_from_ai = self._extract_organizations_from_people(people)
        logger.info(f"Extracted {len(organizations_from_ai)} unique organizations from AI data")

        # Step 3.0.3: Deduplicate organizations using AI
        logger.info("\nStep 3.0.3: Deduplicating organizations with AI")
        org_name_mapping = {}  # original_name -> canonical_name
        if Settings.ANTHROPIC_API_KEY and len(organizations_from_ai) > 1:
            from src.processors.organization_deduplicator import OrganizationDeduplicator
            deduplicator = OrganizationDeduplicator()
            organizations_from_ai, org_name_mapping = deduplicator.deduplicate_organizations(
                organizations_from_ai
            )
            logger.info(f"After deduplication: {len(organizations_from_ai)} organizations")

            # Update people's organization field with canonical names
            for person in people:
                original_org = person.get('organization', '').strip()
                if original_org and original_org in org_name_mapping:
                    canonical_org = org_name_mapping[original_org]
                    if original_org != canonical_org:
                        logger.debug(f"Updated {person.get('name')}'s org: {original_org} -> {canonical_org}")
                        person['organization'] = canonical_org

        # Step 3.0.5: Analyze organization hierarchies using AI
        logger.info("\nStep 3.0.5: Analyzing organization hierarchies with AI")
        if Settings.ANTHROPIC_API_KEY and organizations_from_ai:
            from src.processors.organization_hierarchy import OrganizationHierarchyAnalyzer
            hierarchy_analyzer = OrganizationHierarchyAnalyzer()

            # Prepare Wikipedia data for context
            wiki_data_for_hierarchy = {}
            for person in people:
                name = person.get('name', '')
                if person.get('wikipedia_extract'):
                    wiki_data_for_hierarchy[name] = {
                        'extract': person.get('wikipedia_extract'),
                        'url': person.get('wikipedia_url')
                    }

            hierarchies = hierarchy_analyzer.analyze_batch_hierarchies(
                organizations_from_ai,
                wiki_data_for_hierarchy
            )

            # Apply hierarchies to organizations
            for org_name, org_data in organizations_from_ai.items():
                if org_name in hierarchies:
                    org_data['parentOrganization'] = hierarchies[org_name]

        logger.info("Step 3.1: Assigning unique IDs")
        normalized = self.relationship_mapper.assign_all_ids(
            people,
            organizations_from_ai,
            entities['parties'],
            entities['sectors']
        )

        logger.info("\nStep 3.2: Mapping relationships")
        normalized = self.relationship_mapper.map_relationships(normalized)

        logger.info("\nStep 3.3: Validating references")
        ref_errors = self.relationship_mapper.validate_references(normalized)
        if ref_errors:
            logger.warning(f"Found {len(ref_errors)} reference errors:")
            for error in ref_errors[:5]:  # Show first 5
                logger.warning(f"  - {error}")
        else:
            logger.info("All references valid")

        # Save intermediate normalized data
        self._save_intermediate('normalized_entities.json', {
            'people_count': len(normalized['people']),
            'organizations_count': len(normalized['organizations']),
            'parties_count': len(normalized['parties']),
            'sectors_count': len(normalized['sectors'])
        })

        return normalized

    def _extract_organizations_from_people(self, people: List[Dict]) -> Dict[str, Dict]:
        """
        Extract unique organizations from AI-enhanced people data.

        Args:
            people: List of people with AI-extracted organization field

        Returns:
            Dictionary of organizations keyed by name
        """
        organizations = {}

        for person in people:
            org_name = person.get('organization', '').strip()
            if org_name and org_name not in organizations:
                # Create organization entry
                # Infer sector based on organization name
                from src.processors.entity_recognizer import EntityRecognizer
                recognizer = EntityRecognizer()
                sector = recognizer.infer_sector(org_name)

                organizations[org_name] = {
                    'name': org_name,
                    'chineseName': None,  # Not available from AI extraction
                    'sector': sector['name'] if sector else None,
                    'parentOrganization': None,  # Will be filled by AI hierarchy analysis
                    'description': f"Political organization: {org_name}"
                }

        return organizations

    def _phase4_validation_export(self, entities: Dict) -> tuple[Dict, Dict]:
        """
        Phase 4: Validate and export to CSV.

        Args:
            entities: Normalized entities

        Returns:
            Tuple of (validation_report, output_files)
        """
        logger.info("Step 4.1: Schema validation")
        validation_report = self.validator.validate_all(entities)

        logger.info(f"\nValidation results:")
        logger.info(f"  Errors: {len(validation_report['errors'])}")
        logger.info(f"  Warnings: {len(validation_report['warnings'])}")
        logger.info(f"  Passed: {validation_report['passed']}")

        if validation_report['errors']:
            logger.error("Validation errors found:")
            for error in validation_report['errors'][:10]:  # Show first 10
                logger.error(f"  - {error}")

        # Save validation report
        self.validator.save_report(validation_report)

        logger.info("\nStep 4.2: Exporting to CSV")
        output_files = self.csv_writer.write_all(entities)

        for entity_type, filepath in output_files.items():
            logger.info(f"  {entity_type}: {filepath}")

        return validation_report, output_files

    def _generate_summary(self, validation_report: Dict, output_files: Dict) -> Dict:
        """
        Generate processing summary.

        Args:
            validation_report: Validation report
            output_files: Output file paths

        Returns:
            Summary dictionary
        """
        stats = validation_report.get('statistics', {})

        summary = {
            'total_people': stats.get('total_people', 0),
            'total_organizations': stats.get('total_organizations', 0),
            'total_parties': stats.get('total_parties', 0),
            'total_sectors': stats.get('total_sectors', 0),
            'quality_score': stats.get('overall_quality_score', 0),
            'field_completeness': stats.get('field_completeness', {}),
            'validation_passed': validation_report['passed'],
            'error_count': len(validation_report['errors']),
            'warning_count': len(validation_report['warnings']),
            'output_files': {k: str(v) for k, v in output_files.items()}
        }

        # Save summary
        summary_file = Settings.INTERMEDIATE_DIR / "processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"\nProcessing summary saved to {summary_file}")

        return summary

    def _save_intermediate(self, filename: str, data: Dict):
        """
        Save intermediate data to JSON file.

        Args:
            filename: Output filename
            data: Data to save
        """
        output_file = Settings.INTERMEDIATE_DIR / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Saved intermediate data to {output_file}")

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Political Figure Data Processing Pipeline"
    )
    parser.add_argument(
        '--input',
        type=Path,
        help=f"Input CSV file (default: {Settings.INPUT_DIR / '人物信息.csv'})"
    )
    parser.add_argument(
        '--output',
        type=Path,
        help=f"Output directory (default: {Settings.OUTPUT_DIR})"
    )
    parser.add_argument(
        '--no-wikipedia',
        action='store_true',
        help="Disable Wikipedia data extraction"
    )

    args = parser.parse_args()

    # Override settings if specified
    if args.no_wikipedia:
        Settings.ENABLE_WIKIPEDIA = False

    # Run pipeline
    pipeline = DataProcessingPipeline(
        input_file=args.input,
        output_dir=args.output
    )

    try:
        summary = pipeline.run()

        print("\n" + "=" * 80)
        print("PROCESSING COMPLETE")
        print("=" * 80)
        print(f"Processed: {summary['total_people']} people")
        print(f"Organizations: {summary['total_organizations']}")
        print(f"Parties: {summary['total_parties']}")
        print(f"Sectors: {summary['total_sectors']}")
        print(f"Quality Score: {summary['quality_score']}%")
        print(f"\nOutput files:")
        for entity_type, filepath in summary['output_files'].items():
            print(f"  - {entity_type}: {filepath}")

        if not summary['validation_passed']:
            print(f"\nWarning: {summary['error_count']} validation errors found")
            print("Check quality_report.json for details")

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\nError: {e}")
        print("Check log files for details")
        return 1


if __name__ == "__main__":
    exit(main())
