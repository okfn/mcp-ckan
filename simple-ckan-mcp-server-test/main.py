# /// script
# dependencies = [
#   "fastmcp==3.0.0b1",
#   "requests",
# ]
# ///

# This Script is based on:
# https://github.com/aviveldan/datagov-mcp/blob/main/server.py

from fastmcp import FastMCP, Context
import requests

mcp = FastMCP("Datos Abiertos BCIE")

BASE_URL = "https://datosabiertos.bcie.org/api/3"


@mcp.tool()
async def package_search(ctx: Context, q: str = "", fq: str = "",
                         sort: str = "", rows: int = 20, start: int = 0,
                         include_private: bool = False):

    """Find packages (datasets) matching query terms."""
    await ctx.info("Searching for packages...")
    params = {
        "q": q,
        "fq": fq,
        "rows": rows,
        "start": start,
        "include_private": include_private
    }
    response = requests.get(f"{BASE_URL}/action/package_search", params=params)
    response.raise_for_status()
    return response.json()


@mcp.tool()
async def datastore_search(ctx: Context, resource_id: str, q: str = "", limit: int = 100):
    """Search a datastore resource."""
    await ctx.info(f"Searching datastore for resource: {resource_id}")
    params = {
        "resource_id": resource_id,
        "q": q,
        "limit": limit,
    }
    response = requests.get(f"{BASE_URL}/action/datastore_search", params=params)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def fetch_data(dataset_name: str, limit: int = 100, offset: int = 0):
    """Fetch data from public API based on a dataset name query"""
    def find_resource_id(dataset_name):
        dataset_url = f"{BASE_URL}/action/package_show?id={dataset_name}"
        response = requests.get(dataset_url)
        if response.status_code == 200:
            dataset_data = response.json()
            resources = dataset_data['result']['resources']
            if resources:
                return resources[0]['id']
        return None

    resource_id = find_resource_id(dataset_name)
    if not resource_id:
        return {"error": f"No dataset found matching '{dataset_name}'"}

    base_url = f"{BASE_URL}/action/datastore_search"
    params = {
        "resource_id": resource_id,
        "limit": limit,
        "offset": offset
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    api_data = response.json()

    if api_data.get("success"):
        return api_data["result"]["records"]
    else:
        raise Exception(api_data.get("error", "Unknown error occurred"))


if __name__ == "__main__":
    mcp.run()
