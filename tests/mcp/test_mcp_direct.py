#!/usr/bin/env python3
"""Test MCP functionality directly via WebSocket MCP endpoints."""
import asyncio
import json
import websockets

async def test_mcp_endpoints():
    """Test MCP endpoints through Unmute WebSocket."""
    uri = "ws://localhost:8765/v1/realtime"
    
    async with websockets.connect(uri, subprotocols=["realtime", "model.continuerun.com"]) as websocket:
        print("Connected to Unmute WebSocket")
        
        # First, set up the session properly
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
        
        # Wait for session confirmation
        await asyncio.sleep(1)
        
        # Test 1: List MCP servers
        print("\n--- Testing mcp.servers.list ---")
        await websocket.send(json.dumps({
            "type": "mcp.servers.list"
        }))
        
        # Test 2: List available tools
        print("\n--- Testing mcp.tools.available ---")
        await websocket.send(json.dumps({
            "type": "mcp.tools.available"
        }))
        
        # Listen for responses
        timeout = 10
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(message)
                
                msg_type = data.get('type', 'unknown')
                print(f"\nReceived: {msg_type}")
                
                # Pretty print MCP responses
                if 'mcp' in msg_type:
                    print(json.dumps(data, indent=2))
                elif msg_type == "error":
                    print(f"Error: {data.get('error', {}).get('message', 'Unknown error')}")
                    
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_mcp_endpoints())