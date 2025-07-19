#!/bin/bash
# Test MCP server directly with uvx

echo "🧪 Testing MCP server time directly with uvx"
echo "============================================"

# Create a test script to interact with the MCP server
cat > /tmp/test-mcp-time.py << 'EOF'
import json
import sys
import time

# Send initialize request
init_request = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0.0"}
    },
    "id": 1
}
print(json.dumps(init_request))
sys.stdout.flush()

# Wait for response
response = sys.stdin.readline()
print(f"Init response: {response}", file=sys.stderr)

# Send initialized notification
init_notification = {
    "jsonrpc": "2.0",
    "method": "notifications/initialized"
}
print(json.dumps(init_notification))
sys.stdout.flush()

# Small delay
time.sleep(0.1)

# Send tool call
tool_request = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "get_current_time",
        "arguments": {"timezone": "Europe/London"}
    },
    "id": 2
}
print(json.dumps(tool_request))
sys.stdout.flush()

# Read tool response
response = sys.stdin.readline()
print(f"Tool response: {response}", file=sys.stderr)
EOF

echo "Running MCP server test..."
python3 /tmp/test-mcp-time.py | docker exec -i unmute-backend uvx mcp-server-time --local-timezone Europe/London 2>&1