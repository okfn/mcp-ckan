#!/usr/bin/env python3
"""Test direct HTTP connection to MCP server"""

import requests


# Test local server first
def test_local():
    print("Testing LOCAL server (127.0.0.1:8063)...")
    try:
        response = requests.post(
            "http://127.0.0.1:8063/",
            headers={"Content-Type": "application/json"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            },
            timeout=5
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


def test_remote():
    print("\nTesting REMOTE server (mcp.whoare.io)...")
    try:
        response = requests.post(
            "https://mcp.whoare.io/",
            headers={"Content-Type": "application/json"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            },
            timeout=5
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_local()
    test_remote()
