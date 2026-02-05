#!/usr/bin/env python3
"""
Simple Python test script for MCP server tools.
No external dependencies, no accounts, just pure Python testing.
"""

import sys
sys.path.insert(0, 'src')

from server import prestamos_por_pais


def test_tool(description, **kwargs):
    """Test a tool and print results"""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"{'='*70}")
    print(f"Parameters: {kwargs}")
    print(f"\nResult:")
    print("-" * 70)
    result = prestamos_por_pais(**kwargs)
    print(result)
    print("-" * 70)


if __name__ == "__main__":
    print("Testing MCP Server Tools - BCIE Loans")
    print("=" * 70)

    # Test 1: All countries, all years
    test_tool("All loans for all countries and years")

    # Test 2: Specific country
    test_tool("All loans for Honduras", country="Honduras")

    # Test 3: Country with year range
    test_tool(
        "Costa Rica loans from 2020 to 2023",
        country="Costa Rica",
        year_from=2020,
        year_to=2023
    )

    # Test 4: Year range only (all countries)
    test_tool("All countries from 2015 onwards", year_from=2015)

    # Test 5: Invalid country (should show error)
    test_tool("Invalid country test", country="InvalidCountry")

    # Test 6: Invalid year (should show error)
    test_tool("Invalid year test", country="Honduras", year_from=1900)

    print("\n" + "=" * 70)
    print("Testing complete!")
    print("=" * 70)
