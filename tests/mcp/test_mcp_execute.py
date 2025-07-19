#!/usr/bin/env python3
"""Test MCP tool execution via WebSocket."""
import asyncio
import json
import websockets

async def test_mcp_tool_execution():
    """Test executing MCP tools through Unmute WebSocket."""
    uri = "ws://localhost:8765/v1/realtime"
    
    async with websockets.connect(uri, subprotocols=["realtime", "model.continuerun.com"]) as websocket:
        print("Connected to Unmute WebSocket")
        
        # Set up the session
        await websocket.send(json.dumps({
            "type": "session.update", 
            "session": {
                "instructions": {
                    "text": "You are a helpful assistant."
                },
                "voice": "alloy",
                "allow_recording": False
            }
        }))
        
        await asyncio.sleep(1)
        
        # Test executing the time tool
        print("\n--- Testing mcp.tool.execute for current time ---")
        await websocket.send(json.dumps({
            "type": "mcp.tool.execute",
            "tool_name": "time.get_current_time",
            "arguments": {}
        }))
        
        # Test with specific timezone
        print("\n--- Testing mcp.tool.execute for New York time ---")
        await websocket.send(json.dumps({
            "type": "mcp.tool.execute",
            "tool_name": "time.get_current_time",
            "arguments": {
                "timezone": "America/New_York"
            }
        }))
        
        # Listen for responses
        timeout = 15
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(message)
                
                msg_type = data.get('type', 'unknown')
                print(f"\nReceived: {msg_type}")
                
                if 'mcp' in msg_type or msg_type == "error":
                    print(json.dumps(data, indent=2))
                    
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_mcp_tool_execution())