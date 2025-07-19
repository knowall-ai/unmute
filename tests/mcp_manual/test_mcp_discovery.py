#!/usr/bin/env python3
"""Test MCP discovery by connecting to websocket."""
import asyncio
import json
import websockets

async def test_discovery():
    uri = "ws://localhost:8765/v1/realtime"
    
    try:
        async with websockets.connect(uri, subprotocols=["realtime", "model.continuerun.com"]) as websocket:
            print("Connected - check logs for MCP discovery")
            await asyncio.sleep(2)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_discovery())