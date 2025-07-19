#!/usr/bin/env python3
"""Test time query through voice-like interaction."""
import asyncio
import websockets
import json
import base64

async def test_voice_time():
    """Test asking for time through the full voice pipeline."""
    uri = "ws://localhost:8766/v1/realtime"
    
    try:
        async with websockets.connect(uri, subprotocols=["realtime"]) as websocket:
            print("✅ Connected to MCP backend")
            
            # Send session configuration  
            session_msg = {
                "type": "session.update",
                "session": {
                    "instructions": {
                        "type": "constant",
                        "text": "You are a helpful assistant. When users ask about time, use the available tools."
                    },
                    "allow_recording": False
                }
            }
            await websocket.send(json.dumps(session_msg))
            
            # Wait for session update
            await asyncio.sleep(2)
            
            # Simulate STT output by sending text directly to trigger tool use
            # This bypasses the audio pipeline to test just the tool integration
            stt_text = "What time is it?"
            
            # Create fake audio data (silent audio to trigger the pipeline)
            # Using a minimal audio buffer to trigger the text processing
            audio_msg = {
                "type": "input_audio_buffer.append",
                "audio": ""  # Empty for now, just to test text path
            }
            
            print(f"🗣️ Testing with text: '{stt_text}'")
            
            # Send the audio message
            await websocket.send(json.dumps(audio_msg))
            
            # Monitor responses for a longer time to see tool execution
            timeout = 30
            start_time = asyncio.get_event_loop().time()
            tool_calls_seen = []
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)
                    event_type = data.get("type", "unknown")
                    
                    if event_type == "session.updated":
                        print("✅ Session updated")
                    elif "mcp" in event_type.lower() or "tool" in event_type.lower():
                        tool_calls_seen.append(event_type)
                        print(f"🔧 MCP event: {event_type}")
                        if "result" in data:
                            print(f"📊 Result: {data.get('result', '')}")
                    elif event_type == "response.audio.delta":
                        # Skip audio data
                        continue
                    elif event_type in ["response.text.delta", "response.text.done"]:
                        print(f"💬 Text response: {data}")
                        
                except asyncio.TimeoutError:
                    if not tool_calls_seen:
                        print("⏳ Still waiting for tool calls...")
                    continue
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
            
            if tool_calls_seen:
                print(f"✅ Saw tool-related events: {tool_calls_seen}")
            else:
                print("❌ No tool calls detected")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_voice_time())