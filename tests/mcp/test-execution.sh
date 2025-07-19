#!/bin/bash
echo "🚀 Testing MCP Tool Execution"
echo "============================"
echo ""

# Monitor backend logs for tool execution
echo "Monitoring recent tool executions..."
docker logs unmute-backend 2>&1 | grep -E "(TOOL_CALL|Executing MCP tool|Raw tool response|datetime.*2025)" | tail -20 | while read -r line; do
    if [[ $line == *"TOOL_CALL"* ]]; then
        echo "🎯 $line"
    elif [[ $line == *"Executing MCP tool"* ]]; then
        echo "⚙️  $line"
    elif [[ $line == *"Raw tool response"* ]]; then
        echo "✅ $line"
    elif [[ $line == *"datetime"* ]]; then
        echo "📅 $line"
    else
        echo "   $line"
    fi
done

echo ""
echo "🔍 Summary of successful executions:"
docker logs unmute-backend 2>&1 | grep -B1 "datetime.*2025-07-15" | grep -E "(Raw tool response|datetime)" | tail -5