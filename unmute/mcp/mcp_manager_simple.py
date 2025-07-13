"""Simplified MCP Manager for Unmute without direct MCP SDK dependency.

This module provides MCP-like functionality for demonstration purposes.
"""
import asyncio
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    transport: str = "stdio"
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


@dataclass 
class Tool:
    """Represents an MCP tool."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MCPManager:
    """Simplified MCP Manager that provides tool functionality."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the MCP Manager."""
        self.config_path = config_path or Path.cwd() / ".mcp.json"
        self.servers: Dict[str, MCPServerConfig] = {}
        self.available_tools: Dict[str, Tool] = {}
        self._running = False
        
        # For demo purposes, we'll hardcode the datetime tools
        self._register_demo_tools()
        
    def _register_demo_tools(self):
        """Register demo datetime tools."""
        self.available_tools = {
            "datetime.get_current_time": Tool(
                name="get_current_time",
                description="Get the current time, optionally for a specific location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location or timezone (e.g., 'Tokyo', 'America/New_York')"
                        }
                    }
                }
            ),
            "datetime.get_date": Tool(
                name="get_date",
                description="Get the current date",
                inputSchema={"type": "object", "properties": {}}
            ),
            "datetime.get_day_of_week": Tool(
                name="get_day_of_week", 
                description="Get the current day of the week",
                inputSchema={"type": "object", "properties": {}}
            )
        }
        
    async def initialize(self) -> None:
        """Initialize the MCP manager."""
        await self.load_config()
        self._running = True
        logger.info(f"MCP Manager initialized with {len(self.available_tools)} demo tools")
        
    async def shutdown(self) -> None:
        """Shutdown the MCP manager."""
        self._running = False
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
                self.servers[name] = MCPServerConfig(
                    name=name,
                    command=server_config.get('command', ''),
                    args=server_config.get('args', []),
                    env=server_config.get('env', {}),
                    transport=server_config.get('type', 'stdio')
                )
                
            logger.info(f"Loaded {len(self.servers)} MCP server configurations")
            
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools."""
        tools = []
        for tool_name, tool in self.available_tools.items():
            tools.append({
                "name": tool_name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            })
        return tools
        
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result."""
        # For demo purposes, import and call the datetime functions directly
        if tool_name == "datetime.get_current_time":
            from unmute.mcp.servers.datetime import get_current_time
            return await get_current_time(arguments.get("location"))
        elif tool_name == "datetime.get_date":
            from unmute.mcp.servers.datetime import get_date
            return await get_date()
        elif tool_name == "datetime.get_day_of_week":
            from unmute.mcp.servers.datetime import get_day_of_week
            return await get_day_of_week()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
            
    def get_tools_for_prompt(self) -> str:
        """Get a formatted string of available tools for the LLM prompt."""
        if not self.available_tools:
            return ""
            
        tools_desc = ["Available MCP Tools:"]
        for tool_name, tool in self.available_tools.items():
            tools_desc.append(f"- {tool_name}: {tool.description}")
            
        return '\n'.join(tools_desc)