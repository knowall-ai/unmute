#!/usr/bin/env python3
"""Inspect what tools and descriptions MCP servers provide."""
import json
import subprocess

def inspect_mcp_server():
    """See what the MCP time server actually provides."""
    
    print("Inspecting MCP Time Server")
    print("=" * 60)
    
    # Initialize the server
    init_request = json.dumps({
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "inspector", "version": "1.0.0"}
        },
        "id": 1
    }) + "\n"
    
    # List tools
    list_tools_request = json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }) + "\n"
    
    # Run the server and get tools
    result = subprocess.run(
        ["python3", "-m", "mcp_server_time"],
        input=init_request + list_tools_request,
        capture_output=True,
        text=True
    )
    
    # Parse responses
    for line in result.stdout.strip().split('\n'):
        if line:
            response = json.loads(line)
            if response.get("id") == 2:  # tools/list response
                print("\nTools provided by MCP server:")
                print(json.dumps(response.get("result", {}), indent=2))
                
                # Extract and display each tool
                tools = response.get("result", {}).get("tools", [])
                print(f"\nFound {len(tools)} tools:\n")
                
                for i, tool in enumerate(tools, 1):
                    print(f"{i}. Tool: {tool.get('name')}")
                    print(f"   Description: {tool.get('description')}")
                    print(f"   Input Schema:")
                    print(json.dumps(tool.get('inputSchema', {}), indent=6))
                    print()

if __name__ == "__main__":
    inspect_mcp_server()