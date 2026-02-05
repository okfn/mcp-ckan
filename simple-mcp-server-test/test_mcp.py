#!/usr/bin/env python3
"""
Simple Python test script for MCP server tools.
No external dependencies, no accounts, just pure Python testing.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.bcie_loans import _validate_year, _prepare_response
import pandas as pd


def prestamos_por_pais(country=None, year_from=None, year_to=None):
    """Direct call to the tool logic for testing"""
    url = "https://datosabiertos.bcie.org/dataset/prestamos/resource/ce88a753-57f5-4266-a57e-394600c8435d"
    csv = "https://datosabiertos.bcie.org/dataset/45876cb4-d8b8-4635-b999-0df1c19b831a/resource/ce88a753-57f5-4266-a57e-394600c8435d/download/aprobaciones-prestamos.csv"

    errors = []
    df = pd.read_csv(csv)

    valid_countries = df['PAIS'].unique()
    if country and country not in valid_countries:
        errors.append(f"Country '{country}' not found. Valid countries are: {', '.join(valid_countries)}")

    existent_year_range = (df['ANIO_APROBACION'].min(), df['ANIO_APROBACION'].max())

    valid, error = _validate_year(year_from, *existent_year_range)
    if not valid:
        errors.append(f"Invalid year_from: {error}")
    elif year_from is not None:
        year_from = int(year_from)

    valid, error = _validate_year(year_to, *existent_year_range)
    if not valid:
        errors.append(f"Invalid year_to: {error}")
    elif year_to is not None:
        year_to = int(year_to)

    if errors:
        return _prepare_response({"errors": errors})

    if country:
        df_country = df[df['PAIS'] == country]
    else:
        df_country = df

    if year_from is not None:
        df_country = df_country[df_country['ANIO_APROBACION'] >= year_from]
    else:
        year_from = existent_year_range[0]
    if year_to is not None:
        df_country = df_country[df_country['ANIO_APROBACION'] <= year_to]
    else:
        year_to = existent_year_range[1]

    total_amount = df_country['MONTO_BRUTO_USD'].sum()

    return _prepare_response({
        "total_amount": total_amount,
        "country": country,
        "year_from": year_from,
        "year_to": year_to,
        "url": url,
        "csv": csv
    })


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
