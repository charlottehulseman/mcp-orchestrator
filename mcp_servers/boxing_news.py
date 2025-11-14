#!/usr/bin/env python3
"""
Boxing News & Media MCP Server - REAL DATA ONLY

Provides fight news and media coverage for boxing.
Requires NEWS_API_KEY for real articles.
NO DEMO/FAKE DATA - REAL PROJECT ONLY.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

# Load env variables
load_dotenv()


# News API config
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def validate_news_api_key():
    """Validate that NEWS API key is set - REQUIRED for news operations."""
    if not NEWS_API_KEY:
        raise ValueError(
            "NEWS_API_KEY environment variable is REQUIRED for news data. "
            "This server does not provide demo/fake data. "
            "Get your API key from: https://newsapi.org/ "
            "Then set it with: export NEWS_API_KEY='your_key'"
        )


async def get_fight_news(
    fighter_name: Optional[str] = None,
    days_back: int = 7,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Get REAL boxing news from News API.
    NO FAKE DATA - requires NEWS_API_KEY.
    
    Args:
        fighter_name: Fighter to search for (optional)
        days_back: How many days of news to fetch
        max_results: Maximum number of articles to return
    
    Returns:
        Real news articles from News API
    """
    validate_news_api_key()
    
    try:
        import httpx
    except ImportError:
        raise ValueError("httpx not installed. Run: pip install httpx")
    
    query = f"{fighter_name} boxing" if fighter_name else "boxing"
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": max_results,
        "apiKey": NEWS_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data.get("articles", []):
                articles.append({
                    "title": article["title"],
                    "description": article.get("description", ""),
                    "source": article["source"]["name"],
                    "author": article.get("author", "Unknown"),
                    "published_at": article["publishedAt"],
                    "url": article["url"],
                })
            
            return {
                "query": query,
                "period": f"Last {days_back} days",
                "total_articles": len(articles),
                "articles": articles
            }
            
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch news from API: {e}")


async def get_social_buzz(
    fighter_name: str,
    platform: str = "all",
    hours_back: int = 24
) -> Dict[str, Any]:
    """
    ERROR: Social media APIs require authentication and are not available.
    
    Twitter API and Reddit API require:
    - Twitter: Developer account + API keys (rate limited)
    - Reddit: OAuth credentials
    
    This function returns an error explaining the limitation.
    """
    return {
        "error": "Social media data unavailable",
        "reason": "Twitter and Reddit APIs require authentication",
        "fighter": fighter_name,
        "message": (
            "To get real social media data, you need:\n"
            "1. Twitter API: https://developer.twitter.com/ (requires approval)\n"
            "2. Reddit API: https://www.reddit.com/prefs/apps (requires OAuth)\n"
            "\nThese APIs have strict rate limits and authentication requirements."
        ),
        "alternative": "Use news articles and betting odds for sentiment analysis instead"
    }


async def compare_fighter_hype(
    fighter1: str,
    fighter2: str,
    days_back: int = 7
) -> Dict[str, Any]:
    """
    Compare media attention based on REAL news article counts.
    NO FAKE DATA - only counts actual news articles.
    """
    validate_news_api_key()
    
    # Get real news for both fighters
    news1 = await get_fight_news(fighter1, days_back, max_results=50)
    news2 = await get_fight_news(fighter2, days_back, max_results=50)
    
    count1 = news1.get("total_articles", 0)
    count2 = news2.get("total_articles", 0)
    
    if count1 == 0 and count2 == 0:
        return {
            "error": "No news articles found for either fighter",
            "fighter1": fighter1,
            "fighter2": fighter2,
            "suggestion": "Try searching with full fighter names or check spelling"
        }
    
    # Determine leader based on REAL article counts
    if count1 > count2:
        leader = fighter1
        diff = count1 - count2
        pct_diff = (diff / count2 * 100) if count2 > 0 else 100
    elif count2 > count1:
        leader = fighter2
        diff = count2 - count1
        pct_diff = (diff / count1 * 100) if count1 > 0 else 100
    else:
        leader = "Tied"
        diff = 0
        pct_diff = 0
    
    return {
        "fighter1": fighter1,
        "fighter2": fighter2,
        "analysis_period": f"Last {days_back} days",
        "comparison": {
            fighter1: {
                "news_articles": count1,
                "sample_headlines": [a["title"] for a in news1.get("articles", [])[:3]]
            },
            fighter2: {
                "news_articles": count2,
                "sample_headlines": [a["title"] for a in news2.get("articles", [])[:3]]
            }
        },
        "verdict": {
            "media_leader": leader,
            "article_difference": diff,
            "percentage_advantage": round(pct_diff, 1) if leader != "Tied" else 0,
            "interpretation": f"{leader} has {diff} more articles ({pct_diff:.0f}% more coverage)" if leader != "Tied" else "Equal media coverage"
        }
    }


