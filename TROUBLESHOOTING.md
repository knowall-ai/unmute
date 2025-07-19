# Unmute MCP Integration Troubleshooting Guide

## Common Issues and Solutions

| Problem | Solution |
|---------|----------|
| LLM responds with "It's..." but doesn't provide actual time when asked "What time is it?" | The LLM is guessing instead of using the MCP tool. Strengthen the tool usage instructions in `mcp_manager.py` to make it clear that tools MUST be used for time queries. |
| Tool executes successfully but interpretation generates 0 words | The chat history for interpretation may end with a system message, which some models don't handle well. Ensure the interpretation history has alternating user/assistant messages. |
| Unmute is extremely slow to respond or doesn't respond at all | Check if Ollama is running on CPU instead of GPU. Run `nvidia-smi` to see if ollama process is using GPU. If not, add `runtime: nvidia` to the Ollama service in docker-compose.yml and recreate the container. |
| Ollama using excessive CPU (400%+) and causing system overload | Ollama container was started without GPU support. Update docker-compose.yml with `runtime: nvidia` and recreate: `docker compose up -d ollama` |
| MCP tools discovered but not showing in available tools | Ensure `update_with_mcp_tools()` is called after MCP manager initialization to add tools to the chatbot's system prompt. |
| "index out of range" error in WebSocket receive_loop | The test script is sending empty audio data. This error occurs when opus_bytes buffer is empty. Use actual audio input or the web interface for testing. |
| Constant STT/VAD interruptions preventing responses | Background noise or system sounds are triggering the voice activity detection. Ensure you're in a quiet environment or adjust VAD sensitivity. |
| MCP tool call detected but not executed | Check that the tool call format exactly matches: `TOOL_CALL: tool_name(parameter="value")` on its own line. |
| Tool result shows raw JSON instead of natural language | The interpretation step is failing. Check logs for "Got interpretation word" messages. Ensure the interpretation LLM is properly initialized. |
| Docker container can't find MCP module | Run commands with `uv run` inside the container, or ensure the virtual environment is activated. |
| Weather MCP server fails with JSON decode error | The weather server might not be compatible with uvx or the package name is incorrect. Check PyPI for the correct package name. |
| MCP server fails with "No such file or directory" | The command (e.g., npx) is not available in the container. Use uvx for Python-based MCP servers or install required tools. |