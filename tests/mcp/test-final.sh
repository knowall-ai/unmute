#!/bin/bash
echo "🎯 Final MCP Time Test"
echo "===================="
echo ""
echo "Instructions:"
echo "1. Open http://localhost:3000"
echo "2. Click Play button (green circle)"
echo "3. Wait for 'Loading voices...' to disappear"
echo "4. Say: 'What time is it?'"
echo ""
echo "Expected: The assistant should say the full time, not just 'Europe/London'"
echo ""
echo "📊 Live monitoring..."
echo "===================="

docker logs -f unmute-backend 2>&1 | while read line; do
    if [[ $line =~ "TOOL_CALL:" ]]; then
        echo "[$(date +%H:%M:%S)] 🎯 Assistant initiated tool call"
    elif [[ $line =~ "Executing MCP tool: time.get_current_time" ]]; then
        echo "[$(date +%H:%M:%S)] ⚙️  Executing time tool..."
    elif [[ $line =~ "Tool result:.*datetime.*2025-07-15" ]]; then
        echo "[$(date +%H:%M:%S)] ✅ Got time data: $(echo "$line" | grep -o '"datetime":"[^"]*"')"
    elif [[ $line =~ "chat_history.*Tool result from time.get_current_time" ]]; then
        echo "[$(date +%H:%M:%S)] 📝 Added tool result to chat history for LLM interpretation"
    elif [[ $line =~ "Sending first word to TTS:" ]] && [[ $line =~ "time" ]]; then
        echo "[$(date +%H:%M:%S)] 🗣️  Speaking: $(echo "$line" | cut -d':' -f4-)"
    elif [[ $line =~ "ERROR.*vllm_stream" ]]; then
        echo "[$(date +%H:%M:%S)] ❌ OLD ERROR: vllm_stream (should be fixed now)"
    elif [[ $line =~ "ERROR.*Failed to execute tool" ]]; then
        echo "[$(date +%H:%M:%S)] ❌ ERROR: Tool execution failed"
    fi
done