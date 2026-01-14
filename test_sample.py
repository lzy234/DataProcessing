"""Test script with sample data to verify the pipeline works."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.csv_reader import CSVReader
from src.processors.entity_recognizer import EntityRecognizer
from src.processors.ai_enhancer import ClaudeAIEnhancer
from src.processors.relationship_mapper import RelationshipMapper
from src.validators.schema_validator import SchemaValidator
from src.exporters.csv_writer import CSVWriter
from src.config.settings import Settings


def test_with_sample_data():
    """Test pipeline with minimal sample data."""
    print("=" * 80)
    print("SAMPLE DATA TEST")
    print("=" * 80)

    # Create sample people (mimicking CSV structure)
    sample_people = [
        {
            'id': 1,
            'ChineseName': '南希·佩洛西',
            'name': 'Nancy Pelosi',
            'currentRole': 'Former Speaker of the House (D-CA)',
            'organization_text': '美国众议院 (U.S. House of Representatives)',
            'bio_chinese': '美国民主党政治家，曾任美国众议院议长，是美国历史上首位女性众议院议长。'
        },
        {
            'id': 2,
            'ChineseName': '米奇·麦康奈尔',
            'name': 'Mitch McConnell',
            'currentRole': 'Senate Minority Leader (R-KY)',
            'organization_text': '美国参议院 (U.S. Senate)',
            'bio_chinese': '美国共和党政治家，长期担任参议院领袖。'
        },
        {
            'id': 3,
            'ChineseName': '珍妮特·耶伦',
            'name': 'Janet Yellen',
            'currentRole': 'Secretary of the Treasury',
            'organization_text': '美国财政部 (Department of the Treasury)',
            'bio_chinese': '美国经济学家，曾任美联储主席，现任财政部长。'
        }
    ]

    print(f"\n1. Testing Entity Recognition")
    print("-" * 80)
    recognizer = EntityRecognizer()
    entities = recognizer.process_all_people(sample_people)

    print(f"[OK] Extracted {len(entities['organizations'])} organizations")
    print(f"[OK] Extracted {len(entities['parties'])} parties")
    print(f"[OK] Extracted {len(entities['sectors'])} sectors")

    print(f"\n2. Testing AI Enhancement (with degraded response)")
    print("-" * 80)
    # Simulate AI enhancement without actual API call
    enhanced_people = []
    for person in sample_people:
        enhanced = person.copy()
        enhanced.update({
            'dateOfBirth': None,  # Would come from AI
            'gender': 'female' if '她' in person['bio_chinese'] else 'male',
            'education': '',  # Would come from AI
            'careerHistory': person['currentRole'],
            'bio': person['bio_chinese'],  # Fallback to Chinese
            'sources': [{'sourceName': 'Original CSV', 'sourceUrl': '', 'reliability': 'medium'}]
        })
        enhanced_people.append(enhanced)

    print(f"[OK] Enhanced {len(enhanced_people)} people")

    print(f"\n3. Testing ID Assignment and Relationship Mapping")
    print("-" * 80)
    mapper = RelationshipMapper()
    normalized = mapper.assign_all_ids(
        enhanced_people,
        entities['organizations'],
        entities['parties'],
        entities['sectors']
    )
    normalized = mapper.map_relationships(normalized)

    print(f"[OK] Assigned IDs to {len(normalized['people'])} people")
    print(f"[OK] Assigned IDs to {len(normalized['organizations'])} organizations")
    print(f"[OK] Assigned IDs to {len(normalized['parties'])} parties")
    print(f"[OK] Assigned IDs to {len(normalized['sectors'])} sectors")

    # Show sample IDs
    if normalized['people']:
        print(f"  Sample person ID: {normalized['people'][0]['id']}")
    if normalized['organizations']:
        print(f"  Sample org ID: {normalized['organizations'][0]['id']}")

    print(f"\n4. Testing Schema Validation")
    print("-" * 80)
    validator = SchemaValidator()
    report = validator.validate_all(normalized)

    print(f"[OK] Validation completed")
    print(f"  Errors: {len(report['errors'])}")
    print(f"  Warnings: {len(report['warnings'])}")
    print(f"  Passed: {report['passed']}")

    if report['errors']:
        print("\n  First few errors:")
        for error in report['errors'][:3]:
            print(f"    - {error}")

    if report['statistics']:
        quality_score = report['statistics'].get('overall_quality_score', 0)
        print(f"  Quality score: {quality_score}%")

    print(f"\n5. Testing CSV Export")
    print("-" * 80)

    # Create test output directory
    test_output_dir = Settings.OUTPUT_DIR / "test"
    test_output_dir.mkdir(parents=True, exist_ok=True)

    writer = CSVWriter(test_output_dir)
    output_files = writer.write_all(normalized)

    print(f"[OK] Wrote CSV files to {test_output_dir}")
    for entity_type, filepath in output_files.items():
        file_exists = filepath.exists()
        line_count = 0
        if file_exists:
            with open(filepath, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f) - 1  # Subtract header

        status = "[OK]" if file_exists else "[FAIL]"
        print(f"  {status} {entity_type}: {filepath.name} ({line_count} rows)")

    print("\n" + "=" * 80)
    print("SAMPLE TEST COMPLETED")
    print("=" * 80)

    if report['passed']:
        print("[OK] All validations passed!")
        print(f"\nYou can find the test output in: {test_output_dir}")
        print("\nNext steps:")
        print("1. Set up your .env file with ANTHROPIC_API_KEY")
        print("2. Ensure data/input/人物信息.csv exists")
        print("3. Run: python src/main.py")
        return True
    else:
        print("[WARN] Some validations failed (this is expected with sample data)")
        print("Check the errors above for details")
        return False


if __name__ == "__main__":
    try:
        success = test_with_sample_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
