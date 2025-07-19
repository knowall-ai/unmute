#!/bin/bash
echo "🎤 Voice MCP Test Instructions"
echo "=================================="
echo ""
echo "1. Open http://localhost:3000 in your browser"
echo "2. Click the Play button (green circle)"
echo "3. Wait 10-15 seconds for the agent to initialize"
echo "4. Say: 'What time is it?'"
echo ""
echo "Monitoring backend logs for MCP activity..."
echo ""
docker logs -f unmute-backend 2>&1 | grep -E "(TOOL_CALL|Executing MCP tool|time\.get_current_time|Raw tool response|Tool response|MCP tool error)" --line-buffered