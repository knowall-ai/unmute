# MCP (Model Context Protocol) Integration for Unmute

This module provides Model Context Protocol (MCP) support for Unmute, enabling voice-controlled access to external tools and data sources through MCP servers.

## Overview

The MCP integration allows Unmute to:
- Connect to MCP servers that provide various tools and capabilities
- Make these tools available to the LLM during conversations
- Execute tools based on voice commands
- Return tool results as natural speech

## Configuration

MCP servers are configured using JSON files in the project root:

1. **`.mcp.json`** - Base configuration (committed to git)
2. **`.mcp.local.json`** - Local overrides (ignored by git)

The local config file allows you to customize settings like timezone without modifying tracked files.

### Base Configuration (.mcp.json)

```json
{
  "mcpServers": {
    "time": {
      "command": "python3",
      "args": ["-m", "mcp_server_time", "--local-timezone", "Europe/London"]
    }
  }
}
```

### Local Configuration (.mcp.local.json)

Copy `.mcp.example.json` to `.mcp.local.json` and customize:

```json
{
  "mcpServers": {
    "time": {
      "args": ["-m", "mcp_server_time", "--local-timezone", "America/New_York"]
    }
  }
}
```

Local configuration is deep-merged with base configuration, so you only need to specify the values you want to override.

## Using MCP Servers

Unmute can use any MCP server that follows the Model Context Protocol. Popular servers include:

1. **Official MCP Servers** from https://github.com/modelcontextprotocol/servers
   - `mcp-server-time` - Time and date tools with timezone support
   - `@modelcontextprotocol/server-filesystem` - File system access
   - `@modelcontextprotocol/server-github` - GitHub integration
   - And many more...

2. **Custom MCP Servers** - You can create your own following the MCP specification

To add a new server, simply add it to `.mcp.json` with the appropriate command and arguments. Unmute uses `uvx` to run Python-based MCP servers, ensuring they're executed in isolated environments.

## Usage

Once configured, MCP tools are automatically available during voice conversations. Users can ask questions that trigger tool usage, such as:

- "What time is it in Tokyo?"
- "What's today's date?"
- "What day of the week is it?"

The LLM will automatically invoke the appropriate tools and speak the results.

## WebSocket API

The following WebSocket messages are available for MCP management:

### Client → Server
- `mcp.servers.list` - List all configured MCP servers
- `mcp.servers.status` - Get status of a specific server
- `mcp.tools.available` - List all available tools
- `mcp.tool.execute` - Execute a specific tool

### Server → Client
- `mcp.servers.list.response` - List of servers with status
- `mcp.servers.status.response` - Status of requested server
- `mcp.tools.available.response` - List of available tools
- `mcp.tool.execute.response` - Tool execution result

## Architecture

The MCP integration consists of:

1. **MCPManager** (`mcp_manager.py`) - Manages MCP server lifecycle and tool execution
2. **Tool Discovery** - Automatically discovers tools from MCP servers on startup
3. **LLM Integration** - Tools are injected into the system prompt for the LLM
4. **Tool Execution** - Intercepts `TOOL_CALL:` patterns in LLM responses
5. **Result Interpretation** - Tool results are sent back to the LLM for natural language interpretation

### How It Works

1. When Unmute starts, it reads MCP configurations and spawns servers
2. Each server is queried for available tools via JSON-RPC
3. Tools are registered and made available to the LLM
4. During conversation, when the LLM outputs `TOOL_CALL: tool_name(args)`, Unmute:
   - Parses the tool call
   - Executes it via the appropriate MCP server
   - Sends the result back to the LLM
   - The LLM interprets the result and speaks it naturally

## Troubleshooting

### Agent doesn't respond to time questions
- Check that MCP tools are discovered: Look for "Available MCP tools" in backend logs
- Verify the time server is running: `docker logs unmute-backend-1 | grep mcp`
- Ensure the LLM model supports tool calls (llama3.2:3b or higher)

### Tool execution fails
- Check for "Tool result:" entries in logs
- Verify MCP server permissions and Python environment
- Ensure `uvx` is available in the container

## Future Enhancements

- Support for more MCP transport types (HTTP, WebSocket)
- Persistent MCP server processes (current implementation spawns per-call)
- Tool result caching for frequently used tools
- Enhanced error handling with fallback responses
- Support for streaming tool responses