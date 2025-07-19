#!/usr/bin/env python3
"""Test MCP tool calling through direct LLM interaction."""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unmute.mcp.mcp_manager import MCPManager
from unmute.llm.chatbot import Chatbot
from unmute.llm.vllm_stream import VLLMStream
from unmute.llm.openai_utils import OpenAI

async def test_mcp_direct():
    """Test MCP tool calling directly without WebSocket."""
    print("🚀 Starting direct MCP test...")
    
    # Initialize MCP manager
    mcp_manager = MCPManager()
    await mcp_manager.initialize()
    print(f"✅ MCP initialized with tools: {list(mcp_manager.available_tools.keys())}")
    
    # Set up chatbot
    chatbot = Chatbot()
    
    # Add MCP tools to system prompt
    mcp_tools_desc = mcp_manager.get_tools_for_prompt()
    chatbot.update_with_mcp_tools(mcp_tools_desc)
    print("✅ Updated chatbot with MCP tools")
    
    # Add user message
    await chatbot.add_chat_message_delta("What time is it?", "user")
    print("💬 User: What time is it?")
    
    # Get LLM response
    client = OpenAI()
    llm = VLLMStream(client, temperature=0.7)
    
    print("🤖 Getting LLM response...")
    response_words = []
    tool_call_detected = False
    
    async for word in llm.chat_completion(chatbot.chat_history):
        response_words.append(word)
        current_response = " ".join(response_words)
        
        # Check for tool call
        if "TOOL_CALL:" in current_response and not tool_call_detected:
            tool_call_detected = True
            print(f"🔧 Tool call detected in response: {current_response}")
            
            # Extract tool call
            tool_call_start = current_response.find("TOOL_CALL:")
            tool_part = current_response[tool_call_start:]
            
            # Parse tool call
            if "(" in tool_part and ")" in tool_part:
                tool_call_end = tool_part.find(")") + 1
                tool_call = tool_part[:tool_call_end]
                print(f"📞 Full tool call: {tool_call}")
                
                # Execute tool
                tool_name = tool_call.split("(")[0].replace("TOOL_CALL:", "").strip()
                
                # Extract arguments if any
                args = {}
                if "(" in tool_call and ")" in tool_call:
                    args_str = tool_call.split("(")[1].split(")")[0]
                    if args_str:
                        # Parse key=value pairs
                        for arg in args_str.split(','):
                            if '=' in arg:
                                key, value = arg.strip().split('=', 1)
                                # Remove quotes if present
                                value = value.strip().strip('"\'')
                                args[key] = value
                
                print(f"🚀 Executing tool: {tool_name} with args: {args}")
                try:
                    result = await mcp_manager.execute_tool(tool_name, args)
                    print(f"✅ Tool result: {result}")
                    
                    # Test interpretation
                    print("\n🎭 Testing interpretation...")
                    interpretation_history = chatbot.chat_history.copy()
                    interpretation_history.append({
                        "role": "system",
                        "content": f"The time tool returned: {result}\nProvide this information to the user in a natural, conversational way."
                    })
                    
                    interp_llm = VLLMStream(client, temperature=0.7)
                    interp_words = []
                    
                    async for word in interp_llm.chat_completion(interpretation_history):
                        interp_words.append(word)
                    
                    interpretation = " ".join(interp_words)
                    print(f"💬 Interpretation: {interpretation}")
                    
                except Exception as e:
                    print(f"❌ Tool execution failed: {e}")
                    import traceback
                    traceback.print_exc()
                
                break
    
    if not tool_call_detected:
        print(f"⚠️ No tool call detected. LLM response: {' '.join(response_words)}")
    
    # Cleanup
    await mcp_manager.shutdown()
    print("✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_mcp_direct())