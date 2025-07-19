#!/bin/bash
echo "🎤 Quick MCP Test"
echo "================"
echo ""
echo "1. Go to http://localhost:3000"
echo "2. Click Play and ask 'What time is it?'"
echo ""
echo "Monitoring for tool execution..."
docker logs -f unmute-backend 2>&1 | grep -E "(TOOL_CALL|Executing MCP|Tool result:|ERROR|datetime.*2025-07-15.*0[78]:[45])" --line-buffered | while read line; do
    timestamp=$(date '+%H:%M:%S')
    if [[ $line =~ "TOOL_CALL" ]]; then
        echo "[$timestamp] 🎯 Tool call initiated"
    elif [[ $line =~ "Executing MCP tool" ]]; then
        echo "[$timestamp] ⚙️  Executing tool..."
    elif [[ $line =~ "Tool result:" ]]; then
        echo "[$timestamp] ✅ Got tool result"
    elif [[ $line =~ "datetime.*2025-07-15" ]]; then
        time=$(echo "$line" | grep -o "[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}")
        echo "[$timestamp] 🕐 Time: $time"
    elif [[ $line =~ "ERROR" ]]; then
        echo "[$timestamp] ❌ ERROR: ${line##*ERROR - }"
    fi
done