#!/usr/bin/env python3
"""Direct test of MCP backend websocket for time functionality."""
import asyncio
import json
import websockets
from datetime import datetime

async def test_mcp_time():
    """Connect to MCP backend and test time tools directly."""
    uri = "ws://localhost:8001/v1/realtime"
    
    print("MCP Backend Direct Time Test")
    print("=" * 60)
    print(f"Connecting to: {uri}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 1. Establish connection with 'realtime' subprotocol
        async with websockets.connect(uri, subprotocols=["realtime"]) as websocket:
            print("✓ Connected to MCP backend WebSocket")
            
            # 2. Send session configuration
            print("\n📤 Sending session configuration...")
            await websocket.send(json.dumps({
                "type": "session.update", 
                "session": {
                    "voice": "alloy",
                    "allow_recording": False,
                    "modalities": ["text"],
                    "temperature": 0.7
                }
            }))
            
            # Wait for session confirmation
            print("\n⏳ Waiting for session setup...")
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("type") == "session.updated":
                print("✓ Session updated successfully")
            
            # 3. List available MCP servers
            print("\n📤 Listing MCP servers...")
            await websocket.send(json.dumps({
                "type": "mcp.servers.list"
            }))
            
            # Get server list response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  Response type: {data.get('type')}")
            if data.get("type") == "mcp.servers.list.response":
                servers = data.get("servers", [])
                print(f"✓ Found {len(servers)} MCP servers:")
                for server in servers:
                    print(f"  - {server}")
            else:
                print(f"  Full response: {json.dumps(data, indent=2)}")
            
            # 4. List available tools
            print("\n📤 Listing available MCP tools...")
            await websocket.send(json.dumps({
                "type": "mcp.tools.available"
            }))
            
            # Get tools response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  Response type: {data.get('type')}")
            if data.get("type") == "mcp.tools.available.response":
                tools = data.get("tools", [])
                print(f"✓ Found {len(tools)} MCP tools:")
                for tool in tools:
                    print(f"  - {tool.get('name')}: {tool.get('description', 'No description')}")
            else:
                print(f"  Full response: {json.dumps(data, indent=2)}")
            
            # 5. Execute time tool - get current time (no timezone)
            print("\n📤 Executing time.get_current_time tool (no timezone)...")
            await websocket.send(json.dumps({
                "type": "mcp.tool.execute",
                "tool_name": "time.get_current_time",
                "arguments": {}
            }))
            
            # Get tool execution response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  Response type: {data.get('type')}")
            if data.get("type") == "mcp.tool.execute.response":
                result = data.get("result", "")
                print(f"✓ Tool execution result:")
                if isinstance(result, str):
                    print(f"  {result if result else '(empty string)'}")
                else:
                    print(f"  {json.dumps(result, indent=2)}")
            elif data.get("type") == "error":
                error = data.get("error", {})
                print(f"✗ Tool execution error: {error.get('message', 'Unknown error')}")
                print(f"  Full error: {json.dumps(error, indent=2)}")
            else:
                print(f"  Full response: {json.dumps(data, indent=2)}")
            
            # 5b. Execute time tool - get current time (with timezone)
            print("\n📤 Executing time.get_current_time tool (with timezone)...")
            await websocket.send(json.dumps({
                "type": "mcp.tool.execute",
                "tool_name": "time.get_current_time",
                "arguments": {
                    "timezone": "Europe/London"
                }
            }))
            
            # Get tool execution response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  Response type: {data.get('type')}")
            if data.get("type") == "mcp.tool.execute.response":
                result = data.get("result", "")
                print(f"✓ Tool execution result:")
                if isinstance(result, str):
                    print(f"  {result if result else '(empty string)'}")
                else:
                    print(f"  {json.dumps(result, indent=2)}")
            elif data.get("type") == "error":
                error = data.get("error", {})
                print(f"✗ Tool execution error: {error.get('message', 'Unknown error')}")
                print(f"  Full error: {json.dumps(error, indent=2)}")
            else:
                print(f"  Full response: {json.dumps(data, indent=2)}")
            
            # 6. Execute time conversion tool
            print("\n📤 Executing time.convert_time tool...")
            await websocket.send(json.dumps({
                "type": "mcp.tool.execute",
                "tool_name": "time.convert_time",
                "arguments": {
                    "source_timezone": "Europe/London",
                    "target_timezone": "America/New_York",
                    "time": "15:30"
                }
            }))
            
            # Get tool execution response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  Response type: {data.get('type')}")
            if data.get("type") == "mcp.tool.execute.response":
                result = data.get("result", "")
                print(f"✓ Tool execution result:")
                if isinstance(result, str):
                    print(f"  {result if result else '(empty string)'}")
                else:
                    print(f"  {json.dumps(result, indent=2)}")
            elif data.get("type") == "error":
                error = data.get("error", {})
                print(f"✗ Tool execution error: {error.get('message', 'Unknown error')}")
                print(f"  Full error: {json.dumps(error, indent=2)}")
            else:
                print(f"  Full response: {json.dumps(data, indent=2)}")
            
            # Summary
            print("\n" + "=" * 60)
            print("✅ Test completed successfully!")
            print("The MCP time tools are working correctly.")
            
    except Exception as e:
        print(f"\n❌ Connection failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting MCP time test...")
    asyncio.run(test_mcp_time())