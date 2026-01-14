"""Test script for organization extraction and hierarchy analysis."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.processors.ai_enhancer import ClaudeAIEnhancer
from src.processors.organization_hierarchy import OrganizationHierarchyAnalyzer
from src.utils.logger import logger


def test_organization_extraction():
    """Test extracting organizations from Wikipedia data."""
    print("\n" + "="*80)
    print("TEST 1: Organization Extraction from Wikipedia")
    print("="*80)

    # Sample test data
    test_people = [
        {
            'name': 'Marco Rubio',
            'currentRole': 'Secretary of State',
            'ChineseName': '马尔科·卢比奥'
        },
        {
            'name': 'Pete Hegseth',
            'currentRole': 'Secretary of Defense',
            'ChineseName': '皮特·海格塞斯'
        },
        {
            'name': 'Donald J. Trump',
            'currentRole': 'President',
            'ChineseName': '唐纳德·特朗普'
        }
    ]

    # Sample Wikipedia data
    wikipedia_data = {
        'Marco Rubio': {
            'extract': 'Marco Rubio is an American politician serving as the 72nd United States Secretary of State. He previously served as a U.S. Senator from Florida.',
            'url': 'https://en.wikipedia.org/wiki/Marco_Rubio',
            'birth_date': '1971-05-28'
        },
        'Pete Hegseth': {
            'extract': 'Pete Hegseth is an American television host and author who serves as United States Secretary of Defense. He was a Fox News host and Army National Guard officer.',
            'url': 'https://en.wikipedia.org/wiki/Pete_Hegseth',
            'birth_date': '1980-06-06'
        },
        'Donald J. Trump': {
            'extract': 'Donald John Trump is the 47th and current president of the United States. He previously served as the 45th president from 2017 to 2021. Trump was based in the White House during his presidency.',
            'url': 'https://en.wikipedia.org/wiki/Donald_Trump',
            'birth_date': '1946-06-14'
        }
    }

    try:
        enhancer = ClaudeAIEnhancer()
        results = enhancer.enhance_batch(test_people, wikipedia_data)

        print("\nResults:")
        for result in results:
            name = result.get('name', '')
            org = result.get('organization', '')
            print(f"\n{name}:")
            print(f"  Organization: {org if org else '(not found)'}")
            print(f"  Sources: {len(result.get('sources', []))} sources")

        return results

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return None


def test_hierarchy_analysis(organizations, wikipedia_data):
    """Test organization hierarchy analysis."""
    print("\n" + "="*80)
    print("TEST 2: Organization Hierarchy Analysis")
    print("="*80)

    # Build organization dict from extracted orgs
    org_dict = {}
    for org_name in organizations:
        if org_name:
            org_dict[org_name] = {
                'name': org_name,
                'parentOrganization': None
            }

    if not org_dict:
        print("No organizations found to analyze")
        return

    print(f"\nAnalyzing hierarchies for {len(org_dict)} organizations:")
    for org_name in org_dict.keys():
        print(f"  - {org_name}")

    try:
        analyzer = OrganizationHierarchyAnalyzer()
        hierarchies = analyzer.analyze_batch_hierarchies(org_dict, wikipedia_data)

        print("\nHierarchy Results:")
        for org_name, parent in hierarchies.items():
            if parent:
                print(f"  {org_name} → {parent}")
            else:
                print(f"  {org_name} → (no parent)")

        return hierarchies

    except Exception as e:
        logger.error(f"Hierarchy analysis failed: {e}", exc_info=True)
        return None


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("Organization Extraction and Hierarchy Analysis Tests")
    print("="*80)

    # Test 1: Extract organizations
    results = test_organization_extraction()

    if results:
        # Collect unique organizations
        organizations = set()
        wikipedia_data = {}

        for result in results:
            org = result.get('organization', '').strip()
            if org:
                organizations.add(org)

        # Build wikipedia data from results
        wikipedia_data = {
            'Marco Rubio': {
                'extract': 'Marco Rubio serves as United States Secretary of State.',
                'url': 'https://en.wikipedia.org/wiki/Marco_Rubio'
            },
            'Pete Hegseth': {
                'extract': 'Pete Hegseth serves as United States Secretary of Defense.',
                'url': 'https://en.wikipedia.org/wiki/Pete_Hegseth'
            },
            'Donald J. Trump': {
                'extract': 'Donald Trump serves as President of the United States and works from the White House.',
                'url': 'https://en.wikipedia.org/wiki/Donald_Trump'
            }
        }

        # Test 2: Analyze hierarchies
        if organizations:
            hierarchies = test_hierarchy_analysis(organizations, wikipedia_data)

        print("\n" + "="*80)
        print("TESTS COMPLETED")
        print("="*80)


if __name__ == "__main__":
    main()
