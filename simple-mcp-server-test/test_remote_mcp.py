#!/usr/bin/env python3
"""
Simple MCP client to test remote server
Tests connection and tool listing
"""

import requests
import json

# Configuration
MCP_SERVER_URL = "https://mcp.whoare.io/"

def test_mcp_server():
    """Test MCP server connection and list tools"""

    print("=" * 60)
    print("Testing MCP Server")
    print("=" * 60)
    print(f"Server: {MCP_SERVER_URL}\n")

    # Test 1: Basic connection
    print("1. Testing basic connection...")
    try:
        response = requests.get(MCP_SERVER_URL, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

    print()

    # Test 2: MCP Protocol - Initialize
    print("2. Testing MCP initialize...")
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        response = requests.post(
            MCP_SERVER_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Server: {result.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
            print(f"   Protocol: {result.get('result', {}).get('protocolVersion', 'Unknown')}")
        else:
            print(f"   Response: {response.text[:200]}")

    except Exception as e:
        print(f"   Error: {e}")

    print()

    # Test 3: List tools
    print("3. Testing tools/list...")
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        response = requests.post(
            MCP_SERVER_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            tools = result.get('result', {}).get('tools', [])
            print(f"   Found {len(tools)} tools:")
            for tool in tools:
                print(f"      • {tool.get('name', 'Unknown')}")
        else:
            print(f"   Response: {response.text[:200]}")

    except Exception as e:
        print(f"   Error: {e}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    test_mcp_server()
