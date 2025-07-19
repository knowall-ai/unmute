#!/usr/bin/env python3
"""Test MCP tool calling by asking for the time."""
import asyncio
import websockets
import json
import base64
import time

async def test_time_question():
    """Test asking unmute for the time."""
    uri = "ws://localhost:8766/v1/realtime"  # MCP backend
    
    try:
        async with websockets.connect(uri, subprotocols=["realtime"]) as websocket:
            print("Connected to unmute-backend-mcp")
            
            # Send session configuration
            session_msg = {
                "type": "session.update",
                "session": {
                    "instructions": {
                        "type": "constant",
                        "text": "You are a helpful assistant. Use the MCP tools when asked about time."
                    },
                    "allow_recording": False
                }
            }
            await websocket.send(json.dumps(session_msg))
            print("Session configured")
            
            # List available MCP tools
            tools_msg = {
                "type": "mcp.tools.available"
            }
            await websocket.send(json.dumps(tools_msg))
            print("Requested MCP tools list")
            
            # Wait for response
            await asyncio.sleep(2)
            
            # Execute time tool directly
            time_tool_msg = {
                "type": "mcp.tool.execute",
                "tool_name": "time.get_current_time",
                "arguments": {
                    "timezone": "Europe/London"
                }
            }
            await websocket.send(json.dumps(time_tool_msg))
            print("Executed time.get_current_time tool")
            
            # Listen for responses
            start_time = time.time()
            timeout = 30  # 30 second timeout
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    # Print all relevant events
                    event_type = data.get("type", "unknown")
                    print(f"\n📨 {event_type}: {json.dumps(data, indent=2)}")
                    
                    if event_type == "error":
                        print(f"❌ Error: {data.get('error', {}).get('message', 'Unknown')}")
                    elif event_type == "mcp.tools.available":
                        tools = data.get("tools", [])
                        print(f"🔧 Available tools: {[t.get('name') for t in tools]}")
                    elif event_type == "mcp.tool.result":
                        result = data.get("result", {})
                        print(f"⏰ Tool result: {result}")
                        break
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"\nError receiving: {e}")
                    break
            
            print("\nTest completed")
            
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_time_question())