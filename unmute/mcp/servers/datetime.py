#!/usr/bin/env python3
"""Example MCP server that provides datetime functionality.

This server demonstrates how to create an MCP server for Unmute
that can be called via voice commands.
"""
import asyncio
import datetime
import json
import sys
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.tools import Tool
from pydantic import AnyUrl

# Try different timezone libraries
try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False

try:
    import zoneinfo
    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False


async def get_current_time(location: str | None = None) -> str:
    """Get the current time, optionally for a specific location/timezone.
    
    Args:
        location: Optional location or timezone (e.g., "Tokyo", "America/New_York")
        
    Returns:
        Current time as a string
    """
    now = datetime.datetime.now()
    
    if location:
        # Try to map location to timezone
        timezone_map = {
            # Common cities
            "tokyo": "Asia/Tokyo",
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "new york": "America/New_York",
            "los angeles": "America/Los_Angeles",
            "sydney": "Australia/Sydney",
            "mumbai": "Asia/Kolkata",
            "beijing": "Asia/Shanghai",
            "moscow": "Europe/Moscow",
            "dubai": "Asia/Dubai",
            # Common timezone names
            "pst": "America/Los_Angeles",
            "est": "America/New_York",
            "cst": "America/Chicago",
            "mst": "America/Denver",
            "gmt": "UTC",
            "utc": "UTC",
        }
        
        # Normalize location name
        location_lower = location.lower().strip()
        tz_name = timezone_map.get(location_lower, location)
        
        try:
            if HAS_PYTZ:
                tz = pytz.timezone(tz_name)
                now = datetime.datetime.now(tz)
            elif HAS_ZONEINFO:
                tz = zoneinfo.ZoneInfo(tz_name)
                now = datetime.datetime.now(tz)
            else:
                # Fallback to UTC offset calculation (basic)
                return f"Current time in {location}: {now.strftime('%I:%M %p')} (timezone support not available)"
                
            return f"Current time in {location}: {now.strftime('%I:%M %p on %A, %B %d, %Y')}"
        except Exception:
            return f"Could not find timezone for '{location}'. Current local time: {now.strftime('%I:%M %p on %A, %B %d, %Y')}"
    else:
        return f"Current time: {now.strftime('%I:%M %p on %A, %B %d, %Y')}"


async def get_date() -> str:
    """Get the current date.
    
    Returns:
        Current date as a string
    """
    today = datetime.date.today()
    return f"Today is {today.strftime('%A, %B %d, %Y')}"


async def get_day_of_week() -> str:
    """Get the current day of the week.
    
    Returns:
        Current day of the week
    """
    today = datetime.date.today()
    return f"Today is {today.strftime('%A')}"


async def run_server():
    """Run the MCP datetime server."""
    async with stdio_server() as (read_stream, write_stream):
        await serve_datetime_tools(read_stream, write_stream)


async def serve_datetime_tools(read_stream, write_stream):
    """Serve datetime tools via MCP protocol."""
    # Define available tools
    tools = [
        Tool(
            name="get_current_time",
            description="Get the current time, optionally for a specific location",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location or timezone (e.g., 'Tokyo', 'America/New_York')"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_date",
            description="Get the current date",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_day_of_week",
            description="Get the current day of the week",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]
    
    # Tool handlers
    tool_handlers = {
        "get_current_time": get_current_time,
        "get_date": get_date,
        "get_day_of_week": get_day_of_week,
    }
    
    # Create server
    from mcp.server import Server
    server = Server("datetime-server")
    
    # Register tools
    for tool in tools:
        server.add_tool(tool)
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Handle tool execution requests."""
        if name not in tool_handlers:
            raise ValueError(f"Unknown tool: {name}")
            
        handler = tool_handlers[name]
        result = await handler(**(arguments or {}))
        
        return [{
            "type": "text",
            "text": result
        }]
    
    # Set initialization options
    initialization_options = InitializationOptions(
        server_name="datetime-server",
        server_version="1.0.0"
    )
    
    # Run the server
    await server.run(
        read_stream,
        write_stream,
        initialization_options
    )


if __name__ == "__main__":
    asyncio.run(run_server())