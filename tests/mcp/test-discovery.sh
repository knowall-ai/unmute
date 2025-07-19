#!/bin/bash
echo "🔍 Testing MCP Tool Discovery"
echo "============================"

# Test tool discovery via JSON-RPC
cat > /tmp/test-discovery.py << 'EOF'
import json
import sys

# Send initialize
print(json.dumps({
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0.0"}
    },
    "id": 1
}))
sys.stdout.flush()

# Read response
init_resp = sys.stdin.readline()
print(f"Init response: {init_resp.strip()}", file=sys.stderr)

# Send initialized notification
print(json.dumps({
    "jsonrpc": "2.0",
    "method": "notifications/initialized"
}))
sys.stdout.flush()

# List tools
print(json.dumps({
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 2
}))
sys.stdout.flush()

# Read tools response
tools_resp = sys.stdin.readline()
tools_data = json.loads(tools_resp)

if "result" in tools_data and "tools" in tools_data["result"]:
    print(f"\n✅ Discovered {len(tools_data['result']['tools'])} tools:", file=sys.stderr)
    for tool in tools_data["result"]["tools"]:
        print(f"   - {tool['name']}: {tool.get('description', 'No description')}", file=sys.stderr)
else:
    print(f"❌ Failed to discover tools: {tools_resp}", file=sys.stderr)
EOF

python3 /tmp/test-discovery.py | docker exec -i unmute-backend uvx mcp-server-time --local-timezone Europe/London 2>&1 | grep -E "(Init response|Discovered|tools)"