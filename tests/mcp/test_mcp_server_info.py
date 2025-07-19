#!/usr/bin/env python3
"""Test what information MCP servers provide about their tools."""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters, stdio_client

async def test_mcp_server_info():
    """Connect to MCP time server and see what it provides."""
    
    # Create server parameters for the time server
    server_params = StdioServerParameters(
        command="docker",
        args=["run", "-i", "--rm", "-e", "TZ=Europe/London", "mcp/time"],
        env={}
    )
    
    try:
        # Connect to the server
        async with stdio_client(server_params) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            
            # Initialize the session
            init_result = await session.initialize()
            print("Server initialization:")
            print(json.dumps(init_result.model_dump(), indent=2))
            
            # List available tools
            tools_response = await session.list_tools()
            print("\nAvailable tools:")
            for tool in tools_response.tools:
                print(f"\nTool: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Input Schema: {json.dumps(tool.inputSchema, indent=2)}")
                
            # Test tool execution
            print("\n\nTesting tool execution:")
            result = await session.call_tool("get_current_time", {})
            print(f"Result (no timezone): {result}")
            
            result = await session.call_tool("get_current_time", {"timezone": "America/New_York"})
            print(f"Result (New York): {result}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_server_info())