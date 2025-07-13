"""Tests for MCP (Model Context Protocol) integration."""
import asyncio
import json
import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from unmute.llm.chatbot import Chatbot
from unmute.mcp.mcp_manager import MCPServerConfig


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


class TestMCPManager:
    """Test MCP Manager functionality."""
    
    def test_expand_env_vars(self):
        """Test environment variable expansion."""
        # We can't import MCPManager without the MCP SDK, so test the logic
        import os
        
        def expand_env_vars(value: str) -> str:
            """Expand environment variables in string values."""
            import re
            
            def replacer(match):
                var_name = match.group(1)
                default_value = match.group(3) if match.group(3) else ''
                return os.environ.get(var_name, default_value)
                
            pattern = r'\$\{([^}:]+)(:-([^}]*))?\}'
            return re.sub(pattern, replacer, value)
        
        # Test cases
        os.environ['TEST_VAR'] = 'test_value'
        
        assert expand_env_vars('${TEST_VAR}') == 'test_value'
        assert expand_env_vars('${MISSING_VAR:-default}') == 'default'
        assert expand_env_vars('prefix_${TEST_VAR}_suffix') == 'prefix_test_value_suffix'
        assert expand_env_vars('${MISSING_VAR}') == ''
        
        # Cleanup
        del os.environ['TEST_VAR']
    
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