#!/usr/bin/env python3
"""Test MCP through voice interaction simulation."""
import asyncio
import json
import websockets
from datetime import datetime

async def test_voice_time_query():
    """Test asking for time through simulated voice."""
    uri = "ws://localhost:8765/v1/realtime"
    
    print("MCP Voice Interaction Test")
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
            
            # Give time for MCP to initialize
            await asyncio.sleep(3)
            
            # Simulate user saying "What time is it?"
            print("\n📢 Simulating user voice: 'What time is it?'")
            
            # Send the conversation item with the user's message
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
            
            # Trigger response generation
            await websocket.send(json.dumps({
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"]
                }
            }))
            
            # Listen for responses
            print("\n⏳ Waiting for assistant response...")
            start_time = asyncio.get_event_loop().time()
            timeout = 30
            response_text = []
            tool_execution_seen = False
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    msg_type = data.get('type')
                    
                    if msg_type == "response.text.delta":
                        delta = data.get("delta", "")
                        response_text.append(delta)
                        print(f".", end="", flush=True)
                        
                    elif msg_type == "response.text.done":
                        full_response = "".join(response_text)
                        print(f"\n\n🤖 Assistant response: {full_response}")
                        
                        if "TOOL_CALL:" in full_response:
                            print("✓ Tool call detected in response!")
                            tool_execution_seen = True
                        break
                        
                    elif msg_type == "error":
                        error = data.get("error", {})
                        print(f"\n✗ Error: {error.get('message', 'Unknown error')}")
                        break
                        
                    elif "mcp.tool.execute" in str(data):
                        print(f"\n✓ MCP tool execution detected: {data}")
                        tool_execution_seen = True
                        
                except asyncio.TimeoutError:
                    continue
            
            print("\n" + "=" * 60)
            if tool_execution_seen:
                print("✅ Test PASSED: MCP tool was invoked")
            else:
                print("❌ Test FAILED: MCP tool was not invoked")
                print("   The assistant should have used time.get_current_time()")
            
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_voice_time_query())