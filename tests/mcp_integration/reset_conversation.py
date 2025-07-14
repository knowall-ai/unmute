#!/usr/bin/env python3
"""Reset conversation and test MCP"""

import subprocess
import time

print("=== Resetting Unmute Conversation ===\n")

# Restart backend to clear conversation state
print("1. Restarting backend to clear conversation state...")
subprocess.run(["docker", "restart", "unmute-backend"], capture_output=True)
print("   Waiting for backend to start...")
time.sleep(5)

print("\n2. Backend restarted successfully!")
print("\n3. Instructions for testing:")
print("   a) Open http://localhost:3000 in your browser")
print("   b) Refresh the page (F5)")
print("   c) Select a voice")
print("   d) Ask clearly: 'What day is it today?'")
print("   e) Or ask: 'Tell me the current time'")

print("\n4. Expected behavior:")
print("   - The model should generate: TOOL_CALL: datetime.get_day_of_week()")
print("   - Backend should execute the tool")
print("   - You should hear: 'Today is Monday'")

print("\n5. Monitor logs in another terminal:")
print("   docker logs -f unmute-backend | grep -E 'TOOL_CALL|Executing MCP|Tool result'")

print("\n✅ Ready for testing!")