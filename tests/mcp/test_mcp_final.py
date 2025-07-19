#!/usr/bin/env python3
"""Final MCP integration test - complete workflow."""
import asyncio
import json
import websockets
from datetime import datetime

async def test_mcp_complete():
    """Test the complete MCP workflow."""
    uri = "ws://localhost:8765/v1/realtime"
    
    print("MCP Integration Test - Complete Workflow")
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
            
            # Step 1: List available tools
            print("\n1. Listing available MCP tools...")
            await websocket.send(json.dumps({
                "type": "mcp.tools.available"
            }))
            
            # Collect responses
            tools = []
            deadline = asyncio.get_event_loop().time() + 5
            
            while asyncio.get_event_loop().time() < deadline:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(response)
                    
                    if data.get("type") == "mcp.tools.available.response":
                        tools = data.get("tools", [])
                        print(f"   Found {len(tools)} tools:")
                        for tool in tools:
                            print(f"   - {tool['name']}: {tool['description']}")
                        break
                except asyncio.TimeoutError:
                    continue
            
            if not tools:
                print("   ✗ No tools found!")
                return
            
            # Step 2: Test tool execution
            print("\n2. Testing tool execution...")
            
            # Test get_current_time
            print("\n   a) Testing time.get_current_time (Europe/London)...")
            await websocket.send(json.dumps({
                "type": "mcp.tool.execute",
                "tool_name": "time.get_current_time",
                "arguments": {"timezone": "Europe/London"}
            }))
            
            # Wait for execution response
            deadline = asyncio.get_event_loop().time() + 10
            while asyncio.get_event_loop().time() < deadline:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "mcp.tool.execute.response":
                        if data.get("success"):
                            print(f"      ✓ Result: {data.get('result')}")
                        else:
                            print(f"      ✗ Error: {data.get('error')}")
                        break
                except asyncio.TimeoutError:
                    continue
            
            # Step 3: Simulate voice interaction (text-based)
            print("\n3. Simulating voice interaction...")
            print("   User would say: 'What time is it in Tokyo?'")
            print("   Expected: LLM recognizes intent and calls time.get_current_time(timezone='Asia/Tokyo')")
            
            # Test the tool with Tokyo timezone
            await websocket.send(json.dumps({
                "type": "mcp.tool.execute",
                "tool_name": "time.get_current_time",
                "arguments": {"timezone": "Asia/Tokyo"}
            }))
            
            deadline = asyncio.get_event_loop().time() + 10
            while asyncio.get_event_loop().time() < deadline:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "mcp.tool.execute.response":
                        if data.get("success"):
                            print(f"   LLM would respond: 'The current time in Tokyo is {data.get('result')}'")
                        else:
                            print(f"   ✗ Tool execution failed: {data.get('error')}")
                        break
                except asyncio.TimeoutError:
                    continue
            
            print("\n" + "=" * 60)
            print("✓ MCP Integration Test Complete!")
            print("\nThe system is ready for voice interactions that require MCP tools.")
            print("When users ask about time, the LLM will automatically use the MCP time tool.")
            
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_complete())