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
2. **`.mcp.config.local`** - Local overrides (ignored by git)

The local config file allows you to customize settings like timezone without modifying tracked files.

### Base Configuration (.mcp.json)

```json
{
  "mcpServers": {
    "datetime": {
      "command": "python",
      "args": ["-m", "unmute.mcp.servers.datetime"],
      "env": {}
    }
  }
}
```

### Local Configuration (.mcp.config.local)

Copy `.mcp.config.local.example` to `.mcp.config.local` and customize:

```json
{
  "mcpServers": {
    "datetime": {
      "env": {
        "UNMUTE_TIMEZONE": "America/New_York"
      }
    }
  }
}
```

Local configuration is merged with base configuration, so you only need to specify the values you want to override.

## Creating MCP Servers

To create a new MCP server for Unmute:

1. Create a new Python module in `unmute/mcp/servers/`
2. Implement the MCP server protocol using the `mcp` library
3. Define tools with clear descriptions and input schemas
4. Add the server to `.mcp.json`

See `unmute/mcp/servers/datetime.py` for an example implementation.

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

1. **MCPManager** (`mcp_manager.py`) - Manages MCP server connections and tool execution
2. **WebSocket handlers** - Process MCP-related messages
3. **LLM integration** - Injects available tools into the system prompt
4. **Tool execution** - Intercepts LLM responses to execute tools

## Future Enhancements

- Support for more MCP transport types (HTTP, WebSocket)
- Dynamic server discovery and hot-reloading
- Tool result caching
- Enhanced error handling and recovery