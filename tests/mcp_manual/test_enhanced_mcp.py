#!/usr/bin/env python3
"""Test the enhanced MCP integration."""
import asyncio
import websockets
import json

async def test_enhanced_mcp():
    """Test the enhanced MCP system prompt and tool calling."""
    uri = "ws://localhost:8766/v1/realtime"
    
    try:
        async with websockets.connect(uri, subprotocols=["realtime"]) as websocket:
            print("✅ Connected to enhanced MCP backend")
            
            # Send session configuration
            session_msg = {
                "type": "session.update",
                "session": {
                    "instructions": {
                        "type": "constant",
                        "text": "You are a helpful assistant."
                    },
                    "allow_recording": False
                }
            }
            await websocket.send(json.dumps(session_msg))
            print("📝 Session configured")
            
            # Check available tools
            tools_msg = {"type": "mcp.tools.available"}
            await websocket.send(json.dumps(tools_msg))
            print("🔧 Requested available tools")
            
            # Wait for responses
            timeout = 10
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    event_type = data.get("type", "unknown")
                    
                    if event_type == "session.updated":
                        print("✅ Session updated successfully")
                    elif event_type == "mcp.tools.available.response":
                        tools = data.get("tools", [])
                        print(f"🔧 Available tools: {[t.get('name') for t in tools]}")
                        
                        # Execute time tool directly to test interpretation
                        if tools:
                            time_tool_msg = {
                                "type": "mcp.tool.execute",
                                "tool_name": "time.get_current_time",
                                "arguments": {"timezone": "Europe/London"}
                            }
                            await websocket.send(json.dumps(time_tool_msg))
                            print("⏰ Executed time tool")
                        
                    elif event_type == "mcp.tool.execute.response":
                        tool_name = data.get("tool_name")
                        result = data.get("result")
                        success = data.get("success")
                        print(f"📊 Tool {tool_name} result (success={success}):")
                        print(f"   {result}")
                        break
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
            
            print("✅ Test completed")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_mcp())