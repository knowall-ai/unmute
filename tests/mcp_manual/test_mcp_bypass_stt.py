#!/usr/bin/env python3
"""Test MCP by bypassing STT/TTS requirements."""
import asyncio
import json
import websockets
from datetime import datetime

async def test_mcp_bypass():
    """Connect to MCP backend with minimal session config."""
    uri = "ws://localhost:8001/v1/realtime"
    
    print("MCP Backend Test (Bypassing STT/TTS)")
    print("=" * 60)
    print(f"Connecting to: {uri}")
    
    try:
        # Try connection without realtime subprotocol
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to MCP backend WebSocket (no subprotocol)")
            
            # Send minimal session update
            print("\n📤 Sending minimal session config...")
            await websocket.send(json.dumps({
                "type": "session.update", 
                "session": {}
            }))
            
            # Monitor for any response
            print("\n⏳ Monitoring responses...")
            timeout = 5
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    print(f"Received: {msg_type}")
                    
                    if msg_type == "error":
                        error = data.get("error", {})
                        print(f"  Error: {error.get('message', 'Unknown')}")
                        print(f"  Details: {json.dumps(error, indent=2)}")
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"Error receiving: {e}")
                    break
                    
    except Exception as e:
        print(f"\n❌ Failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_bypass())