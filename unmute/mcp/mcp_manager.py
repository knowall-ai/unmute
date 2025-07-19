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
        self.local_config_path = Path.cwd() / ".mcp.local.json"
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
        """Load MCP server configuration from .mcp.json and optional .mcp.config.local file."""
        config = {}
        
        # Load base configuration
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded base config from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load base MCP config: {e}")
                return
        else:
            logger.warning(f"MCP config file not found at {self.config_path}")
            
        # Load local overrides if they exist
        if os.path.exists(self.local_config_path):
            try:
                with open(self.local_config_path, 'r') as f:
                    local_config = json.load(f)
                # Deep merge local config into base config
                self._merge_configs(config, local_config)
                logger.info(f"Loaded local config from {self.local_config_path}")
            except Exception as e:
                logger.warning(f"Failed to load local MCP config: {e}")
                
        # Process merged configuration
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
        """Start all configured MCP servers and discover their tools."""
        logger.info("Starting MCP servers...")
        for name, config in self.servers.items():
            try:
                # For stdio servers, we need to spawn them temporarily to get tool info
                if config.transport == "stdio":
                    await self._discover_stdio_server_tools(name, config)
                else:
                    client = await self._start_server(config)
                    if client:
                        self.clients[name] = client
                        
                        # Get available tools from the server
                        tools_response = await client.list_tools()
                        for tool in tools_response.tools:
                            # Prefix tool name with server name to avoid conflicts
                            prefixed_name = f"{name}.{tool.name}"
                            self.available_tools[prefixed_name] = tool
                            
                        logger.info(f"Started MCP server '{name}' with {len(tools_response.tools)} tools")
                
            except Exception as e:
                logger.error(f"Failed to configure MCP server '{name}': {e}")
                
    async def _discover_stdio_server_tools(self, name: str, config: MCPServerConfig) -> None:
        """Discover tools from a stdio server by spawning it temporarily."""
        logger.info(f"Discovering tools from MCP server '{name}'...")
        
        # Dynamic tool discovery using subprocess approach
        try:
            # Start the MCP server process
            cmd = [config.command] + config.args
            env = {**os.environ, **config.env}
            
            logger.debug(f"Starting MCP server for discovery: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            try:
                # Send initialize request
                init_request = json.dumps({
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "unmute", "version": "1.0.0"}
                    },
                    "id": 1
                }) + '\n'
                
                process.stdin.write(init_request.encode())
                await process.stdin.drain()
                
                # Read initialization response
                init_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=15.0)
                init_response = json.loads(init_response_line.decode())
                
                if 'error' in init_response:
                    raise Exception(f"Initialization failed: {init_response['error']}")
                
                # Send initialized notification
                init_notification = json.dumps({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }) + '\n'
                
                process.stdin.write(init_notification.encode())
                await process.stdin.drain()
                
                # Request tool list
                list_tools_request = json.dumps({
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": 2
                }) + '\n'
                
                process.stdin.write(list_tools_request.encode())
                await process.stdin.drain()
                
                # Read tools response
                tools_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=15.0)
                tools_response = json.loads(tools_response_line.decode())
                
                if 'error' in tools_response:
                    raise Exception(f"Failed to list tools: {tools_response['error']}")
                
                # Parse and register tools
                tools = tools_response.get('result', {}).get('tools', [])
                
                # Import Tool class to create tool objects
                from mcp import Tool
                
                for tool_data in tools:
                    tool = Tool(
                        name=tool_data['name'],
                        description=tool_data.get('description', ''),
                        inputSchema=tool_data.get('inputSchema', {})
                    )
                    prefixed_name = f"{name}.{tool.name}"
                    self.available_tools[prefixed_name] = tool
                    logger.debug(f"Registered tool: {prefixed_name} - {tool.description}")
                
                logger.info(f"Discovered {len(tools)} tools from MCP server '{name}'")
                
            finally:
                # Clean up the process
                process.stdin.close()
                process.terminate()
                await process.wait()
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout discovering tools from MCP server '{name}' - server spawn may have failed")
            logger.warning(f"MCP server '{name}' will not be available")
        except Exception as e:
            logger.error(f"Failed to discover tools from MCP server '{name}': {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # For now, continue without this server's tools
            logger.warning(f"MCP server '{name}' will not be available")
                
    async def _start_server(self, config: MCPServerConfig) -> ClientSession:
        """Start a single MCP server based on its configuration."""
        if config.transport == "stdio":
            # For now, return None as we'll spawn servers on-demand
            # The stdio_client needs to be used in a context manager
            # which doesn't fit well with our persistent client model
            logger.info(f"MCP server '{config.name}' configured for on-demand spawning")
            return None
                
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
        
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not configured")
            
        config = self.servers[server_name]
        
        # For stdio servers, spawn on demand
        if config.transport == "stdio":
            try:
                # Use direct subprocess approach with persistent process
                logger.info(f"Executing MCP tool via subprocess: {config.command} {' '.join(config.args)}")
                
                import subprocess
                
                # Run the MCP server
                cmd = [config.command] + config.args
                env = {**os.environ, **config.env}
                
                logger.debug(f"Running command: {' '.join(cmd)}")
                
                # Start the process
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
                
                # Send initialize request and wait for response
                init_request = json.dumps({
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "unmute", "version": "1.0.0"}
                    },
                    "id": 1
                }) + '\n'
                
                process.stdin.write(init_request.encode())
                await process.stdin.drain()
                
                # Read initialization response
                try:
                    init_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=15.0)
                    logger.info(f"Raw init response: {init_response_line.decode().strip()}")
                    init_response = json.loads(init_response_line.decode())
                    logger.info(f"Parsed init response: {init_response}")
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for initialization response")
                    raise Exception("MCP server initialization timeout")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse init response: {e}")
                    logger.error(f"Raw response was: {init_response_line.decode()}")
                    raise
                
                if 'error' in init_response:
                    raise Exception(f"Initialization failed: {init_response['error']}")
                
                # Send initialized notification to complete the handshake
                init_notification = json.dumps({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }) + '\n'
                
                process.stdin.write(init_notification.encode())
                await process.stdin.drain()
                
                # Small delay to ensure server processes the notification
                await asyncio.sleep(0.1)
                
                # Now send the tool call request
                # Handle missing timezone for get_current_time
                tool_args = arguments or {}
                if actual_tool_name == "get_current_time" and "timezone" not in tool_args:
                    # Use the configured timezone as default
                    tool_args["timezone"] = "Europe/London"
                    logger.info("No timezone provided, using default: Europe/London")
                
                tool_request = json.dumps({
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": actual_tool_name,
                        "arguments": tool_args
                    },
                    "id": 2
                }) + '\n'
                
                process.stdin.write(tool_request.encode())
                await process.stdin.drain()
                
                # Read tool response
                try:
                    tool_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
                    logger.info(f"Raw tool response: {tool_response_line.decode().strip()}")
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for tool response after 10 seconds")
                    # Try to get any stderr output
                    try:
                        stderr = await asyncio.wait_for(process.stderr.read(), timeout=0.5)
                        if stderr:
                            logger.error(f"MCP server stderr during timeout: {stderr.decode()}")
                    except asyncio.TimeoutError:
                        pass
                    raise Exception("MCP tool execution timeout")
                
                # Read any stderr output
                stderr_task = asyncio.create_task(process.stderr.read())
                
                # Clean up the process
                process.stdin.close()
                await process.wait()
                
                # Get stderr if any
                try:
                    stderr = await asyncio.wait_for(stderr_task, timeout=0.5)
                    if stderr:
                        logger.warning(f"MCP server stderr: {stderr.decode()}")
                except asyncio.TimeoutError:
                    pass
                
                # Parse tool response
                tool_response = json.loads(tool_response_line.decode())
                logger.debug(f"Tool response: {tool_response}")
                
                if 'error' in tool_response:
                    error_msg = tool_response['error'].get('message', 'Unknown error')
                    raise Exception(f"MCP tool error: {error_msg}")
                
                result = tool_response.get('result', {})
                content = result.get('content', [])
                
                # Extract text from content
                text_parts = []
                for item in content:
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                
                return ' '.join(text_parts) if text_parts else "No output from tool"
                        
            except asyncio.TimeoutError:
                logger.error(f"Tool execution timed out for '{tool_name}'")
                raise Exception("Tool execution timed out")
            except Exception as e:
                logger.error(f"Failed to execute tool '{tool_name}': {e}")
                raise
        else:
            # For persistent clients
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
            Formatted string describing available MCP tools with usage guidance.
        """
        if not self.available_tools:
            return ""
            
        tools_desc = [
            "You have access to the following tools to help answer user questions:",
            ""
        ]
        
        for tool_name, tool in self.available_tools.items():
            # Start with tool name and description
            tool_info = [f"**{tool_name}**: {tool.description}"]
            
            # Add parameter information from the input schema
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                schema = tool.inputSchema
                if isinstance(schema, dict) and schema.get('properties'):
                    params_list = []
                    for param_name, param_info in schema['properties'].items():
                        param_desc = param_info.get('description', 'No description')
                        param_type = param_info.get('type', 'any')
                        required = param_name in schema.get('required', [])
                        req_str = " (required)" if required else " (optional)"
                        params_list.append(f"{param_name}: {param_desc}{req_str}")
                    
                    if params_list:
                        tool_info.append(f"  Usage: TOOL_CALL: {tool_name}({', '.join(params_list)})")
                    else:
                        tool_info.append(f"  Usage: TOOL_CALL: {tool_name}()")
                else:
                    tool_info.append(f"  Usage: TOOL_CALL: {tool_name}()")
            else:
                tool_info.append(f"  Usage: TOOL_CALL: {tool_name}()")
            
            tools_desc.extend(tool_info)
            tools_desc.append("")  # Add blank line between tools
            
        # Add general usage instructions
        tools_desc.extend([
            "TOOL USAGE INSTRUCTIONS:",
            "- Only use tools when the user specifically asks for information that tools can provide",
            "- DO NOT proactively use tools unless the user asks a question that requires them",
            "- When asked about time, weather, or web content, use the appropriate tool",
            "- Use the EXACT format: TOOL_CALL: tool_name(parameter=\"value\") or TOOL_CALL: tool_name() for tools with no parameters", 
            "- The tool call MUST be on its own line, not mixed with other text",
            "- Example: If user asks 'What time is it?', respond with: TOOL_CALL: time.get_current_time(timezone=\"Europe/London\")",
            "- Do not use tools for general conversation or when not explicitly needed",
            "- After using a tool, you will receive the result and should present it naturally in conversation",
            "- Do not mention that you used a tool - just provide the information naturally",
            "- If a tool returns technical data (like JSON), interpret it into human-friendly language"
        ])
            
        return '\n'.join(tools_desc)
        
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge override config into base config."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value