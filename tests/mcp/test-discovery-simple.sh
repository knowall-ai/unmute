#!/bin/bash
echo "🔍 Testing MCP Tool Discovery (Simple)"
echo "====================================="

# Send the commands and capture the full output
(
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}'
sleep 0.1
echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'
sleep 0.1
echo '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}'
sleep 0.1
) | docker exec -i unmute-backend uvx mcp-server-time --local-timezone Europe/London 2>&1 | grep -A20 "tools/list" | head -10

echo -e "\n✅ Tool discovery test complete"