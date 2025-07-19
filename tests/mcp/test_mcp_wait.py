#!/usr/bin/env python3
"""Test MCP with proper waiting for discovery."""
import asyncio
import json
import websockets

async def test_mcp_with_wait():
    uri = "ws://localhost:8765/v1/realtime"
    
    print("MCP Test with Discovery Wait")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri, subprotocols=["realtime", "model.continuerun.com"]) as websocket:
            print("✓ Connected to Unmute WebSocket")
            
            # Setup session
            await websocket.send(json.dumps({
                "type": "session.update", 
                "session": {
                    "voice": "alloy",
                    "allow_recording": False
                }
            }))
            
            # Wait for session update
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("type") == "session.updated":
                print("✓ Session configured")
            
            # Wait longer for MCP discovery to complete (uvx needs time on first run)
            print("\n⏳ Waiting 65 seconds for MCP discovery to complete...")
            await asyncio.sleep(65)
            
            # Now request available tools
            print("\n📋 Requesting available tools...")
            await websocket.send(json.dumps({
                "type": "mcp.tools.available"
            }))
            
            # Wait for response
            timeout = 10
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "mcp.tools.available.response":
                        tools = data.get("tools", [])
                        print(f"\n✅ Found {len(tools)} tools:")
                        for tool in tools:
                            print(f"\n  Tool: {tool['name']}")
                            print(f"  Description: {tool['description']}")
                            if 'input_schema' in tool:
                                print(f"  Parameters:")
                                schema = tool['input_schema']
                                if 'properties' in schema:
                                    for param, info in schema['properties'].items():
                                        req = " (required)" if param in schema.get('required', []) else " (optional)"
                                        print(f"    - {param}: {info.get('description', 'No description')}{req}")
                        
                        if tools:
                            print("\n✅ MCP dynamic discovery is working!")
                        else:
                            print("\n❌ No tools discovered - check logs")
                        break
                        
                except asyncio.TimeoutError:
                    continue
                    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_with_wait())