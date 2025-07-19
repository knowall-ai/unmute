#!/usr/bin/env python3
"""Test MCP directly inside the container"""

import subprocess
import sys

# Run the test inside the Docker container
cmd = [
    "docker", "exec", "unmute-backend", "python3", "-c",
    """
import asyncio
import logging
from unmute.mcp.mcp_manager import MCPManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test():
    print('🧪 Testing MCP Manager directly...')
    print('=' * 50)
    
    mcp = MCPManager()
    await mcp.initialize()
    
    tools = mcp.get_available_tools()
    print(f'\\n✅ Discovered tools: {[t["name"] for t in tools]}')
    
    # Test 1: Without timezone
    print('\\n📍 Test 1: Get time without timezone')
    try:
        result = await mcp.execute_tool('time.get_current_time', {})
        print(f'Result: {result}')
    except Exception as e:
        print(f'❌ Error: {e}')
    
    # Test 2: With timezone
    print('\\n📍 Test 2: Get time with timezone')
    try:
        result = await mcp.execute_tool('time.get_current_time', {'timezone': 'Europe/London'})
        print(f'✅ Result: {result}')
    except Exception as e:
        print(f'❌ Error: {e}')
    
    print('\\n' + '=' * 50)
    print('✅ Test complete!')

asyncio.run(test())
"""
]

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)