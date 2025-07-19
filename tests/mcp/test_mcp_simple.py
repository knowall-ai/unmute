#!/usr/bin/env python3
"""Simple MCP test to check tool discovery."""
import asyncio
import json
import websockets

async def test_mcp():
    uri = "ws://localhost:8765/v1/realtime"
    
    try:
        async with websockets.connect(uri, subprotocols=["realtime", "model.continuerun.com"]) as websocket:
            print("Connected to Unmute WebSocket")
            
            # Setup session
            await websocket.send(json.dumps({
                "type": "session.update", 
                "session": {
                    "voice": "alloy",
                    "allow_recording": False
                }
            }))
            
            await asyncio.sleep(5)  # Give more time for MCP discovery
            
            # List available tools
            print("\nRequesting available tools...")
            await websocket.send(json.dumps({
                "type": "mcp.tools.available"
            }))
            
            # Wait for responses
            timeout = 5.0
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)
                
                if data.get("type") == "mcp.tools.available.response":
                    tools = data.get("tools", [])
                    print(f"\nFound {len(tools)} tools:")
                    for tool in tools:
                        print(f"\nTool: {tool['name']}")
                        print(f"Description: {tool['description']}")
                        if 'input_schema' in tool:
                            print(f"Input Schema: {json.dumps(tool['input_schema'], indent=2)}")
                    break
                else:
                    print(f"Received: {data.get('type')}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp())