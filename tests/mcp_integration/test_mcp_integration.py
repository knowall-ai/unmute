#!/usr/bin/env python3
"""Comprehensive MCP integration tests for Unmute"""

import asyncio
import json
import subprocess
import time
from openai import AsyncOpenAI

class MCPTester:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="dummy"
        )
        
    async def test_tool_call_generation(self):
        """Test if LLM generates TOOL_CALL correctly"""
        print("=== Testing TOOL_CALL Generation ===\n")
        
        system_prompt = """You are a helpful assistant.

# AVAILABLE TOOLS (MCP)

You have access to the following tools:

## datetime.get_current_time
Get the current time
Input schema: {}

## datetime.get_day_of_week
Get the current day of the week
Input schema: {}

To use a tool, respond with:
TOOL_CALL: tool_name(arguments)

Example: TOOL_CALL: datetime.get_current_time()"""
        
        test_cases = [
            ("What time is it?", "datetime.get_current_time"),
            ("What day is it today?", "datetime.get_day_of_week"),
        ]
        
        for question, expected_tool in test_cases:
            print(f"Q: {question}")
            response = await self.client.chat.completions.create(
                model="llama3.2:3b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip()
            print(f"A: {result}")
            
            if "TOOL_CALL:" in result and expected_tool in result:
                print("✓ Success\n")
            else:
                print("✗ Failed\n")
    
    def test_backend_mcp_initialization(self):
        """Check if backend initializes MCP correctly"""
        print("=== Testing Backend MCP Initialization ===\n")
        
        # Check recent logs
        result = subprocess.run(
            ["docker", "logs", "unmute-backend", "--tail", "50"],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout + result.stderr
        
        checks = [
            ("MCP manager initialized", "MCP manager initialized successfully"),
            ("Tools available", "Available MCP tools:"),
            ("System prompt updated", "MCP tools added to system prompt"),
        ]
        
        for check_name, check_string in checks:
            if check_string in logs:
                print(f"✓ {check_name}")
            else:
                print(f"✗ {check_name}")
        
        print()
    
    def reset_conversation(self):
        """Reset backend to clear conversation state"""
        print("=== Resetting Conversation ===\n")
        subprocess.run(["docker", "restart", "unmute-backend"], capture_output=True)
        print("Waiting for backend to restart...")
        time.sleep(5)
        print("✓ Backend restarted\n")

async def main():
    tester = MCPTester()
    
    # Run tests
    tester.reset_conversation()
    await tester.test_tool_call_generation()
    tester.test_backend_mcp_initialization()
    
    print("\n=== Next Steps ===")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Select a voice")
    print("3. Ask: 'What time is it?' or 'What day is it today?'")
    print("4. The system should use MCP tools to respond with actual time/day")
    print("\nMonitor logs with:")
    print("docker logs -f unmute-backend | grep -E 'TOOL_CALL|MCP|Tool result'")

if __name__ == "__main__":
    asyncio.run(main())