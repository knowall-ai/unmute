#!/usr/bin/env python3
"""Test actual MCP tool execution."""
import asyncio
import json
import websockets

async def test_tool_execution():
    uri = "ws://localhost:8765/v1/realtime"
    
    async with websockets.connect(uri, subprotocols=["realtime", "model.continuerun.com"]) as websocket:
        print("Connected to Unmute WebSocket")
        
        # Setup session
        await websocket.send(json.dumps({
            "type": "session.update", 
            "session": {
                "voice": "alloy",
                "allow_recording": False
            }
        }))
        
        await asyncio.sleep(2)
        
        # Test 1: Execute get_current_time with no parameters
        print("\n1. Testing get_current_time (default timezone)...")
        await websocket.send(json.dumps({
            "type": "mcp.tool.execute",
            "tool_name": "time.get_current_time",
            "arguments": {}
        }))
        
        # Test 2: Execute get_current_time with specific timezone
        print("\n2. Testing get_current_time (New York)...")
        await websocket.send(json.dumps({
            "type": "mcp.tool.execute",
            "tool_name": "time.get_current_time",
            "arguments": {"timezone": "America/New_York"}
        }))
        
        # Test 3: Execute convert_time
        print("\n3. Testing convert_time...")
        await websocket.send(json.dumps({
            "type": "mcp.tool.execute",
            "tool_name": "time.convert_time",
            "arguments": {
                "time": "3:00 PM",
                "from_timezone": "America/New_York",
                "to_timezone": "Europe/London"
            }
        }))
        
        # Listen for responses
        timeout = 15
        start_time = asyncio.get_event_loop().time()
        execution_count = 0
        
        while asyncio.get_event_loop().time() - start_time < timeout and execution_count < 3:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)
                msg_type = data.get('type')
                
                if msg_type == "mcp.tool.execute.response":
                    execution_count += 1
                    result = data.get("result", "No result")
                    print(f"\n✓ Tool execution #{execution_count} result: {result}")
                elif msg_type == "error":
                    error = data.get("error", {})
                    print(f"\n✗ Error: {error.get('message', 'Unknown error')}")
                    if error.get('details'):
                        print(f"   Details: {json.dumps(error['details'], indent=2)}")
                else:
                    print(f"   Received: {msg_type}")
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"\n✗ Exception: {e}")
                break
                
        print(f"\n{'='*60}")
        print(f"Summary: {execution_count}/3 tool executions completed")

if __name__ == "__main__":
    asyncio.run(test_tool_execution())