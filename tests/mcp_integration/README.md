# MCP Integration Tests

This directory contains tests for the Model Context Protocol (MCP) integration in Unmute.

## Test Files

- `test_mcp_integration.py` - Comprehensive test suite for MCP functionality
- `reset_conversation.py` - Utility to reset the backend conversation state

## Running Tests

1. Ensure the Unmute backend is running:
   ```bash
   cd /mnt/raid1/GitHub/black-panther/ai-stack
   docker compose up -d unmute-backend unmute-stt unmute-tts ollama
   ```

2. Run the integration tests:
   ```bash
   python tests/mcp_integration/test_mcp_integration.py
   ```

3. For manual testing through the voice interface:
   - Open http://localhost:3000
   - Select a voice
   - Ask questions like "What time is it?" or "What day is it today?"

## Expected Behavior

When MCP is working correctly:
1. The LLM should generate `TOOL_CALL: datetime.get_current_time()` for time questions
2. The backend should execute the tool and get the actual time
3. The response should include the real current time/day

## Monitoring

Monitor MCP activity in real-time:
```bash
docker logs -f unmute-backend | grep -E 'TOOL_CALL|MCP|Tool result'
```