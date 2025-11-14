#!/usr/bin/env python3
"""
ULTRA MINIMAL TEST - Just imports, no logic
"""
import sys
print("STEP 1: Script started", file=sys.stderr, flush=True)

try:
    import asyncio
    print("STEP 2: asyncio imported", file=sys.stderr, flush=True)
except Exception as e:
    print(f"STEP 2 FAILED: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

try:
    import json
    print("STEP 3: json imported", file=sys.stderr, flush=True)
except Exception as e:
    print(f"STEP 3 FAILED: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

try:
    import sqlite3
    print("STEP 4: sqlite3 imported", file=sys.stderr, flush=True)
except Exception as e:
    print(f"STEP 4 FAILED: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

try:
    from pathlib import Path
    print("STEP 5: pathlib imported", file=sys.stderr, flush=True)
except Exception as e:
    print(f"STEP 5 FAILED: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

try:
    from mcp.server import Server
    print("STEP 6: mcp.server imported", file=sys.stderr, flush=True)
except Exception as e:
    print(f"STEP 6 FAILED: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

try:
    from mcp.server.stdio import stdio_server
    print("STEP 7: mcp.server.stdio imported", file=sys.stderr, flush=True)
except Exception as e:
    print(f"STEP 7 FAILED: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

try:
    from mcp.types import Tool, TextContent
    print("STEP 8: mcp.types imported", file=sys.stderr, flush=True)
except Exception as e:
    print(f"STEP 8 FAILED: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

print("STEP 9: All imports successful!", file=sys.stderr, flush=True)

# Check file system
try:
    PROJECT_ROOT = Path(__file__).parent.parent
    print(f"STEP 10: Project root: {PROJECT_ROOT}", file=sys.stderr, flush=True)
    
    DB_PATH = PROJECT_ROOT / "data" / "boxing_data.db"
    print(f"STEP 11: DB path: {DB_PATH}", file=sys.stderr, flush=True)
    print(f"STEP 12: DB exists: {DB_PATH.exists()}", file=sys.stderr, flush=True)
    
except Exception as e:
    print(f"STEP 10-12 FAILED: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

# Create minimal server
print("STEP 13: Creating server", file=sys.stderr, flush=True)
app = Server("test-server")

@app.list_tools()
async def list_tools():
    print("STEP 14: list_tools called", file=sys.stderr, flush=True)
    return [
        Tool(
            name="test_tool",
            description="Test tool",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    print(f"STEP 15: call_tool called: {name}", file=sys.stderr, flush=True)
    return [TextContent(type="text", text='{"status": "ok"}')]

async def main():
    print("STEP 16: main() started", file=sys.stderr, flush=True)
    try:
        async with stdio_server() as (read_stream, write_stream):
            print("STEP 17: stdio_server created", file=sys.stderr, flush=True)
            await app.run(read_stream, write_stream, app.create_initialization_options())
            print("STEP 18: app.run completed", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"STEP 16-18 FAILED: {e}", file=sys.stderr, flush=True)
        import traceback
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        raise

if __name__ == "__main__":
    print("STEP 19: Entry point", file=sys.stderr, flush=True)
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"STEP 19 FAILED: {e}", file=sys.stderr, flush=True)
        import traceback
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        sys.exit(1)