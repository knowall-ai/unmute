#!/usr/bin/env python3
"""Comprehensive MCP Time Test"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime

def test_direct_mcp():
    """Test MCP server directly"""
    print("🧪 Test 1: Direct MCP Server Test")
    print("=" * 50)
    
    # Create test script
    test_script = """
import json
import sys
import time

# Initialize
print(json.dumps({"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}))
sys.stdout.flush()
response = sys.stdin.readline()
print(f"Init: {json.loads(response).get('result', {}).get('serverInfo', {}).get('name')}", file=sys.stderr)

# Send initialized
print(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"}))
sys.stdout.flush()
time.sleep(0.1)

# Get current time
print(json.dumps({"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_current_time","arguments":{"timezone":"Europe/London"}},"id":2}))
sys.stdout.flush()
response = sys.stdin.readline()
result = json.loads(response)
if 'result' in result:
    content = result['result']['content'][0]['text']
    data = json.loads(content)
    print(f"✅ Time: {data['datetime']}", file=sys.stderr)
else:
    print(f"❌ Error: {result}", file=sys.stderr)
"""
    
    # Run test
    proc = subprocess.Popen(
        ['docker', 'exec', '-i', 'unmute-backend-1', 'sh', '-c', 
         f'echo {repr(test_script)} | python3 | uvx mcp-server-time --local-timezone Europe/London 2>&1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = proc.communicate()
    if "✅ Time:" in stderr:
        print("✅ Direct MCP test passed")
        print(f"   {stderr.strip()}")
    else:
        print("❌ Direct MCP test failed")
        print(f"   Output: {stdout}")
        print(f"   Error: {stderr}")
    print()

def test_backend_tools():
    """Test backend tool discovery"""
    print("🧪 Test 2: Backend Tool Discovery")
    print("=" * 50)
    
    result = subprocess.run(
        ['docker', 'logs', 'unmute-backend-1'],
        capture_output=True,
        text=True
    )
    
    logs = result.stderr
    if "Available MCP tools: time.get_current_time, time.convert_time" in logs:
        print("✅ Tools discovered correctly")
        # Find most recent discovery
        for line in logs.split('\n')[-100:]:
            if "Available MCP tools:" in line:
                print(f"   {line.strip()}")
                break
    else:
        print("❌ Tools not discovered")
    print()

def test_tool_execution():
    """Test recent tool executions"""
    print("🧪 Test 3: Recent Tool Executions")
    print("=" * 50)
    
    result = subprocess.run(
        ['docker', 'logs', 'unmute-backend-1'],
        capture_output=True,
        text=True
    )
    
    logs = result.stderr
    executions = []
    errors = []
    
    for line in logs.split('\n')[-500:]:
        if "Executing MCP tool: time.get_current_time" in line:
            executions.append(line)
        elif "Tool result:" in line and "datetime" in logs[logs.find(line):logs.find(line)+200]:
            executions.append("✅ Successful execution")
        elif "Failed to execute tool" in line:
            errors.append(line)
    
    if executions:
        print(f"✅ Found {len(executions)} tool execution attempts")
        for exec in executions[-3:]:
            print(f"   {exec.strip()}")
    else:
        print("❌ No tool executions found")
    
    if errors:
        print(f"\n⚠️  Found {len(errors)} errors:")
        for error in errors[-3:]:
            print(f"   {error.strip()}")
    print()

def test_system_prompt():
    """Check if system prompt includes MCP tools"""
    print("🧪 Test 4: System Prompt Configuration")
    print("=" * 50)
    
    # Check if MCP tools are in system prompt
    result = subprocess.run(
        ['docker', 'exec', 'unmute-backend-1', 'python3', '-c',
         'from unmute.llm.system_prompt import get_default_instructions; print(get_default_instructions().make_system_prompt())'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        prompt = result.stdout
        if "AVAILABLE TOOLS" in prompt and "time.get_current_time" in prompt:
            print("✅ MCP tools in system prompt")
        else:
            print("❌ MCP tools NOT in system prompt")
            print("   This explains why the LLM thinks it doesn't have time access!")
    else:
        print("❌ Could not check system prompt")
        print(f"   Error: {result.stderr}")
    print()

def test_voice_flow():
    """Test the voice interaction flow"""
    print("🧪 Test 5: Voice Interaction Flow")
    print("=" * 50)
    
    print("📝 To test voice interaction:")
    print("1. Open http://localhost:3000")
    print("2. Click Play button")
    print("3. Say: 'What time is it?'")
    print()
    print("Expected flow:")
    print("  → LLM outputs: TOOL_CALL: time.get_current_time()")
    print("  → Backend executes MCP tool")
    print("  → Tool returns time data")
    print("  → LLM interprets result")
    print("  → TTS speaks: 'The current time in London is...'")
    print()

if __name__ == "__main__":
    print("🔍 Comprehensive MCP Time Test")
    print("=" * 70)
    print(f"Test time: {datetime.now()}")
    print()
    
    test_direct_mcp()
    test_backend_tools()
    test_tool_execution()
    test_system_prompt()
    test_voice_flow()
    
    print("=" * 70)
    print("📊 Test Summary:")
    print("- If Test 1 passes: MCP server works")
    print("- If Test 2 passes: Tools are discovered")
    print("- If Test 3 shows errors: Check the error messages")
    print("- If Test 4 fails: System prompt needs MCP tools added")
    print("- Test 5: Manual voice test required")