#!/usr/bin/env python3
"""
Boxing Analytics MCP Server - RAILWAY DIAGNOSTIC
Logs to stderr (Railway can see it) and never exits
"""

import asyncio
import json
import sqlite3
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

def log(msg):
    """Log to stderr so Railway can see it."""
    print(f"[DIAGNOSTIC] {msg}", file=sys.stderr, flush=True)

log("=== SERVER STARTING ===")
log(f"Python version: {sys.version}")
log(f"Current working directory: {os.getcwd()}")
log(f"Script location: {__file__}")

# Database path
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "boxing_data.db"

log(f"Project root: {PROJECT_ROOT}")
log(f"Database path: {DB_PATH}")
log(f"Database absolute: {DB_PATH.absolute()}")
log(f"Database exists: {DB_PATH.exists()}")

# List project root
try:
    items = list(PROJECT_ROOT.iterdir())
    log(f"Items in project root: {[i.name for i in items]}")
except Exception as e:
    log(f"Error listing project root: {e}")

# Check data directory
data_dir = PROJECT_ROOT / "data"
log(f"Data directory exists: {data_dir.exists()}")
if data_dir.exists():
    try:
        files = list(data_dir.iterdir())
        log(f"Files in data/: {[f.name for f in files]}")
    except Exception as e:
        log(f"Error listing data/: {e}")

# Try prediction import
PREDICTION_AVAILABLE = False
try:
    sys.path.insert(0, str(PROJECT_ROOT))
    log(f"Added to sys.path: {PROJECT_ROOT}")
    
    from mcp_servers.boxing_prediction import (
        analyze_career_trajectory,
        compare_common_opponents,
        analyze_title_fight_performance
    )
    PREDICTION_AVAILABLE = True
    log("✓ Prediction module loaded")
except ImportError as e:
    log(f"⚠ Prediction module failed: {e}")
except Exception as e:
    log(f"⚠ Unexpected error loading prediction: {e}")

log(f"Prediction available: {PREDICTION_AVAILABLE}")


def get_db_connection():
    """Get a database connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def format_record(wins: int, losses: int, draws: int) -> str:
    """Format a fighter's record as W-L-D string."""
    return f"{wins}-{losses}-{draws}"


async def get_fighter_stats(name: str) -> Dict[str, Any]:
    """Get comprehensive statistics for a fighter."""
    log(f"get_fighter_stats called for: {name}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM fighters 
            WHERE LOWER(name) LIKE LOWER(?)
            ORDER BY 
                CASE WHEN LOWER(name) = LOWER(?) THEN 0 ELSE 1 END,
                record_wins DESC
            LIMIT 1
        """, (f"%{name}%", name))
        
        fighter = cursor.fetchone()
        
        if not fighter:
            conn.close()
            return {
                "error": f"Fighter '{name}' not found",
                "suggestion": "Try searching with a different spelling"
            }
        
        conn.close()
        
        return {
            "name": fighter['name'],
            "nickname": fighter['nickname'],
            "nationality": fighter['nationality'],
            "weight_class": fighter['weight_class'],
            "record": format_record(fighter['record_wins'], fighter['record_losses'], fighter['record_draws']),
        }
    except Exception as e:
        log(f"Error in get_fighter_stats: {e}")
        return {"error": str(e)}


app = Server("boxing-analytics")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available boxing analytics tools."""
    log("list_tools() called")
    
    tools = [
        Tool(
            name="get_fighter_stats",
            description="Get statistics for a boxer (RAILWAY DIAGNOSTIC VERSION)",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Fighter's name"}
                },
                "required": ["name"]
            }
        ),
    ]
    
    # Add prediction tools if available
    if PREDICTION_AVAILABLE:
        tools.extend([
            Tool(
                name="analyze_career_trajectory",
                description="Analyze fighter's career trajectory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Fighter name"},
                        "window": {"type": "integer", "description": "Rolling window size", "default": 5}
                    },
                    "required": ["name"]
                }
            ),
        ])
    
    log(f"Returning {len(tools)} tools")
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a boxing analytics tool."""
    log(f"call_tool: {name} with {arguments}")
    
    try:
        if name == "get_fighter_stats":
            result = await get_fighter_stats(arguments["name"])
        elif PREDICTION_AVAILABLE and name == "analyze_career_trajectory":
            result = await analyze_career_trajectory(
                arguments["name"],
                arguments.get("window", 5)
            )
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        log(f"Error in call_tool: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name}, indent=2)
        )]


async def main():
    """Run the MCP server."""
    log("main() starting")
    
    # Check database BEFORE starting server
    if not DB_PATH.exists():
        log(f"ERROR: Database not found at {DB_PATH}")
        log(f"Absolute path: {DB_PATH.absolute()}")
        log(f"CWD: {os.getcwd()}")
        # Don't exit - let it try to start anyway
    else:
        log(f"✓ Database found: {DB_PATH.stat().st_size} bytes")
    
    try:
        log("Starting stdio_server...")
        async with stdio_server() as (read_stream, write_stream):
            log("✓ stdio_server created")
            log("Running app.run()...")
            await app.run(read_stream, write_stream, app.create_initialization_options())
            log("app.run() completed")
    except Exception as e:
        log(f"ERROR in main(): {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    log("=== SCRIPT ENTRY POINT ===")
    try:
        asyncio.run(main())
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        raise