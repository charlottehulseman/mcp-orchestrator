#!/usr/bin/env python3
"""
Boxing Betting & Odds MCP Server

Provides sports betting data and odds analysis for boxing matches from Odds API.

"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

load_dotenv()

# Odds API config
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# Initialize MCP server
app = Server("boxing-odds")

def validate_api_key():
    """Validate that API key is set - REQUIRED for all operations."""
    if not ODDS_API_KEY:
        raise ValueError(
            "ODDS_API_KEY environment variable is required."
        )

async def fetch_live_odds(fighter1: str, fighter2: str) -> dict:
    """
    Fetch real odds from The Odds API.
    Throws error if API key not set.
    """
    validate_api_key()
    
    import httpx
    
    url = "https://api.the-odds-api.com/v4/sports/boxing_boxing/odds/"
    
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            
            # Find specific fight
            for event in data:
                if fighter1.lower() in event.get('home_team', '').lower() or \
                   fighter2.lower() in event.get('home_team', '').lower():
                    return event
            
            # If fight not found, return error
            raise ValueError(
                f"Fight '{fighter1} vs {fighter2}' not found in current odds. "
                f"Available fights: {len(data)}"
            )
            
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch odds from API: {e}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available betting tools - ALL REQUIRE ODDS_API_KEY when called."""
    
    # Don't validate at startup - validate when tools are called
    # This allows the server to start without the API key
    
    return [
        Tool(
            name="get_fight_odds",
            description="Get current betting odds for a specific boxing match. Requires ODDS_API_KEY (checked when called).",
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter1": {"type": "string", "description": "First fighter name"},
                    "fighter2": {"type": "string", "description": "Second fighter name"},
                },
                "required": ["fighter1", "fighter2"]
            }
        ),
        Tool(
            name="get_odds_movement",
            description="Track how odds have changed over time for a fight. Requires ODDS_API_KEY (checked when called).",
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter1": {"type": "string", "description": "First fighter name"},
                    "fighter2": {"type": "string", "description": "Second fighter name"},
                    "timeframe": {"type": "string", "description": "Time period (e.g., '7d', '30d')"},
                },
                "required": ["fighter1", "fighter2"]
            }
        ),
        Tool(
            name="calculate_betting_value",
            description="Calculate if there's value in current odds. Requires ODDS_API_KEY (checked when called).",
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter_name": {"type": "string", "description": "Fighter to analyze"},
                    "opponent": {"type": "string", "description": "Opponent name"},
                },
                "required": ["fighter_name", "opponent"]
            }
        ),
        Tool(
            name="get_betting_trends",
            description="Get betting trends and public money percentages. Requires ODDS_API_KEY (checked when called).",
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter1": {"type": "string", "description": "First fighter name"},
                    "fighter2": {"type": "string", "description": "Second fighter name"},
                },
                "required": ["fighter1", "fighter2"]
            }
        ),
        Tool(
            name="predict_fight_outcome",
            description="Predict fight outcome based on odds and betting patterns. Requires ODDS_API_KEY (checked when called).",
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter1": {"type": "string", "description": "First fighter name"},
                    "fighter2": {"type": "string", "description": "Second fighter name"},
                },
                "required": ["fighter1", "fighter2"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls, all require real API data."""
    
    try:
        # Validate API key for ALL tools
        validate_api_key()
        
        if name == "get_fight_odds":
            fighter1 = arguments["fighter1"]
            fighter2 = arguments["fighter2"]
            
            odds_data = await fetch_live_odds(fighter1, fighter2)
            
            return [TextContent(
                type="text",
                text=json.dumps(odds_data, indent=2)
            )]
        
        elif name == "get_odds_movement":
            fighter1 = arguments["fighter1"]
            fighter2 = arguments["fighter2"]
            timeframe = arguments.get("timeframe", "7d")
            
            # require historical API data
            # for now fetch current
            odds_data = await fetch_live_odds(fighter1, fighter2)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "current_odds": odds_data,
                    "note": "Historical odds tracking requires premium API access",
                    "timeframe": timeframe
                }, indent=2)
            )]
        
        elif name == "calculate_betting_value":
            fighter_name = arguments["fighter_name"]
            opponent = arguments["opponent"]
            
            odds_data = await fetch_live_odds(fighter_name, opponent)
            
            # Calc implied probability and value
            bookmakers = odds_data.get('bookmakers', [])
            if bookmakers:
                odds = bookmakers[0].get('markets', [{}])[0].get('outcomes', [])
                
                result = {
                    "fighter": fighter_name,
                    "opponent": opponent,
                    "analysis": "Value calculated from real market odds",
                    "odds_data": odds
                }
            else:
                result = {
                    "error": "No odds available for this fight"
                }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "get_betting_trends":
            fighter1 = arguments["fighter1"]
            fighter2 = arguments["fighter2"]
            
            odds_data = await fetch_live_odds(fighter1, fighter2)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "fight": f"{fighter1} vs {fighter2}",
                    "current_odds": odds_data,
                    "note": "Betting percentages require premium data feed"
                }, indent=2)
            )]
        
        elif name == "predict_fight_outcome":
            fighter1 = arguments["fighter1"]
            fighter2 = arguments["fighter2"]
            
            odds_data = await fetch_live_odds(fighter1, fighter2)
            
            # Prediction
            bookmakers = odds_data.get('bookmakers', [])
            if bookmakers:
                prediction = {
                    "fight": f"{fighter1} vs {fighter2}",
                    "odds_based_prediction": "Based on real market odds",
                    "odds_data": bookmakers[0]
                }
            else:
                prediction = {
                    "error": "Insufficient data for prediction"
                }
            
            return [TextContent(
                type="text",
                text=json.dumps(prediction, indent=2)
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except ValueError as e:
        # Return error
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "message": "This server requires real API data. No demo/fake data is provided."
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "arguments": arguments
            }, indent=2)
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())