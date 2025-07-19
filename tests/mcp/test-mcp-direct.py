#!/usr/bin/env python3
"""Direct test of MCP functionality without audio"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import asyncio
import logging
from unmute.mcp.mcp_manager import MCPManager
from unmute.unmute_handler import UnmuteHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_mcp_direct():
    """Test MCP directly without voice interaction"""
    print("🧪 Direct MCP Test")
    print("=" * 60)
    
    # Initialize MCP manager
    print("\n📦 Initializing MCP Manager...")
    mcp_manager = MCPManager()
    await mcp_manager.initialize()
    
    # List available tools
    tools = mcp_manager.get_available_tools()
    print(f"\n🔧 Available MCP tools: {', '.join(tools)}")
    
    # Test 1: Get current time without timezone (should use default)
    print("\n🎯 Test 1: Get current time (no timezone)")
    try:
        result = await mcp_manager.execute_tool("time.get_current_time", {})
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get current time with timezone
    print("\n🎯 Test 2: Get current time (Europe/London)")
    try:
        result = await mcp_manager.execute_tool("time.get_current_time", {"timezone": "Europe/London"})
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get current time with location name
    print("\n🎯 Test 3: Get current time (New York)")
    try:
        result = await mcp_manager.execute_tool("time.get_current_time", {"timezone": "New York"})
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Convert time between timezones
    print("\n🎯 Test 4: Convert time between timezones")
    try:
        result = await mcp_manager.execute_tool("time.convert_time", {
            "time": "2pm",
            "from_timezone": "London",
            "to_timezone": "Tokyo"
        })
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Direct MCP test complete")

if __name__ == "__main__":
    asyncio.run(test_mcp_direct())