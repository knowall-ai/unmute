#!/usr/bin/env python3
"""Test script for real MCP SDK integration."""
import asyncio
import logging
import sys
from unmute.mcp.mcp_manager import MCPManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp():
    """Test MCP functionality with real SDK."""
    manager = MCPManager()
    
    try:
        # Initialize the manager
        logger.info("Initializing MCP manager...")
        await manager.initialize()
        
        # List available tools
        tools = manager.get_available_tools()
        logger.info(f"Available tools: {len(tools)}")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")
        
        # Get tools description for prompt
        tools_prompt = manager.get_tools_for_prompt()
        logger.info(f"\nTools for prompt:\n{tools_prompt}")
        
        # Test tool execution
        if "time.get_current_time" in manager.available_tools:
            logger.info("\nTesting get_current_time tool...")
            result = await manager.execute_tool("time.get_current_time", {})
            logger.info(f"Current time result: {result}")
            
            # Test with location
            logger.info("\nTesting get_current_time with location...")
            result = await manager.execute_tool("time.get_current_time", {"timezone": "America/New_York"})
            logger.info(f"New York time result: {result}")
        
        logger.info("\nMCP test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await manager.shutdown()

if __name__ == "__main__":
    asyncio.run(test_mcp())