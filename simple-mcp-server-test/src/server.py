import os
import pandas as pd
from mcp.server.mcpserver import MCPServer


# Create an MCP server
mcp = MCPServer("Demo")


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


@mcp.tool()
def prestamos_por_pais(country, year_from=None, year_to=None):
    """ Fetch loan data for a specific country and optional year range
    Args:Country is not a CODE, is just the country name so we need to parse it accordingly
    """
    url = "https://datosabiertos.bcie.org/dataset/prestamos/resource/ce88a753-57f5-4266-a57e-394600c8435d"
    csv = "https://datosabiertos.bcie.org/dataset/45876cb4-d8b8-4635-b999-0df1c19b831a/resource/ce88a753-57f5-4266-a57e-394600c8435d/download/aprobaciones-prestamos.csv"
    column_names = [
        "PAIS", "ANIO_APROBACION", "SECTOR_INSTITUCIONAL", "MONTO_BRUTO_USD", "CANTIDAD_APROBACIONES"
    ]

    # Validate all before responding with errors
    errors = []
    # Load the CSV data into a DataFrame
    df = pd.read_csv(csv)

    # valid countries
    valid_countries = df['PAIS'].unique()
    if country not in valid_countries:
        errors.append(f"Country '{country}' not found. Valid countries are: {', '.join(valid_countries)}")

    existent_year_range = (df['ANIO_APROBACION'].min(), df['ANIO_APROBACION'].max())

    # Validate year_from and year_to
    valid, error = _validate_year(year_from, *existent_year_range)
    if not valid:
        errors.append(f"Invalid year_from: {error}")
    valid, error = _validate_year(year_to, *existent_year_range)
    if not valid:
        errors.append(f"Invalid year_to: {error}")
    if errors:
        return {"errors": errors}

    # Filter by country
    df_country = df[df['PAIS'] == country]

    # Filter by year range if provided
    if year_from is not None:
        df_country = df_country[df_country['ANIO'] >= year_from]
    if year_to is not None:
        df_country = df_country[df_country['ANIO'] <= year_to]

    # Sum all amounts from the specific country in the filtered DataFrame
    total_amount = df_country['MONTO_BRUTO_USD'].sum()

    return {"total_amount": total_amount}


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
        host = os.getenv("MCP_HOST")
        port = int(os.getenv("MCP_PORT"))
        mcp.run(transport="streamable-http", host=host, port=port, json_response=True)
    else:
        # stdio mode (default) for local development
        mcp.run(transport="stdio")
