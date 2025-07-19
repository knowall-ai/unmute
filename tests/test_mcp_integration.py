"""Tests for MCP (Model Context Protocol) integration."""
import asyncio
import json
import re
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

import pytest

from unmute.llm.chatbot import Chatbot
from unmute.mcp.mcp_manager import MCPServerConfig, MCPManager


class TestMCPServerConfig:
    """Test MCP server configuration."""
    
    def test_server_config_defaults(self):
        """Test default values for MCPServerConfig."""
        config = MCPServerConfig(name="test", command="python")
        assert config.name == "test"
        assert config.command == "python"
        assert config.args == []
        assert config.env == {}
        assert config.transport == "stdio"
        assert config.url is None
        assert config.headers is None


@pytest.mark.asyncio
class TestMCPServerDiscovery:
    """Test MCP server discovery functionality."""
    
    async def test_discover_servers_from_config(self):
        """Test that MCP servers can be discovered from config file."""
        config_data = {
            "mcpServers": {
                "time": {
                    "command": "docker",
                    "args": ["run", "-i", "--rm", "mcp/time"],
                    "env": {}
                },
                "synthesis": {
                    "command": "python",
                    "args": ["-m", "synthesis_server"],
                    "env": {"API_KEY": "test"}
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            with patch("os.path.exists", return_value=True):
                manager = MCPManager()
                await manager.load_config()
                
                # Check servers were discovered
                assert len(manager.servers) == 2
                assert "time" in manager.servers
                assert "synthesis" in manager.servers
                
                # Check server configurations
                time_server = manager.servers["time"]
                assert time_server.name == "time"
                assert time_server.command == "docker"
                assert time_server.args == ["run", "-i", "--rm", "mcp/time"]
                assert time_server.transport == "stdio"
                
                synthesis_server = manager.servers["synthesis"]
                assert synthesis_server.name == "synthesis"
                assert synthesis_server.command == "python"
                assert synthesis_server.env["API_KEY"] == "test"
    
    async def test_discover_servers_with_local_override(self):
        """Test that local config overrides base config."""
        base_config = {
            "mcpServers": {
                "time": {
                    "command": "docker",
                    "args": ["run", "mcp/time"],
                    "env": {}
                }
            }
        }
        
        local_config = {
            "mcpServers": {
                "time": {
                    "args": ["run", "-i", "--rm", "mcp/time:custom"],
                    "env": {"TZ": "America/New_York"}
                }
            }
        }
        
        with patch("builtins.open") as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=json.dumps(base_config)).return_value,
                mock_open(read_data=json.dumps(local_config)).return_value
            ]
            with patch("os.path.exists", return_value=True):
                manager = MCPManager()
                await manager.load_config()
                
                # Check merged configuration
                time_server = manager.servers["time"]
                assert time_server.command == "docker"  # From base
                assert time_server.args == ["run", "-i", "--rm", "mcp/time:custom"]  # From local
                assert time_server.env["TZ"] == "America/New_York"  # From local
    
    async def test_no_servers_when_config_missing(self):
        """Test graceful handling when config file is missing."""
        with patch("os.path.exists", return_value=False):
            manager = MCPManager()
            await manager.load_config()
            assert len(manager.servers) == 0


@pytest.mark.asyncio
class TestMCPToolRegistration:
    """Test MCP tool registration from servers."""
    
    async def test_tools_registered_with_descriptions(self):
        """Test that tools are properly registered with their descriptions from the server."""
        # Mock the MCP Tool class
        from mcp import Tool
        
        mock_tools = [
            Tool(
                name="get_current_time",
                description="Get the current time in a specific timezone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timezone": {"type": "string"}
                    }
                }
            ),
            Tool(
                name="get_date",
                description="Get today's date",
                inputSchema={"type": "object"}
            )
        ]
        
        config_data = {
            "mcpServers": {
                "time": {
                    "command": "test",
                    "args": [],
                    "transport": "stdio"
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            with patch("os.path.exists", return_value=True):
                manager = MCPManager()
                await manager.load_config()
                
                # Manually register tools (simulating what start_servers would do)
                for tool in mock_tools:
                    manager.available_tools[f"time.{tool.name}"] = tool
                
                # Get available tools
                tools = manager.get_available_tools()
                
                assert len(tools) == 2
                
                # Check first tool
                time_tool = next(t for t in tools if t["name"] == "time.get_current_time")
                assert time_tool["description"] == "Get the current time in a specific timezone"
                assert "timezone" in time_tool["input_schema"]["properties"]
                
                # Check second tool
                date_tool = next(t for t in tools if t["name"] == "time.get_date")
                assert date_tool["description"] == "Get today's date"
    
    async def test_tool_name_prefixing(self):
        """Test that tool names are prefixed with server name to avoid conflicts."""
        from mcp import Tool
        
        config_data = {
            "mcpServers": {
                "server1": {"command": "test1", "args": []},
                "server2": {"command": "test2", "args": []}
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            with patch("os.path.exists", return_value=True):
                manager = MCPManager()
                await manager.load_config()
                
                # Register same tool name from different servers
                tool = Tool(name="get_data", description="Get data", inputSchema={})
                manager.available_tools["server1.get_data"] = tool
                manager.available_tools["server2.get_data"] = tool
                
                tools = manager.get_available_tools()
                tool_names = [t["name"] for t in tools]
                
                assert "server1.get_data" in tool_names
                assert "server2.get_data" in tool_names
    
    async def test_get_tools_for_prompt(self):
        """Test generating tool descriptions for LLM prompt."""
        from mcp import Tool
        
        manager = MCPManager()
        manager.available_tools = {
            "time.get_current_time": Tool(
                name="get_current_time",
                description="Get the current time in a specific timezone",
                inputSchema={}
            ),
            "weather.get_weather": Tool(
                name="get_weather", 
                description="Get current weather for a location",
                inputSchema={}
            )
        }
        
        prompt_text = manager.get_tools_for_prompt()
        
        assert "Available MCP Tools:" in prompt_text
        assert "time.get_current_time: Get the current time in a specific timezone" in prompt_text
        assert "weather.get_weather: Get current weather for a location" in prompt_text


@pytest.mark.asyncio
class TestMCPToolExecution:
    """Test MCP tool execution."""
    
    async def test_execute_tool_success(self):
        """Test successful tool execution."""
        from mcp import Tool, TextContent
        from mcp.types import CallToolResult
        
        config_data = {
            "mcpServers": {
                "time": {
                    "command": "test",
                    "args": [],
                    "transport": "stdio"
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            with patch("os.path.exists", return_value=True):
                manager = MCPManager()
                await manager.load_config()
                
                # Register a tool
                tool = Tool(
                    name="get_current_time",
                    description="Get current time",
                    inputSchema={}
                )
                manager.available_tools["time.get_current_time"] = tool
                
                # Mock the stdio_client context manager and session
                mock_session = AsyncMock()
                mock_result = CallToolResult(
                    content=[TextContent(text="Current time: 2:30 PM")]
                )
                mock_session.call_tool.return_value = mock_result
                
                with patch("unmute.mcp.mcp_manager.stdio_client") as mock_stdio:
                    mock_stdio.return_value.__aenter__.return_value = (None, None)
                    with patch("unmute.mcp.mcp_manager.ClientSession", return_value=mock_session):
                        result = await manager.execute_tool(
                            "time.get_current_time",
                            {"timezone": "UTC"}
                        )
                        
                        assert result == "Current time: 2:30 PM"
                        mock_session.call_tool.assert_called_once_with(
                            "get_current_time",
                            {"timezone": "UTC"}
                        )
    
    async def test_execute_tool_not_found(self):
        """Test error when executing non-existent tool."""
        manager = MCPManager()
        
        with pytest.raises(ValueError, match="Tool 'unknown.tool' not found"):
            await manager.execute_tool("unknown.tool", {})
    
    async def test_execute_tool_server_not_configured(self):
        """Test error when server for tool is not configured."""
        from mcp import Tool
        
        manager = MCPManager()
        manager.available_tools["unknown_server.tool"] = Tool(
            name="tool",
            description="Test tool",
            inputSchema={}
        )
        
        with pytest.raises(ValueError, match="Server 'unknown_server' not configured"):
            await manager.execute_tool("unknown_server.tool", {})
    
    async def test_execute_tool_with_error(self):
        """Test error handling during tool execution."""
        from mcp import Tool
        
        config_data = {
            "mcpServers": {
                "test": {
                    "command": "test",
                    "args": [],
                    "transport": "stdio"
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            with patch("os.path.exists", return_value=True):
                manager = MCPManager()
                await manager.load_config()
                
                tool = Tool(name="fail_tool", description="Tool that fails", inputSchema={})
                manager.available_tools["test.fail_tool"] = tool
                
                # Mock stdio_client to raise an exception
                with patch("unmute.mcp.mcp_manager.stdio_client") as mock_stdio:
                    mock_stdio.side_effect = Exception("Connection failed")
                    
                    with pytest.raises(Exception, match="Connection failed"):
                        await manager.execute_tool("test.fail_tool", {})


class TestMCPManager:
    """Test MCP Manager functionality."""
    
    def test_expand_env_vars(self):
        """Test environment variable expansion."""
        manager = MCPManager()
        
        # Test cases
        os.environ['TEST_VAR'] = 'test_value'
        
        assert manager._expand_env_vars('${TEST_VAR}') == 'test_value'
        assert manager._expand_env_vars('${MISSING_VAR:-default}') == 'default'
        assert manager._expand_env_vars('prefix_${TEST_VAR}_suffix') == 'prefix_test_value_suffix'
        assert manager._expand_env_vars('${MISSING_VAR}') == ''
        
        # Cleanup
        del os.environ['TEST_VAR']
    
    @pytest.mark.asyncio
    async def test_initialize_and_shutdown_lifecycle(self):
        """Test the full lifecycle of MCPManager initialization and shutdown."""
        config_data = {
            "mcpServers": {
                "time": {
                    "command": "test",
                    "args": []
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            with patch("os.path.exists", return_value=True):
                manager = MCPManager()
                
                # Initialize
                with patch.object(manager, 'start_servers', new_callable=AsyncMock) as mock_start:
                    await manager.initialize()
                    
                    assert manager._running is True
                    mock_start.assert_called_once()
                
                # Shutdown
                await manager.shutdown()
                
                assert manager._running is False
                assert len(manager.clients) == 0
                assert len(manager.available_tools) == 0
    
    @pytest.mark.asyncio
    async def test_environment_variable_expansion_in_config(self):
        """Test that environment variables are expanded in all config fields."""
        os.environ['TEST_COMMAND'] = '/usr/bin/python'
        os.environ['TEST_ARG'] = 'server.py'
        os.environ['TEST_KEY'] = 'secret123'
        os.environ['TEST_URL'] = 'http://localhost:8080'
        
        config_data = {
            "mcpServers": {
                "test": {
                    "command": "${TEST_COMMAND}",
                    "args": ["${TEST_ARG}", "--port", "${PORT:-3000}"],
                    "env": {
                        "API_KEY": "${TEST_KEY}",
                        "DEBUG": "${DEBUG:-false}"
                    },
                    "url": "${TEST_URL}",
                    "headers": {
                        "Authorization": "Bearer ${TEST_KEY}"
                    }
                }
            }
        }
        
        try:
            with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
                with patch("os.path.exists", return_value=True):
                    manager = MCPManager()
                    await manager.load_config()
                    
                    server = manager.servers["test"]
                    assert server.command == "/usr/bin/python"
                    assert server.args == ["server.py", "--port", "3000"]
                    assert server.env["API_KEY"] == "secret123"
                    assert server.env["DEBUG"] == "false"
                    assert server.url == "http://localhost:8080"
                    assert server.headers["Authorization"] == "Bearer secret123"
        finally:
            # Cleanup
            for var in ['TEST_COMMAND', 'TEST_ARG', 'TEST_KEY', 'TEST_URL']:
                if var in os.environ:
                    del os.environ[var]
    
    def test_config_loading(self):
        """Test configuration file structure."""
        # Test valid config structure
        valid_config = {
            "mcpServers": {
                "datetime": {
                    "command": "python",
                    "args": ["-m", "unmute.mcp.servers.datetime"],
                    "env": {}
                }
            }
        }
        
        # Validate structure
        assert "mcpServers" in valid_config
        assert "datetime" in valid_config["mcpServers"]
        assert "command" in valid_config["mcpServers"]["datetime"]


class TestToolCallParsing:
    """Test tool call parsing from LLM responses."""
    
    def test_tool_call_pattern_matching(self):
        """Test extracting tool calls from text."""
        pattern = r'TOOL_CALL:\s*(\w+(?:\.\w+)*)\((.*?)\)'
        
        test_cases = [
            ("TOOL_CALL: datetime.get_current_time()", 
             ("datetime.get_current_time", "")),
            ("Let me check. TOOL_CALL: datetime.get_current_time(location=\"Tokyo\")",
             ("datetime.get_current_time", 'location="Tokyo"')),
            ("TOOL_CALL: tool.name(arg1=\"val1\", arg2=\"val2\")",
             ("tool.name", 'arg1="val1", arg2="val2"')),
        ]
        
        for text, expected in test_cases:
            match = re.search(pattern, text)
            assert match is not None
            assert (match.group(1), match.group(2)) == expected
    
    def test_argument_parsing(self):
        """Test parsing tool call arguments."""
        def parse_args(args_str: str) -> dict:
            args = {}
            if args_str:
                for arg in args_str.split(','):
                    if '=' in arg:
                        key, value = arg.strip().split('=', 1)
                        value = value.strip().strip('"\'')
                        args[key] = value
            return args
        
        test_cases = [
            ('location="Tokyo"', {"location": "Tokyo"}),
            ("location='New York'", {"location": "New York"}),
            ('arg1="val1", arg2="val2"', {"arg1": "val1", "arg2": "val2"}),
            ("", {}),
        ]
        
        for args_str, expected in test_cases:
            assert parse_args(args_str) == expected


class TestChatbotMCPIntegration:
    """Test Chatbot MCP integration."""
    
    def test_update_with_mcp_tools(self):
        """Test updating system prompt with MCP tools."""
        chatbot = Chatbot()
        initial_prompt = chatbot.get_system_prompt()
        
        # Add MCP tools
        mcp_tools = "Available MCP Tools:\n- datetime.get_current_time: Get current time"
        chatbot.update_with_mcp_tools(mcp_tools)
        
        updated_prompt = chatbot.get_system_prompt()
        
        # Check that MCP section was added
        assert "# AVAILABLE TOOLS (MCP)" in updated_prompt
        assert "datetime.get_current_time" in updated_prompt
        assert "TOOL_CALL:" in updated_prompt
        assert len(updated_prompt) > len(initial_prompt)
    
    def test_update_with_empty_tools(self):
        """Test that empty tools don't modify the prompt."""
        chatbot = Chatbot()
        initial_prompt = chatbot.get_system_prompt()
        
        chatbot.update_with_mcp_tools("")
        
        assert chatbot.get_system_prompt() == initial_prompt


class TestWebSocketEvents:
    """Test WebSocket event definitions."""
    
    def test_mcp_event_types_exist(self):
        """Test that all MCP event types are defined."""
        from unmute import openai_realtime_api_events as ora
        
        required_events = [
            "MCPServersList",
            "MCPServersListResponse",
            "MCPServersStatus", 
            "MCPServersStatusResponse",
            "MCPToolsAvailable",
            "MCPToolsAvailableResponse",
            "MCPToolExecute",
            "MCPToolExecuteResponse",
        ]
        
        for event_name in required_events:
            assert hasattr(ora, event_name), f"Missing event type: {event_name}"
    
    def test_mcp_event_structure(self):
        """Test MCP event data structures."""
        from unmute import openai_realtime_api_events as ora
        
        # Test creating events
        list_event = ora.MCPServersList()
        assert list_event.type == "mcp.servers.list"
        
        execute_event = ora.MCPToolExecute(
            tool_name="datetime.get_current_time",
            arguments={"location": "Tokyo"}
        )
        assert execute_event.type == "mcp.tool.execute"
        assert execute_event.tool_name == "datetime.get_current_time"
        assert execute_event.arguments == {"location": "Tokyo"}


@pytest.mark.asyncio
class TestDatetimeServer:
    """Test the example datetime MCP server."""
    
    async def test_get_current_time(self):
        """Test get_current_time function."""
        from unmute.mcp.servers.datetime import get_current_time
        
        # Test without location
        result = await get_current_time()
        assert "Current time:" in result
        
        # Test with location
        result = await get_current_time("Tokyo")
        assert "Tokyo" in result
        assert "time" in result.lower()
    
    async def test_get_date(self):
        """Test get_date function."""
        from unmute.mcp.servers.datetime import get_date
        
        result = await get_date()
        assert "Today is" in result
        
    async def test_get_day_of_week(self):
        """Test get_day_of_week function."""
        from unmute.mcp.servers.datetime import get_day_of_week
        
        result = await get_day_of_week()
        assert "Today is" in result
        # Check it returns a valid day
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        assert any(day in result for day in days)


@pytest.mark.asyncio
class TestMCPIntegrationFlow:
    """Test the complete MCP integration flow."""
    
    async def test_full_mcp_workflow(self):
        """Test the complete workflow: discovery, registration, and execution."""
        from mcp import Tool, TextContent
        from mcp.types import CallToolResult
        
        # Configuration with multiple servers
        config_data = {
            "mcpServers": {
                "time": {
                    "command": "docker",
                    "args": ["run", "-i", "--rm", "mcp/time"],
                    "env": {"TZ": "UTC"},
                    "transport": "stdio"
                },
                "weather": {
                    "command": "python",
                    "args": ["-m", "weather_server"],
                    "transport": "stdio"
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            with patch("os.path.exists", return_value=True):
                # Step 1: Discovery - Create and initialize manager
                manager = MCPManager()
                await manager.load_config()
                
                # Verify servers discovered
                assert len(manager.servers) == 2
                assert "time" in manager.servers
                assert "weather" in manager.servers
                
                # Step 2: Registration - Mock tool registration
                time_tools = [
                    Tool(
                        name="get_current_time",
                        description="Get the current time in a specific timezone",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "timezone": {
                                    "type": "string",
                                    "description": "IANA timezone name"
                                }
                            }
                        }
                    ),
                    Tool(
                        name="get_date",
                        description="Get today's date",
                        inputSchema={"type": "object"}
                    )
                ]
                
                weather_tools = [
                    Tool(
                        name="get_weather",
                        description="Get current weather for a location",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "City name or coordinates"
                                }
                            },
                            "required": ["location"]
                        }
                    )
                ]
                
                # Register tools from each server
                for tool in time_tools:
                    manager.available_tools[f"time.{tool.name}"] = tool
                for tool in weather_tools:
                    manager.available_tools[f"weather.{tool.name}"] = tool
                
                # Verify tool registration
                all_tools = manager.get_available_tools()
                assert len(all_tools) == 3
                
                tool_names = [t["name"] for t in all_tools]
                assert "time.get_current_time" in tool_names
                assert "time.get_date" in tool_names
                assert "weather.get_weather" in tool_names
                
                # Verify tool descriptions are preserved
                time_tool = next(t for t in all_tools if t["name"] == "time.get_current_time")
                assert time_tool["description"] == "Get the current time in a specific timezone"
                assert "timezone" in time_tool["input_schema"]["properties"]
                
                # Step 3: Execution - Test tool execution
                mock_session = AsyncMock()
                mock_result = CallToolResult(
                    content=[TextContent(text="Current time in New York: 3:45 PM EST")]
                )
                mock_session.call_tool.return_value = mock_result
                mock_session.initialize = AsyncMock()
                
                with patch("unmute.mcp.mcp_manager.stdio_client") as mock_stdio:
                    mock_stdio.return_value.__aenter__.return_value = (None, None)
                    with patch("unmute.mcp.mcp_manager.ClientSession", return_value=mock_session):
                        # Execute tool with arguments
                        result = await manager.execute_tool(
                            "time.get_current_time",
                            {"timezone": "America/New_York"}
                        )
                        
                        assert result == "Current time in New York: 3:45 PM EST"
                        
                        # Verify correct tool was called with correct arguments
                        mock_session.call_tool.assert_called_once_with(
                            "get_current_time",
                            {"timezone": "America/New_York"}
                        )
                
                # Verify tools can be formatted for LLM prompt
                prompt_tools = manager.get_tools_for_prompt()
                assert "Available MCP Tools:" in prompt_tools
                assert "time.get_current_time: Get the current time in a specific timezone" in prompt_tools
                assert "weather.get_weather: Get current weather for a location" in prompt_tools
    
    async def test_chatbot_integration_with_mcp(self):
        """Test that MCP tools integrate properly with the chatbot."""
        from mcp import Tool
        
        # Create a chatbot and MCP manager
        chatbot = Chatbot()
        manager = MCPManager()
        
        # Mock some tools
        manager.available_tools = {
            "time.get_current_time": Tool(
                name="get_current_time",
                description="Get the current time in a specific timezone",
                inputSchema={}
            ),
            "weather.get_weather": Tool(
                name="get_weather",
                description="Get current weather for a location",
                inputSchema={}
            )
        }
        
        # Update chatbot with MCP tools
        tools_prompt = manager.get_tools_for_prompt()
        chatbot.update_with_mcp_tools(tools_prompt)
        
        # Verify the system prompt includes MCP tools
        system_prompt = chatbot.get_system_prompt()
        assert "# AVAILABLE TOOLS (MCP)" in system_prompt
        assert "time.get_current_time" in system_prompt
        assert "weather.get_weather" in system_prompt
        assert "TOOL_CALL:" in system_prompt
        
        # Verify tool call format is explained
        assert "TOOL_CALL: tool_name(arg1=\"value1\", arg2=\"value2\")" in system_prompt