#!/usr/bin/env python3
"""Comprehensive test suite for MCP integration."""
import asyncio
import json
import websockets
import sys

class MCPTester:
    def __init__(self):
        self.uri = "ws://localhost:8765/v1/realtime"
        self.results = []
        
    async def connect_and_setup(self):
        """Connect to WebSocket and setup session."""
        self.websocket = await websockets.connect(self.uri, subprotocols=["realtime", "model.continuerun.com"])
        print("✓ Connected to Unmute WebSocket")
        
        # Setup session (skip the problematic instructions field)
        await self.websocket.send(json.dumps({
            "type": "session.update", 
            "session": {
                "voice": "alloy",
                "allow_recording": False
            }
        }))
        await asyncio.sleep(1)
        return True
        
    async def test_list_servers(self):
        """Test listing MCP servers."""
        print("\n1. Testing mcp.servers.list...")
        await self.websocket.send(json.dumps({
            "type": "mcp.servers.list"
        }))
        
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
            data = json.loads(response)
            if data.get("type") == "mcp.servers.list.response":
                servers = data.get("servers", [])
                print(f"   ✓ Received server list: {len(servers)} servers")
                self.results.append(("List servers", True, f"{len(servers)} servers"))
                return True
            else:
                print(f"   ✗ Unexpected response: {data.get('type')}")
                self.results.append(("List servers", False, f"Unexpected: {data.get('type')}"))
                return False
        except Exception as e:
            print(f"   ✗ Error: {e}")
            self.results.append(("List servers", False, str(e)))
            return False
            
    async def test_list_tools(self):
        """Test listing available tools."""
        print("\n2. Testing mcp.tools.available...")
        await self.websocket.send(json.dumps({
            "type": "mcp.tools.available"
        }))
        
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
            data = json.loads(response)
            if data.get("type") == "mcp.tools.available.response":
                tools = data.get("tools", [])
                print(f"   ✓ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"     - {tool['name']}: {tool['description']}")
                self.results.append(("List tools", True, f"{len(tools)} tools"))
                return len(tools) > 0
            else:
                print(f"   ✗ Unexpected response: {data.get('type')}")
                self.results.append(("List tools", False, f"Unexpected: {data.get('type')}"))
                return False
        except Exception as e:
            print(f"   ✗ Error: {e}")
            self.results.append(("List tools", False, str(e)))
            return False
            
    async def test_execute_tool(self, tool_name, args, description):
        """Test executing a specific tool."""
        print(f"\n3. Testing tool execution: {description}...")
        await self.websocket.send(json.dumps({
            "type": "mcp.tool.execute",
            "tool_name": tool_name,
            "arguments": args
        }))
        
        try:
            # Wait for response with longer timeout for Docker container spawn
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            data = json.loads(response)
            
            if data.get("type") == "mcp.tool.execute.response":
                result = data.get("result", "")
                print(f"   ✓ Tool executed successfully: {result}")
                self.results.append((description, True, result))
                return True
            elif data.get("type") == "error":
                error = data.get("error", {}).get("message", "Unknown error")
                print(f"   ✗ Error: {error}")
                self.results.append((description, False, error))
                return False
            else:
                print(f"   ✗ Unexpected response: {data.get('type')}")
                self.results.append((description, False, f"Unexpected: {data.get('type')}"))
                return False
        except asyncio.TimeoutError:
            print(f"   ✗ Timeout waiting for tool execution")
            self.results.append((description, False, "Timeout"))
            return False
        except Exception as e:
            print(f"   ✗ Error: {e}")
            self.results.append((description, False, str(e)))
            return False
            
    async def test_docker_connectivity(self):
        """Test if Docker is accessible from unmute-backend."""
        print("\n4. Testing Docker connectivity...")
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "exec", "unmute-backend", "docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("   ✓ Docker is accessible from unmute-backend")
                self.results.append(("Docker connectivity", True, "Accessible"))
                return True
            else:
                print(f"   ✗ Docker command failed: {result.stderr}")
                self.results.append(("Docker connectivity", False, result.stderr))
                return False
        except Exception as e:
            print(f"   ✗ Error: {e}")
            self.results.append(("Docker connectivity", False, str(e)))
            return False
            
    async def test_mcp_image_exists(self):
        """Test if MCP time image exists."""
        print("\n5. Testing MCP time image availability...")
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}", "mcp/time"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "mcp/time" in result.stdout:
                print("   ✓ MCP time image exists")
                self.results.append(("MCP image", True, "Image exists"))
                return True
            else:
                print("   ✗ MCP time image not found")
                self.results.append(("MCP image", False, "Image not found"))
                return False
        except Exception as e:
            print(f"   ✗ Error: {e}")
            self.results.append(("MCP image", False, str(e)))
            return False
            
    async def run_all_tests(self):
        """Run all MCP tests."""
        print("=" * 60)
        print("MCP Integration Test Suite")
        print("=" * 60)
        
        try:
            # Connect and setup
            await self.connect_and_setup()
            
            # Run tests
            await self.test_list_servers()
            await self.test_list_tools()
            
            # Test Docker before tool execution
            await self.test_docker_connectivity()
            await self.test_mcp_image_exists()
            
            # Execute tools
            await self.test_execute_tool(
                "time.get_current_time",
                {},
                "Get current time (default timezone)"
            )
            
            await self.test_execute_tool(
                "time.get_current_time",
                {"timezone": "America/New_York"},
                "Get New York time"
            )
            
            await self.test_execute_tool(
                "time.get_current_time",
                {"timezone": "Asia/Tokyo"},
                "Get Tokyo time"
            )
            
        except Exception as e:
            print(f"\nTest suite error: {e}")
            self.results.append(("Test suite", False, str(e)))
        finally:
            if hasattr(self, 'websocket'):
                await self.websocket.close()
                
        # Print summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        for test_name, success, details in self.results:
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status} | {test_name:<25} | {details}")
            
        print("-" * 60)
        print(f"Total: {passed}/{total} tests passed")
        
        return passed == total

async def main():
    tester = MCPTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())