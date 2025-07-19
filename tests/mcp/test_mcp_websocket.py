#!/usr/bin/env python3
"""Test MCP functionality via WebSocket connection."""
import asyncio
import json
import websockets

async def test_mcp_time():
    """Test MCP time functionality through Unmute WebSocket."""
    uri = "ws://localhost:8765/v1/realtime"
    
    async with websockets.connect(uri, subprotocols=["realtime", "model.continuerun.com"]) as websocket:
        print("Connected to Unmute WebSocket")
        
        # Send initial session update
        await websocket.send(json.dumps({
            "type": "session.update",
            "session": {
                "instructions": "You are a helpful assistant with access to MCP tools.",
                "voice": "alloy"
            }
        }))
        
        # Wait for connection to stabilize
        await asyncio.sleep(2)
        
        # Send a message asking for the time
        await websocket.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "What time is it?"
                    }
                ]
            }
        }))
        
        # Send response create to trigger the assistant
        await websocket.send(json.dumps({
            "type": "response.create"
        }))
        
        # Listen for responses
        timeout = 30  # 30 seconds timeout
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(message)
                
                print(f"Received: {data.get('type', 'unknown')}")
                
                # Look for assistant messages or tool calls
                if data.get("type") == "conversation.item.created":
                    item = data.get("item", {})
                    if item.get("role") == "assistant":
                        content = item.get("content", [])
                        for c in content:
                            if c.get("type") == "text":
                                print(f"Assistant: {c.get('text', '')}")
                
                # Check for tool call execution
                if "tool" in str(data).lower() or "mcp" in str(data).lower():
                    print(f"Tool-related message: {json.dumps(data, indent=2)}")
                    
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_mcp_time())