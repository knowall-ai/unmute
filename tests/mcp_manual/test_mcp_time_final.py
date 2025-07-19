#!/usr/bin/env python3
"""Final test of MCP time functionality with retries and better error handling."""
import asyncio
import json
import websockets
from datetime import datetime
import time

async def wait_for_services():
    """Wait for backend services to be fully ready."""
    print("⏳ Waiting for services to stabilize...")
    await asyncio.sleep(3)
    print("✓ Services should be ready")

async def test_mcp_time_with_retries():
    """Connect to MCP backend and ask for the current time with retries."""
    uri = "ws://localhost:8001/v1/realtime"
    max_retries = 3
    
    print("MCP Backend Time Test (with retries)")
    print("=" * 60)
    print(f"Target: {uri}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    await wait_for_services()
    
    for attempt in range(1, max_retries + 1):
        print(f"\nAttempt {attempt}/{max_retries}")
        print("-" * 40)
        
        try:
            async with websockets.connect(uri, subprotocols=["realtime"]) as websocket:
                print("✓ Connected to WebSocket")
                
                # Try minimal session first
                print("📤 Sending minimal session config...")
                await websocket.send(json.dumps({
                    "type": "session.update", 
                    "session": {
                        "modalities": ["text"],
                        "temperature": 0.7,
                        "allow_recording": False,
                        "voice": "alloy"
                    }
                }))
                
                # Wait and collect early responses
                await asyncio.sleep(1)
                
                # Check if connection is still open
                try:
                    pong = await websocket.ping()
                    print("✓ Connection alive (ping successful)")
                except:
                    print("✗ Connection lost during setup")
                    continue
                
                # Send user message
                print("\n📤 Creating user message...")
                await websocket.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "What time is it in London?"
                            }
                        ]
                    }
                }))
                
                # Trigger response
                print("📤 Triggering response...")
                await websocket.send(json.dumps({
                    "type": "response.create"
                }))
                
                # Monitor responses
                print("\n⏳ Monitoring for responses...")
                start_time = time.time()
                timeout = 20
                
                response_parts = []
                tool_calls = []
                
                while time.time() - start_time < timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        msg_type = data.get('type', 'unknown')
                        
                        # Log key events
                        if msg_type in ["session.updated", "conversation.item.created", 
                                       "response.created", "response.done"]:
                            print(f"✓ {msg_type}")
                            
                        elif msg_type == "response.text.delta":
                            delta = data.get("delta", "")
                            response_parts.append(delta)
                            if "TOOL_CALL" in delta or "mcp__" in delta:
                                print(f"🔧 Tool reference detected: {delta.strip()}")
                                
                        elif msg_type == "response.text.done":
                            full_text = "".join(response_parts)
                            print(f"\n🤖 Response: {full_text}")
                            
                        elif msg_type == "response.function_call_arguments.done":
                            print(f"🔧 Function call: {data.get('arguments', '')}")
                            tool_calls.append(data.get('arguments', ''))
                            
                        elif msg_type == "error":
                            error = data.get("error", {})
                            print(f"\n❌ Error: {error.get('message', 'Unknown')}")
                            if "details" in error:
                                print(f"   Details: {error['details']}")
                            break
                            
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"\n✗ Error during monitoring: {e}")
                        break
                
                # Summary
                print("\n" + "-" * 40)
                print(f"Attempt {attempt} Summary:")
                print(f"  Response received: {'Yes' if response_parts else 'No'}")
                print(f"  Tool calls: {len(tool_calls)}")
                
                if response_parts or tool_calls:
                    print("\n✅ Test SUCCESSFUL!")
                    return True
                    
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"✗ Connection rejected: {e}")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"✗ Connection closed: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {type(e).__name__}: {e}")
            
        if attempt < max_retries:
            wait_time = attempt * 2
            print(f"\n⏳ Waiting {wait_time} seconds before retry...")
            await asyncio.sleep(wait_time)
    
    print("\n" + "=" * 60)
    print("❌ Test FAILED after all retries")
    return False

async def main():
    """Run the test and play completion sound."""
    success = await test_mcp_time_with_retries()
    
    # Play completion sound as requested in CLAUDE.md
    try:
        import subprocess
        subprocess.run(["canberra-gtk-play", "-i", "complete"], check=False)
    except:
        pass
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)