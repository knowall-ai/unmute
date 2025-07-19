#!/bin/bash
echo "🎤 Live MCP Test"
echo "================"
echo ""
echo "1. Open http://localhost:3000 in your browser"
echo "2. Click the Play button (green circle)"
echo "3. Wait for initialization"
echo "4. Say: 'What time is it?'"
echo ""
echo "📊 Monitoring for MCP activity..."
echo "================================"
docker logs -f unmute-backend 2>&1 | grep -E "(TOOL_CALL|Executing MCP tool|Raw tool response|datetime.*2025-07-15)" --line-buffered | while read -r line; do
    timestamp=$(date '+%H:%M:%S')
    if [[ $line == *"TOOL_CALL"* ]]; then
        echo "[$timestamp] 🎯 LLM initiating tool call"
    elif [[ $line == *"Executing MCP tool"* ]]; then
        echo "[$timestamp] ⚙️  Executing: $(echo "$line" | grep -o "time\.[^ ]*")"
    elif [[ $line == *"Raw tool response"* ]]; then
        echo "[$timestamp] ✅ SUCCESS! Got time response"
        echo "$line" | grep -o '"datetime":"[^"]*"' | sed 's/"datetime":"/[$timestamp] 📅 Time: /'
    fi
done