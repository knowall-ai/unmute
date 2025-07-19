#!/usr/bin/env python3
"""Test MCP server subprocess execution directly."""
import asyncio
import json
import subprocess

async def test_mcp_subprocess():
    """Test the exact subprocess approach we're using."""
    print("Testing MCP subprocess execution")
    print("=" * 60)
    
    cmd = ["uvx", "mcp-server-time", "--local-timezone", "Europe/London"]
    
    try:
        # Start the process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"✓ Started process: {' '.join(cmd)}")
        
        # Send initialize request
        init_request = json.dumps({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"}
            },
            "id": 1
        }) + '\n'
        
        print(f"\n→ Sending init request...")
        process.stdin.write(init_request.encode())
        await process.stdin.drain()
        
        # Read initialization response
        print("← Waiting for init response...")
        init_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
        print(f"✓ Init response: {init_response_line.decode().strip()}")
        
        init_response = json.loads(init_response_line.decode())
        if 'error' in init_response:
            print(f"✗ Init error: {init_response['error']}")
            return
        
        # Send tool call request
        tool_request = json.dumps({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_current_time",
                "arguments": {}
            },
            "id": 2
        }) + '\n'
        
        print(f"\n→ Sending tool request...")
        process.stdin.write(tool_request.encode())
        await process.stdin.drain()
        
        # Read tool response
        print("← Waiting for tool response...")
        tool_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
        print(f"✓ Tool response: {tool_response_line.decode().strip()}")
        
        tool_response = json.loads(tool_response_line.decode())
        if 'error' in tool_response:
            print(f"\n✗ Tool error: {tool_response['error']}")
        else:
            result = tool_response.get('result', {})
            content = result.get('content', [])
            for item in content:
                if item.get('type') == 'text':
                    print(f"\n✅ SUCCESS! Time: {item.get('text')}")
        
        # Clean up
        process.stdin.close()
        await process.wait()
        
        # Check stderr
        stderr = await process.stderr.read()
        if stderr:
            print(f"\nStderr output:\n{stderr.decode()}")
            
    except asyncio.TimeoutError:
        print("\n✗ Timeout!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_subprocess())