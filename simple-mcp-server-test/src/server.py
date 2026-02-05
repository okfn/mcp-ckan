import os
import pandas as pd
from mcp.server.fastmcp import FastMCP


# Create an MCP server with configurable settings
def create_mcp_server():
    """Create MCP server with settings from environment variables"""
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8063"))
    return FastMCP("Demo", host=host, port=port, streamable_http_path="/")

mcp = create_mcp_server()


def _validate_year(year, min_year, max_year):
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
    """ We need to send a string response back to MCP clients
        Here we prepare the response accordingly
    """
    if 'errors' in data:
        return "There were errors. We cant respond. Please check:\n" + "\n".join(data['errors'])

    pais = "para " + data['country'] if data['country'] else "para todos los países"
    response = (
        f"La cantidad total de préstamos aprobados por el BCIE {pais} "
        f"fue de ${data['total_amount']:,.2f} "
        f"entre los años {data['year_from']} y {data['year_to']}."
    )
    response += f"\nFuente de datos: {data['url']}"
    response += f"\nCSV de datos: {data['csv']}"
    return response


@mcp.tool()
def prestamos_por_pais(country=None, year_from=None, year_to=None):
    """Get total approved loans from BCIE (Central American Bank for Economic Integration) by country and year range.

    This tool fetches loan data from the BCIE open data portal and calculates the total
    amount of approved loans based on the specified filters.

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
            - Total loan amount in USD (formatted with thousands separators)
            - Country filter applied (or "all countries" if none specified)
            - Year range used for the calculation
            - Source URL and CSV data link

            If there are validation errors (invalid country name, years out of range, etc.),
            returns an error message with details about what went wrong.

    Examples:
        - prestamos_por_pais(country="Honduras") - All loans for Honduras
        - prestamos_por_pais(country="Costa Rica", year_from=2020, year_to=2023) - Costa Rica loans 2020-2023
        - prestamos_por_pais(year_from=2015) - All countries from 2015 onwards
    """
    url = "https://datosabiertos.bcie.org/dataset/prestamos/resource/ce88a753-57f5-4266-a57e-394600c8435d"
    csv = "https://datosabiertos.bcie.org/dataset/45876cb4-d8b8-4635-b999-0df1c19b831a/resource/ce88a753-57f5-4266-a57e-394600c8435d/download/aprobaciones-prestamos.csv"
    # column_names "PAIS", "ANIO_APROBACION", "SECTOR_INSTITUCIONAL", "MONTO_BRUTO_USD", "CANTIDAD_APROBACIONES"

    # Validate all before responding with errors
    errors = []
    # Load the CSV data into a DataFrame
    df = pd.read_csv(csv)

    # valid countries
    valid_countries = df['PAIS'].unique()
    if country and country not in valid_countries:
        errors.append(f"Country '{country}' not found. Valid countries are: {', '.join(valid_countries)}")

    existent_year_range = (df['ANIO_APROBACION'].min(), df['ANIO_APROBACION'].max())

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
        df_country = df_country[df_country['ANIO_APROBACION'] >= year_from]
    else:
        # use this to prepare the future response
        year_from = existent_year_range[0]
    if year_to is not None:
        df_country = df_country[df_country['ANIO_APROBACION'] <= year_to]
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


# Run with configured transport
if __name__ == "__main__":

    required = ["MCP_TRANSPORT", "MCP_HOST", "MCP_PORT"]
    for var in required:
        if os.getenv(var) is None:
            print(f"Error: Environment variable {var} is not set.")
            exit(1)

    transport = os.getenv("MCP_TRANSPORT")

    if transport == "http":
        # HTTP mode for infrastructure deployment
        print(f"Starting MCP server in HTTP mode on {os.getenv('MCP_HOST')}:{os.getenv('MCP_PORT')}")
        mcp.run(transport="streamable-http")
    else:
        # stdio mode (default) for local development
        mcp.run(transport="stdio")
