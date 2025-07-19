#!/bin/bash
# Monitor backend logs during test
echo "📋 Monitoring backend logs for MCP activity..."
docker logs -f unmute-backend 2>&1 | grep -E "(MCP|TOOL_CALL|Executing|time\.get_current_time|Invalid request|stderr|Speaking|speech)" --line-buffered