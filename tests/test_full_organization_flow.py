"""Test full organization extraction, deduplication, and hierarchy flow."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.processors.ai_enhancer import ClaudeAIEnhancer
from src.processors.organization_deduplicator import OrganizationDeduplicator
from src.processors.organization_hierarchy import OrganizationHierarchyAnalyzer
from src.utils.logger import logger


def test_full_flow():
    """Test the complete flow: extraction -> deduplication -> hierarchy."""
    print("\n" + "="*80)
    print("FULL ORGANIZATION FLOW TEST")
    print("="*80)

    # Sample people with Wikipedia data
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
        },
        {
            'name': 'John Doe',  # Fictional person for testing
            'currentRole': 'State Department Official',
            'ChineseName': '约翰·多伊'
        }
    ]

    # Wikipedia data
    wikipedia_data = {
        'Marco Rubio': {
            'extract': 'Marco Antonio Rubio is an American politician serving as the 72nd United States Secretary of State since 2025. He previously served as a U.S. Senator from Florida from 2011 to 2025. The Department of State is the federal executive department responsible for international relations.',
            'url': 'https://en.wikipedia.org/wiki/Marco_Rubio',
            'birth_date': '1971-05-28'
        },
        'Pete Hegseth': {
            'extract': 'Peter Brian Hegseth is an American television host and author who serves as United States Secretary of Defense. The U.S. Department of Defense is responsible for coordinating and supervising all agencies concerned with national security.',
            'url': 'https://en.wikipedia.org/wiki/Pete_Hegseth',
            'birth_date': '1980-06-06'
        },
        'Donald J. Trump': {
            'extract': 'Donald John Trump is the 47th and current president of the United States. He works from the White House, the official residence and workplace of the president. The White House is located in Washington, D.C.',
            'url': 'https://en.wikipedia.org/wiki/Donald_Trump',
            'birth_date': '1946-06-14'
        },
        'John Doe': {
            'extract': 'John Doe works as an official at the State Department in Washington, D.C. The Department of State handles U.S. foreign policy and international relations.',
            'url': 'https://en.wikipedia.org/wiki/John_Doe',
            'birth_date': '1980-01-01'
        }
    }

    print(f"\nTest data: {len(test_people)} people")
    for person in test_people:
        print(f"  - {person['name']} ({person['currentRole']})")

    # STEP 1: Extract organizations from Wikipedia using AI
    print("\n" + "="*80)
    print("STEP 1: Extract Organizations from Wikipedia")
    print("="*80)

    try:
        enhancer = ClaudeAIEnhancer()
        enhanced_people = enhancer.enhance_batch(test_people, wikipedia_data)

        print("\nExtracted organizations:")
        organizations = {}
        for person in enhanced_people:
            name = person.get('name', '')
            org = person.get('organization', '').strip()
            print(f"  {name}: {org if org else '(none)'}")

            if org and org not in organizations:
                organizations[org] = {
                    'name': org,
                    'sector': 'Government',
                    'parentOrganization': None
                }

        print(f"\nUnique organizations extracted: {len(organizations)}")

        # STEP 2: Deduplicate organizations
        print("\n" + "="*80)
        print("STEP 2: Deduplicate Organizations")
        print("="*80)

        if len(organizations) > 1:
            deduplicator = OrganizationDeduplicator()
            deduplicated_orgs, name_mapping = deduplicator.deduplicate_organizations(organizations)

            print(f"\nBefore deduplication: {len(organizations)} organizations")
            print(f"After deduplication: {len(deduplicated_orgs)} organizations")
            print(f"Merged: {len(organizations) - len(deduplicated_orgs)} duplicates")

            # Show mappings
            has_duplicates = False
            print("\nDuplicate mappings:")
            for original, canonical in sorted(name_mapping.items()):
                if original != canonical:
                    print(f"  {original} -> {canonical}")
                    has_duplicates = True

            if not has_duplicates:
                print("  (No duplicates found)")

            # Update people's organization references
            for person in enhanced_people:
                original_org = person.get('organization', '').strip()
                if original_org and original_org in name_mapping:
                    person['organization'] = name_mapping[original_org]

            organizations = deduplicated_orgs
        else:
            print("\nOnly 1 organization found, skipping deduplication")
            name_mapping = {name: name for name in organizations.keys()}

        # STEP 3: Analyze organization hierarchies
        print("\n" + "="*80)
        print("STEP 3: Analyze Organization Hierarchies")
        print("="*80)

        if organizations:
            hierarchy_analyzer = OrganizationHierarchyAnalyzer()

            # Prepare Wikipedia data for hierarchy analysis
            wiki_data_for_hierarchy = {}
            for person in enhanced_people:
                name = person.get('name', '')
                if name in wikipedia_data:
                    wiki_data_for_hierarchy[name] = wikipedia_data[name]

            hierarchies = hierarchy_analyzer.analyze_batch_hierarchies(
                organizations,
                wiki_data_for_hierarchy
            )

            print("\nOrganization hierarchies:")
            for org_name, parent in hierarchies.items():
                if parent:
                    print(f"  {org_name} -> {parent}")
                else:
                    print(f"  {org_name} -> (no parent)")

            # Apply hierarchies
            for org_name, org_data in organizations.items():
                if org_name in hierarchies:
                    org_data['parentOrganization'] = hierarchies[org_name]

        # FINAL RESULTS
        print("\n" + "="*80)
        print("FINAL RESULTS")
        print("="*80)

        print("\n" + "-"*80)
        print("Organizations:")
        print("-"*80)
        for org_name, org_data in sorted(organizations.items()):
            parent = org_data.get('parentOrganization')
            parent_str = f" -> {parent}" if parent else ""
            print(f"  {org_name}{parent_str}")

        print("\n" + "-"*80)
        print("People -> Organizations:")
        print("-"*80)
        for person in enhanced_people:
            name = person.get('name', '')
            org = person.get('organization', '')
            print(f"  {name}: {org if org else '(none)'}")

        print("\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("="*80)

        return enhanced_people, organizations

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n[FAILED] Test failed: {e}")
        return None, None


if __name__ == "__main__":
    test_full_flow()
