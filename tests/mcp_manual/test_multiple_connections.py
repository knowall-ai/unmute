#!/usr/bin/env python3
"""Test multiple simultaneous WebSocket connections to unmute backend."""
import asyncio
import websockets
import json
import time

async def test_connection(connection_id):
    """Test a single WebSocket connection."""
    uri = "ws://localhost:8766/api/chat"  # Using MCP backend
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connection {connection_id}: Connected")
            
            # Send a simple message
            message = {
                "type": "session.update",
                "session": {
                    "instructions": f"You are connection {connection_id}. Just say hello.",
                    "input_audio_transcription": {"model": "whisper-1"}
                }
            }
            await websocket.send(json.dumps(message))
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Send a test message
            test_msg = {
                "type": "input_audio_buffer.append",
                "audio": ""  # Empty audio for now
            }
            await websocket.send(json.dumps(test_msg))
            
            # Keep connection alive for a bit
            await asyncio.sleep(5)
            
            print(f"Connection {connection_id}: Closing")
            
    except Exception as e:
        print(f"Connection {connection_id}: Error - {e}")

async def main():
    """Test multiple connections simultaneously."""
    print("Testing multiple WebSocket connections...")
    
    # Test with 5 simultaneous connections
    tasks = [test_connection(i) for i in range(1, 6)]
    await asyncio.gather(*tasks)
    
    print("All connections completed!")

if __name__ == "__main__":
    asyncio.run(main())