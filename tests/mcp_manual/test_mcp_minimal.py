#!/usr/bin/env python3
"""Minimal test to check MCP backend connectivity and tool availability."""
import asyncio
import aiohttp
import json

async def test_mcp_http():
    """Test MCP backend via HTTP endpoints."""
    base_url = "http://localhost:8001"
    
    print("MCP Backend HTTP Test")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        print("\n1. Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✓ Health check passed: {data}")
                else:
                    print(f"   ✗ Health check failed: {resp.status}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            
        # Test 2: Metrics
        print("\n2. Testing metrics endpoint...")
        try:
            async with session.get(f"{base_url}/metrics") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    print(f"   ✓ Metrics available ({len(text)} bytes)")
                else:
                    print(f"   ✗ Metrics failed: {resp.status}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            
        # Test 3: Try to get more info
        print("\n3. Testing other endpoints...")
        for endpoint in ["/", "/api", "/v1", "/docs"]:
            try:
                async with session.get(f"{base_url}{endpoint}") as resp:
                    print(f"   {endpoint}: {resp.status} {resp.reason}")
            except Exception as e:
                print(f"   {endpoint}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_http())