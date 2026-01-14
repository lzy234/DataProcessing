"""Test script for organization deduplication."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.processors.organization_deduplicator import OrganizationDeduplicator
from src.utils.logger import logger


def test_organization_deduplication():
    """Test AI-powered organization deduplication."""
    print("\n" + "="*80)
    print("TEST: AI-Powered Organization Deduplication")
    print("="*80)

    # Sample test data with intentional duplicates
    test_organizations = {
        "U.S. Department of State": {
            "name": "U.S. Department of State",
            "sector": "Government - Executive",
            "parentOrganization": "U.S. Federal Government",
            "description": "Handles foreign policy"
        },
        "Department of State": {
            "name": "Department of State",
            "sector": "Government - Executive",
            "parentOrganization": None,
            "description": "State department"
        },
        "State Department": {
            "name": "State Department",
            "sector": "Government - Executive",
            "parentOrganization": None,
            "description": "Short name"
        },
        "CIA": {
            "name": "CIA",
            "sector": "Government - Intelligence",
            "parentOrganization": "U.S. Federal Government",
            "description": "Intelligence agency"
        },
        "Central Intelligence Agency": {
            "name": "Central Intelligence Agency",
            "sector": "Government - Intelligence",
            "parentOrganization": "U.S. Federal Government",
            "description": "Full name of CIA"
        },
        "White House": {
            "name": "White House",
            "sector": "Government - Executive",
            "parentOrganization": "Executive Office of the President",
            "description": "Presidential residence"
        },
        "U.S. Senate": {
            "name": "U.S. Senate",
            "sector": "Government - Legislative",
            "parentOrganization": None,
            "description": "Upper chamber"
        },
        "United States Senate": {
            "name": "United States Senate",
            "sector": "Government - Legislative",
            "parentOrganization": None,
            "description": "Full name of Senate"
        },
        "US Senate": {
            "name": "US Senate",
            "sector": "Government - Legislative",
            "parentOrganization": None,
            "description": "No dots version"
        },
        "Department of Defense": {
            "name": "Department of Defense",
            "sector": "Government - Executive",
            "parentOrganization": None,
            "description": "Defense department"
        },
        "U.S. Department of Defense": {
            "name": "U.S. Department of Defense",
            "sector": "Government - Executive",
            "parentOrganization": "U.S. Federal Government",
            "description": "Full name with prefix"
        },
        "DoD": {
            "name": "DoD",
            "sector": "Government - Executive",
            "parentOrganization": None,
            "description": "Abbreviation"
        }
    }

    print(f"\nOriginal organizations: {len(test_organizations)}")
    print("\nOrganization list:")
    for i, name in enumerate(sorted(test_organizations.keys()), 1):
        print(f"  {i}. {name}")

    try:
        # Run deduplication
        deduplicator = OrganizationDeduplicator()
        deduplicated_orgs, name_mapping = deduplicator.deduplicate_organizations(test_organizations)

        # Display results
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)

        print(f"\nAfter deduplication: {len(deduplicated_orgs)} organizations")
        print(f"Merged duplicates: {len(test_organizations) - len(deduplicated_orgs)}")

        print("\n" + "-"*80)
        print("Deduplicated Organizations:")
        print("-"*80)
        for i, name in enumerate(sorted(deduplicated_orgs.keys()), 1):
            print(f"  {i}. {name}")

        print("\n" + "-"*80)
        print("Name Mappings (Original -> Canonical):")
        print("-"*80)
        has_mappings = False
        for original, canonical in sorted(name_mapping.items()):
            if original != canonical:
                print(f"  {original}")
                print(f"    -> {canonical}")
                has_mappings = True

        if not has_mappings:
            print("  (No duplicates found - all names are unique)")

        print("\n" + "="*80)
        print("TEST COMPLETED")
        print("="*80)

        return deduplicated_orgs, name_mapping

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n[FAILED] Test failed: {e}")
        return None, None


def test_with_people_data():
    """Test deduplication with simulated people data."""
    print("\n" + "="*80)
    print("TEST: Deduplication Impact on People Data")
    print("="*80)

    # Simulated people with organizations
    test_people = [
        {"name": "Person A", "organization": "Department of State"},
        {"name": "Person B", "organization": "U.S. Department of State"},
        {"name": "Person C", "organization": "State Department"},
        {"name": "Person D", "organization": "CIA"},
        {"name": "Person E", "organization": "Central Intelligence Agency"},
        {"name": "Person F", "organization": "U.S. Senate"},
        {"name": "Person G", "organization": "United States Senate"},
    ]

    # Extract unique organizations
    organizations = {}
    for person in test_people:
        org_name = person['organization']
        if org_name not in organizations:
            organizations[org_name] = {
                'name': org_name,
                'sector': 'Government',
                'parentOrganization': None
            }

    print(f"\nPeople: {len(test_people)}")
    print(f"Unique organizations before dedup: {len(organizations)}")

    try:
        # Deduplicate
        deduplicator = OrganizationDeduplicator()
        deduplicated_orgs, name_mapping = deduplicator.deduplicate_organizations(organizations)

        print(f"Unique organizations after dedup: {len(deduplicated_orgs)}")

        # Apply canonical names to people
        print("\n" + "-"*80)
        print("People's Organizations (Updated):")
        print("-"*80)
        for person in test_people:
            original_org = person['organization']
            canonical_org = name_mapping.get(original_org, original_org)
            updated = " (UPDATED)" if original_org != canonical_org else ""
            print(f"  {person['name']}: {canonical_org}{updated}")
            if updated:
                print(f"    (was: {original_org})")

        print("\n" + "="*80)
        print("TEST COMPLETED")
        print("="*80)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n[FAILED] Test failed: {e}")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("Organization Deduplication Tests")
    print("="*80)

    # Test 1: Basic deduplication
    test_organization_deduplication()

    # Test 2: Impact on people data
    test_with_people_data()

    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)


if __name__ == "__main__":
    main()