async def get_fight_predictions(
    fighter1: str,
    fighter2: str,
    source: str = "all"
) -> Dict[str, Any]:
    """
    ERROR: Expert predictions require web scraping or dedicated APIs.
    
    Real implementation would need:
    - Web scraping of ESPN, Ring Magazine, etc. (legally complex)
    - Dedicated sports prediction APIs (expensive)
    
    Returns error explaining the limitation.
    """
    return {
        "error": "Expert predictions unavailable",
        "reason": "Requires web scraping or dedicated prediction APIs",
        "fight": f"{fighter1} vs {fighter2}",
        "message": (
            "To get real expert predictions, you would need:\n"
            "1. Web scraping (legally complex, ToS violations)\n"
            "2. Dedicated sports prediction APIs (e.g., Odds API with predictions)\n"
            "3. Manual data entry from expert sources\n"
            "\nThese options have legal and technical constraints."
        ),
        "alternative": "Use betting odds as a proxy for expert consensus (odds reflect market wisdom)"
    }


async def analyze_press_conference(
    fighter_name: str,
    event: str = "recent"
) -> Dict[str, Any]:
    """
    ERROR: Press conference analysis requires video/transcript APIs.
    
    Real implementation would need:
    - YouTube Data API (for press conference videos)
    - Transcript extraction (Speech-to-text)
    - NLP sentiment analysis
    
    Returns error explaining the limitation.
    """
    return {
        "error": "Press conference analysis unavailable",
        "reason": "Requires video/transcript APIs and NLP processing",
        "fighter": fighter_name,
        "message": (
            "To get real press conference analysis, you would need:\n"
            "1. YouTube Data API (for video access)\n"
            "2. Speech-to-text service (Google, AWS, etc.)\n"
            "3. NLP sentiment analysis (requires ML models)\n"
            "\nThis is a complex multi-API integration."
        ),
        "alternative": "Use news articles and betting odds movement instead"
    }


# Create MCP server
app = Server("boxing-news")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available boxing news tools - REQUIRES NEWS_API_KEY when called."""
    
    # Don't validate at startup - validate when tools are called
    # This allows the server to start even without the API key
    
    return [
        Tool(
            name="get_fight_news",
            description=(
                "Get REAL boxing news articles from News API. "
                "Requires NEWS_API_KEY (checked when called). Returns actual articles with titles, "
                "summaries, sources, and URLs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter_name": {
                        "type": "string",
                        "description": "Fighter to search for (optional)"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "How many days of news to fetch",
                        "default": 7
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum articles to return",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_social_buzz",
            description=(
                "UNAVAILABLE: Social media APIs require authentication. "
                "Returns error explaining limitations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter_name": {
                        "type": "string",
                        "description": "Fighter to analyze"
                    },
                    "platform": {
                        "type": "string",
                        "description": "Social platform (twitter, reddit, all)",
                        "default": "all"
                    },
                    "hours_back": {
                        "type": "integer",
                        "description": "Hours of social data to analyze",
                        "default": 24
                    }
                },
                "required": ["fighter_name"]
            }
        ),
        Tool(
            name="compare_fighter_hype",
            description=(
                "Compare media attention between fighters based on REAL news article counts. "
                "Requires NEWS_API_KEY (checked when called). Uses actual article counts, no fake metrics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter1": {
                        "type": "string",
                        "description": "First fighter name"
                    },
                    "fighter2": {
                        "type": "string",
                        "description": "Second fighter name"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Days of media coverage to analyze",
                        "default": 7
                    }
                },
                "required": ["fighter1", "fighter2"]
            }
        ),
        Tool(
            name="get_fight_predictions",
            description=(
                "UNAVAILABLE: Expert predictions require web scraping. "
                "Returns error explaining limitations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter1": {
                        "type": "string",
                        "description": "First fighter name"
                    },
                    "fighter2": {
                        "type": "string",
                        "description": "Second fighter name"
                    },
                    "source": {
                        "type": "string",
                        "description": "Prediction source (espn, ringtv, all)",
                        "default": "all"
                    }
                },
                "required": ["fighter1", "fighter2"]
            }
        ),
        Tool(
            name="analyze_press_conference",
            description=(
                "UNAVAILABLE: Press conference analysis requires video/transcript APIs. "
                "Returns error explaining limitations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter_name": {
                        "type": "string",
                        "description": "Fighter to analyze"
                    },
                    "event": {
                        "type": "string",
                        "description": "Specific event or 'recent'",
                        "default": "recent"
                    }
                },
                "required": ["fighter_name"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a boxing news tool - ALL require real data or return errors."""
    try:
        if name == "get_fight_news":
            result = await get_fight_news(
                arguments.get("fighter_name"),
                arguments.get("days_back", 7),
                arguments.get("max_results", 10)
            )
        elif name == "get_social_buzz":
            result = await get_social_buzz(
                arguments["fighter_name"],
                arguments.get("platform", "all"),
                arguments.get("hours_back", 24)
            )
        elif name == "compare_fighter_hype":
            result = await compare_fighter_hype(
                arguments["fighter1"],
                arguments["fighter2"],
                arguments.get("days_back", 7)
            )
        elif name == "get_fight_predictions":
            result = await get_fight_predictions(
                arguments["fighter1"],
                arguments["fighter2"],
                arguments.get("source", "all")
            )
        elif name == "analyze_press_conference":
            result = await analyze_press_conference(
                arguments["fighter_name"],
                arguments.get("event", "recent")
            )
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    except ValueError as e:
        # Return clear error to user
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