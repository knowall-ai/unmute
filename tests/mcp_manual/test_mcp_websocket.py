#!/usr/bin/env python3
"""Test MCP backend websocket connection"""

import asyncio
import json
import websockets

async def test_mcp_backend():
    uri = "ws://localhost:8766/v1/realtime"
    
    print(f"Connecting to {uri}...")
    
    async with websockets.connect(uri, subprotocols=["realtime"]) as websocket:
        print("Connected! Waiting for messages...")
        
        # Send initial session config
        await websocket.send(json.dumps({
            "type": "session.update",
            "session": {
                "instructions": "You are a helpful assistant.",
                "voice": "alloy"
            }
        }))
        
        # Listen for messages
        try:
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"Received: {data.get('type', 'unknown')}")
                
                # Check for MCP tool discovery
                if data.get('type') == 'session.updated':
                    print("Session updated successfully")
                    
                # Send a message asking about time
                if data.get('type') == 'session.updated':
                    print("\nSending time question...")
                    await websocket.send(json.dumps({
                        "type": "conversation.item.create",
                        "item": {
                            "type": "message",
                            "role": "user",
                            "content": [{
                                "type": "text",
                                "text": "What time is it?"
                            }]
                        }
                    }))
                    
                    await websocket.send(json.dumps({
                        "type": "response.create"
                    }))
                    
                # Look for tool calls
                if 'TOOL_CALL' in str(data):
                    print(f"Tool call detected: {data}")
                    
                # Print any text responses
                if data.get('type') == 'response.text.delta':
                    print(f"Response: {data.get('delta', '')}")
                    
        except asyncio.TimeoutError:
            print("\nTimeout - no more messages")
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_backend())