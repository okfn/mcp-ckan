"""
BCIE Disbursements Tool
Fetches disbursement data from BCIE (Central American Bank for Economic Integration)

Data source:
URL: https://datosabiertos.bcie.org/dataset/prestamos/resource/e3a3c0f6-5bb6-496e-9b7f-013666f86259
CSV: https://datosabiertos.bcie.org/dataset/45876cb4-d8b8-4635-b999-0df1c19b831a/resource/e3a3c0f6-5bb6-496e-9b7f-013666f86259/download/desembolsos-prestamos.csv
"""

import pandas as pd


def _validate_year(year, min_year, max_year):
    """Validate year parameter (int or str)"""
    if not year:
        return True, None

    if isinstance(year, int):
        valid = min_year <= year <= max_year
        error = None if valid else f"Year {year} is out of range ({min_year}-{max_year})"
        return valid, error

    if not isinstance(year, str):
        return False, "Year must be an integer or string"

    if not year.isdigit():
        return False, "Year string must contain only digits"
    try:
        year_int = int(year)
    except ValueError:
        return False, "Year conversion error"

    return _validate_year(year_int, min_year, max_year)


def _prepare_response(data):
    """Prepare string response for MCP client"""
    if 'errors' in data:
        return "Hubo errores. No podemos responder. Por favor verifica:\n" + "\n".join(data['errors'])

    pais = "para " + data['country'] if data['country'] else "para todos los países"
    response = (
        f"El total de desembolsos realizados por el BCIE {pais} "
        f"fue de ${data['total_amount']:,.2f} "
        f"entre los años {data['year_from']} y {data['year_to']}."
    )
    response += f"\nFuente de datos: {data['url']}"
    response += f"\nCSV de datos: {data['csv']}"
    return response


def register_tools(mcp):
    """Register BCIE disbursement tools with the MCP server"""

    @mcp.tool()
    def desembolsos_por_pais(country=None, year_from=None, year_to=None):
        """Get total disbursements from BCIE (Central American Bank for Economic Integration) by country and year range.

        This tool fetches disbursement data from the BCIE open data portal and calculates the total
        amount of disbursements based on the specified filters.

        Args:
            country (str, optional): Full country name (NOT a country code).
                Examples: "Honduras", "Costa Rica", "El Salvador", "Guatemala", "Nicaragua", "Panamá".
                If not provided, returns data for all countries combined.
            year_from (int or str, optional): Starting year for the date range (inclusive).
                Must be within the available data range. If not provided, uses the earliest available year.
            year_to (int or str, optional): Ending year for the date range (inclusive).
                Must be within the available data range. If not provided, uses the most recent available year.

        Returns:
            str: A formatted response containing:
                - Total disbursement amount in USD (formatted with thousands separators)
                - Country filter applied (or "all countries" if none specified)
                - Year range used for the calculation
                - Source URL and CSV data link

                If there are validation errors (invalid country name, years out of range, etc.),
                returns an error message with details about what went wrong.

        Examples:
            - desembolsos_por_pais(country="Honduras") - All disbursements for Honduras
            - desembolsos_por_pais(country="Costa Rica", year_from=2020, year_to=2023) - Costa Rica disbursements 2020-2023
            - desembolsos_por_pais(year_from=2015) - All countries from 2015 onwards
        """
        url = "https://datosabiertos.bcie.org/dataset/prestamos/resource/e3a3c0f6-5bb6-496e-9b7f-013666f86259"
        csv = "https://datosabiertos.bcie.org/dataset/45876cb4-d8b8-4635-b999-0df1c19b831a/resource/e3a3c0f6-5bb6-496e-9b7f-013666f86259/download/desembolsos-prestamos.csv"
        # column_names: "PAIS", "ANIO_DESEMBOLSO", "SECTOR_INSTITUCIONAL", "MONTO_BRUTO_USD"

        # Validate all before responding with errors
        errors = []
        # Load the CSV data into a DataFrame
        df = pd.read_csv(csv)

        # valid countries
        valid_countries = df['PAIS'].unique()
        if country and country not in valid_countries:
            errors.append(f"Country '{country}' not found. Valid countries are: {', '.join(valid_countries)}")

        existent_year_range = (df['ANIO_DESEMBOLSO'].min(), df['ANIO_DESEMBOLSO'].max())

        # Validate and convert year_from and year_to
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

        # Filter by country
        if country:
            df_country = df[df['PAIS'] == country]
        else:
            df_country = df

        # Filter by year range if provided
        if year_from is not None:
            df_country = df_country[df_country['ANIO_DESEMBOLSO'] >= year_from]
        else:
            # use this to prepare the future response
            year_from = existent_year_range[0]
        if year_to is not None:
            df_country = df_country[df_country['ANIO_DESEMBOLSO'] <= year_to]
        else:
            # use this to prepare the future response
            year_to = existent_year_range[1]

        # Sum all amounts from the specific country in the filtered DataFrame
        total_amount = df_country['MONTO_BRUTO_USD'].sum()

        return _prepare_response({
            "total_amount": total_amount,
            "country": country,
            "year_from": year_from,
            "year_to": year_to,
            "url": url,
            "csv": csv
        })

    @mcp.tool()
    def paises_con_desembolsos_bcie():
        """Get list of all countries that receive disbursements from BCIE.

        This tool fetches the current list of countries that have received disbursements
        from the BCIE (Central American Bank for Economic Integration).

        Returns:
            str: A formatted list of all countries that receive BCIE disbursements, including
                the total number of countries and the complete list of country names.

        Examples:
            - paises_con_desembolsos_bcie() - Get all countries with BCIE disbursements
        """
        csv = "https://datosabiertos.bcie.org/dataset/45876cb4-d8b8-4635-b999-0df1c19b831a/resource/e3a3c0f6-5bb6-496e-9b7f-013666f86259/download/desembolsos-prestamos.csv"

        # Load the CSV data
        df = pd.read_csv(csv)

        # Get unique countries and sort them
        countries = sorted(df['PAIS'].unique())

        # Format response
        response = f"El BCIE (Banco Centroamericano de Integración Económica) ha desembolsado fondos a {len(countries)} países:\n\n"

        # List countries with bullet points
        for country in countries:
            response += f"  • {country}\n"

        response += "\nFuente de datos: https://datosabiertos.bcie.org/dataset/prestamos/resource/e3a3c0f6-5bb6-496e-9b7f-013666f86259"

        return response
