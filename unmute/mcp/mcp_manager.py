"""MCP (Model Context Protocol) Manager for Unmute.

This module handles the integration of MCP servers with Unmute,
allowing voice-controlled access to external tools and data sources.
"""
import asyncio
import json
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import aiohttp
from mcp import ClientSession, StdioServerParameters, stdio_client, Tool
from mcp.types import TextContent

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    transport: str = "stdio"  # "stdio" or "sse"
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


class MCPManager:
    """Manages MCP server connections and tool executions."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the MCP Manager.
        
        Args:
            config_path: Path to .mcp.json config file. Defaults to project root.
        """
        self.config_path = config_path or Path.cwd() / ".mcp.json"
        self.servers: Dict[str, MCPServerConfig] = {}
        self.clients: Dict[str, ClientSession] = {}
        self.available_tools: Dict[str, Tool] = {}
        self._running = False
        
    async def initialize(self) -> None:
        """Initialize the MCP manager by loading config and starting servers."""
        await self.load_config()
        await self.start_servers()
        self._running = True
        
    async def shutdown(self) -> None:
        """Shutdown all MCP servers and cleanup."""
        self._running = False
        for client in self.clients.values():
            await client.close()
        self.clients.clear()
        self.available_tools.clear()
        
    async def load_config(self) -> None:
        """Load MCP server configuration from .mcp.json file."""
        if not os.path.exists(self.config_path):
            logger.warning(f"MCP config file not found at {self.config_path}")
            return
            
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            mcp_servers = config.get('mcpServers', {})
            for name, server_config in mcp_servers.items():
                # Expand environment variables in config
                command = self._expand_env_vars(server_config.get('command', ''))
                args = [self._expand_env_vars(arg) for arg in server_config.get('args', [])]
                env = {k: self._expand_env_vars(v) for k, v in server_config.get('env', {}).items()}
                
                # Determine transport type
                transport = server_config.get('type', 'stdio')
                url = self._expand_env_vars(server_config.get('url', '')) if 'url' in server_config else None
                headers = {k: self._expand_env_vars(v) for k, v in server_config.get('headers', {}).items()} if 'headers' in server_config else None
                
                self.servers[name] = MCPServerConfig(
                    name=name,
                    command=command,
                    args=args,
                    env=env,
                    transport=transport,
                    url=url,
                    headers=headers
                )
                
            logger.info(f"Loaded {len(self.servers)} MCP server configurations")
            
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            
    def _expand_env_vars(self, value: str) -> str:
        """Expand environment variables in string values.
        
        Supports ${VAR} and ${VAR:-default} syntax.
        """
        import re
        
        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(3) if match.group(3) else ''
            return os.environ.get(var_name, default_value)
            
        # Match ${VAR} or ${VAR:-default}
        pattern = r'\$\{([^}:]+)(:-([^}]*))?\}'
        return re.sub(pattern, replacer, value)
        
    async def start_servers(self) -> None:
        """Start all configured MCP servers."""
        for name, config in self.servers.items():
            try:
                client = await self._start_server(config)
                self.clients[name] = client
                
                # Get available tools from the server
                tools_response = await client.list_tools()
                for tool in tools_response.tools:
                    # Prefix tool name with server name to avoid conflicts
                    prefixed_name = f"{name}.{tool.name}"
                    self.available_tools[prefixed_name] = tool
                    
                logger.info(f"Started MCP server '{name}' with {len(tools_response.tools)} tools")
                
            except Exception as e:
                logger.error(f"Failed to start MCP server '{name}': {e}")
                
    async def _start_server(self, config: MCPServerConfig) -> ClientSession:
        """Start a single MCP server based on its configuration."""
        if config.transport == "stdio":
            # Create stdio server parameters
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env={**os.environ, **config.env}  # Merge with current env
            )
            # Start the stdio client
            read_stream, write_stream = await stdio_client(server_params).__aenter__()
            session = ClientSession(read_stream, write_stream)
            
            # Initialize the session
            init_result = await session.initialize()
            logger.info(f"Initialized MCP server '{config.name}': {init_result}")
            
            return session
                
        elif config.transport == "sse":
            # SSE transport would use HTTP/SSE for communication
            raise NotImplementedError(f"SSE transport not implemented yet for server '{config.name}'")
                
        else:
            raise ValueError(f"Unknown transport type '{config.transport}' for server '{config.name}'")
            
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools from all servers.
        
        Returns:
            List of tool descriptions suitable for LLM context.
        """
        tools = []
        for tool_name, tool in self.available_tools.items():
            tools.append({
                "name": tool_name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            })
        return tools
        
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result.
        
        Args:
            tool_name: Name of the tool (format: "server.tool")
            arguments: Tool arguments
            
        Returns:
            Tool execution result as string
        """
        if tool_name not in self.available_tools:
            raise ValueError(f"Tool '{tool_name}' not found")
            
        # Extract server name from tool name
        server_name = tool_name.split('.')[0]
        actual_tool_name = '.'.join(tool_name.split('.')[1:])
        
        if server_name not in self.clients:
            raise ValueError(f"Server '{server_name}' not connected")
            
        client = self.clients[server_name]
        
        try:
            # Execute the tool
            result = await client.call_tool(actual_tool_name, arguments)
            
            # Extract text content from result
            if result.content:
                text_parts = []
                for content in result.content:
                    if isinstance(content, TextContent):
                        text_parts.append(content.text)
                return ' '.join(text_parts)
            else:
                return "Tool executed successfully with no output"
                
        except Exception as e:
            logger.error(f"Failed to execute tool '{tool_name}': {e}")
            raise
            
    def get_tools_for_prompt(self) -> str:
        """Get a formatted string of available tools for the LLM prompt.
        
        Returns:
            Formatted string describing available MCP tools.
        """
        if not self.available_tools:
            return ""
            
        tools_desc = ["Available MCP Tools:"]
        for tool_name, tool in self.available_tools.items():
            tools_desc.append(f"- {tool_name}: {tool.description}")
            
        return '\n'.join(tools_desc)