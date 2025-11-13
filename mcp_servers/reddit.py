#!/usr/bin/env python3
"""
Boxing Reddit MCP Server

Provides Reddit social media analysis for boxing discussions.
Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Reddit API configuration - REQUIRED
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "boxing-mcp-server/1.0")

# Default boxing subreddits to search
BOXING_SUBREDDITS = [
    "Boxing",
    "amateur_boxing",
    "boxingdiscussion",
    "fightporn",
    "sports",
    "MMA",
    "JoeRogan",
    "videos",         
    "PublicFreakout" 
]


def validate_reddit_credentials():
    """Validate that Reddit API credentials are set - REQUIRED for operations."""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise ValueError(
            "Reddit API credentials are REQUIRED. "
            "This server does not provide demo/fake data. "
            "\n\nSetup instructions:"
            "\n1. Go to: https://www.reddit.com/prefs/apps"
            "\n2. Create an app (choose 'script' type)"
            "\n3. Set environment variables:"
            "\n   export REDDIT_CLIENT_ID='your_client_id'"
            "\n   export REDDIT_CLIENT_SECRET='your_client_secret'"
            "\n   export REDDIT_USER_AGENT='boxing-analyzer/1.0 by /u/yourusername'"
        )


async def get_reddit_client():
    """Get authenticated Reddit client using PRAW."""
    validate_reddit_credentials()
    
    try:
        import praw
    except ImportError:
        raise ValueError(
            "PRAW library not installed. "
            "Install with: pip install praw"
        )
    
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
        check_for_async=False  # We'll handle async ourselves
    )
    
    return reddit


async def search_boxing_posts(
    query: str,
    subreddit: str = "Boxing",
    time_filter: str = "week",
    limit: int = 100,
    sort: str = "relevance"
) -> Dict[str, Any]:
    """
    Search for boxing-related posts on Reddit.
    
    Args:
        query: Search query (fighter name, event, etc.)
        subreddit: Subreddit to search (default: Boxing)
        time_filter: Time period - hour, day, week, month, year, all
        limit: Maximum number of posts to return (1-100)
        sort: Sort by - relevance, hot, top, new, comments
    
    Returns:
        Search results with post details and metadata
    """
    validate_reddit_credentials()
    
    reddit = await get_reddit_client()
    
    try:
        # Search the subreddit
        subreddit_obj = reddit.subreddit(subreddit)
        results = subreddit_obj.search(
            query=query,
            sort=sort,
            time_filter=time_filter,
            limit=limit
        )
        
        posts = []
        for submission in results:
            # Get top comments (limited to avoid rate limits)
            submission.comments.replace_more(limit=0)
            top_comments = []
            for comment in submission.comments[:5]:  # Top 5 comments
                top_comments.append({
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "body": comment.body[:500],  # Truncate long comments
                    "score": comment.score,
                    "created_utc": datetime.fromtimestamp(comment.created_utc).isoformat()
                })
            
            posts.append({
                "title": submission.title,
                "author": str(submission.author) if submission.author else "[deleted]",
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "num_comments": submission.num_comments,
                "created_utc": datetime.fromtimestamp(submission.created_utc).isoformat(),
                "url": f"https://reddit.com{submission.permalink}",
                "selftext": submission.selftext[:1000] if submission.selftext else "",  # Truncate
                "is_video": submission.is_video,
                "top_comments": top_comments,
                "flair": submission.link_flair_text
            })
        
        return {
            "query": query,
            "subreddit": subreddit,
            "time_filter": time_filter,
            "total_posts": len(posts),
            "posts": posts,
            "search_params": {
                "sort": sort,
                "limit": limit
            }
        }
        
    except Exception as e:
        raise ValueError(f"Reddit search failed: {str(e)}")


async def get_hot_boxing_posts(
    subreddit: str = "Boxing",
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get hot/trending posts from boxing subreddits.
    
    Args:
        subreddit: Subreddit name (default: Boxing)
        limit: Number of posts to fetch (1-100)
    
    Returns:
        Hot posts with engagement metrics
    """
    validate_reddit_credentials()
    
    reddit = await get_reddit_client()
    
    try:
        subreddit_obj = reddit.subreddit(subreddit)
        hot_posts = subreddit_obj.hot(limit=limit)
        
        posts = []
        for submission in hot_posts:
            # Get sample comments
            submission.comments.replace_more(limit=0)
            comment_sample = []
            for comment in submission.comments[:3]:
                comment_sample.append({
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "body": comment.body[:300],
                    "score": comment.score
                })
            
            posts.append({
                "title": submission.title,
                "author": str(submission.author) if submission.author else "[deleted]",
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "num_comments": submission.num_comments,
                "created_utc": datetime.fromtimestamp(submission.created_utc).isoformat(),
                "url": f"https://reddit.com{submission.permalink}",
                "selftext": submission.selftext[:500] if submission.selftext else "",
                "gilded": submission.gilded,
                "distinguished": submission.distinguished,
                "stickied": submission.stickied,
                "comment_sample": comment_sample,
                "flair": submission.link_flair_text
            })
        
        return {
            "subreddit": subreddit,
            "total_posts": len(posts),
            "posts": posts,
            "fetch_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise ValueError(f"Failed to fetch hot posts: {str(e)}")


async def get_fighter_mentions(
    fighter_name: str,
    days_back: int = 7,
    min_score: int = 5,
    subreddits: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Search for mentions of a specific fighter across boxing subreddits.
    
    Args:
        fighter_name: Fighter's name to search for
        days_back: How many days to look back
        min_score: Minimum post score to include
        subreddits: List of subreddits to search (default: BOXING_SUBREDDITS)
    
    Returns:
        Aggregated mentions with sentiment indicators
    """
    validate_reddit_credentials()
    
    if subreddits is None:
        subreddits = BOXING_SUBREDDITS
    
    reddit = await get_reddit_client()
    
    all_mentions = []
    
    try:
        # Calculate time threshold
        time_threshold = datetime.now() - timedelta(days=days_back)
        
        for subreddit_name in subreddits:
            try:
                subreddit_obj = reddit.subreddit(subreddit_name)
                
                # Search for fighter name
                results = subreddit_obj.search(
                    query=fighter_name,
                    time_filter="week" if days_back <= 7 else "month",
                    limit=50
                )
                
                for submission in results:
                    created_time = datetime.fromtimestamp(submission.created_utc)
                    
                    # Filter by time and score
                    if created_time >= time_threshold and submission.score >= min_score:
                        all_mentions.append({
                            "subreddit": subreddit_name,
                            "title": submission.title,
                            "author": str(submission.author) if submission.author else "[deleted]",
                            "score": submission.score,
                            "upvote_ratio": submission.upvote_ratio,
                            "num_comments": submission.num_comments,
                            "created_utc": created_time.isoformat(),
                            "url": f"https://reddit.com{submission.permalink}",
                            "text_preview": submission.selftext[:300] if submission.selftext else ""
                        })
            
            except Exception as e:
                # Continue with other subreddits if one fails
                print(f"Warning: Failed to search {subreddit_name}: {e}", file=sys.stderr)
                continue
        
        # Sort by score
        all_mentions.sort(key=lambda x: x['score'], reverse=True)
        
        # Calculate aggregate metrics
        total_score = sum(m['score'] for m in all_mentions)
        avg_score = total_score / len(all_mentions) if all_mentions else 0
        total_comments = sum(m['num_comments'] for m in all_mentions)
        avg_upvote_ratio = sum(m['upvote_ratio'] for m in all_mentions) / len(all_mentions) if all_mentions else 0
        
        return {
            "fighter": fighter_name,
            "search_period_days": days_back,
            "total_mentions": len(all_mentions),
            "subreddits_searched": subreddits,
            "aggregate_metrics": {
                "total_score": total_score,
                "average_score": round(avg_score, 2),
                "total_comments": total_comments,
                "average_upvote_ratio": round(avg_upvote_ratio, 3)
            },
            "mentions": all_mentions[:100],  # Limit to top 100
            "analysis": {
                "engagement_level": "High" if avg_score > 100 else "Medium" if avg_score > 50 else "Low",
                "sentiment_indicator": "Positive" if avg_upvote_ratio > 0.75 else "Mixed" if avg_upvote_ratio > 0.5 else "Controversial"
            }
        }
        
    except Exception as e:
        raise ValueError(f"Failed to search for fighter mentions: {str(e)}")


async def compare_fighter_buzz(
    fighter1: str,
    fighter2: str,
    days_back: int = 7
) -> Dict[str, Any]:
    """
    Compare Reddit buzz between two fighters.
    
    Args:
        fighter1: First fighter name
        fighter2: Second fighter name
        days_back: Days to look back
    
    Returns:
        Comparison of social media buzz
    """
    validate_reddit_credentials()
    
    # Get mentions for both fighters
    mentions1 = await get_fighter_mentions(fighter1, days_back)
    mentions2 = await get_fighter_mentions(fighter2, days_back)
    
    # Compare metrics
    score1 = mentions1['aggregate_metrics']['total_score']
    score2 = mentions2['aggregate_metrics']['total_score']
    
    count1 = mentions1['total_mentions']
    count2 = mentions2['total_mentions']
    
    comments1 = mentions1['aggregate_metrics']['total_comments']
    comments2 = mentions2['aggregate_metrics']['total_comments']
    
    # Determine leader
    if count1 > count2:
        leader = fighter1
        advantage_pct = ((count1 - count2) / count2 * 100) if count2 > 0 else 100
    elif count2 > count1:
        leader = fighter2
        advantage_pct = ((count2 - count1) / count1 * 100) if count1 > 0 else 100
    else:
        leader = "Tied"
        advantage_pct = 0
    
    return {
        "fighter1": fighter1,
        "fighter2": fighter2,
        "analysis_period": f"Last {days_back} days",
        "comparison": {
            fighter1: {
                "total_mentions": count1,
                "total_score": score1,
                "total_comments": comments1,
                "avg_score": mentions1['aggregate_metrics']['average_score'],
                "sentiment": mentions1['analysis']['sentiment_indicator'],
                "top_posts": [m['title'] for m in mentions1['mentions'][:3]]
            },
            fighter2: {
                "total_mentions": count2,
                "total_score": score2,
                "total_comments": comments2,
                "avg_score": mentions2['aggregate_metrics']['average_score'],
                "sentiment": mentions2['analysis']['sentiment_indicator'],
                "top_posts": [m['title'] for m in mentions2['mentions'][:3]]
            }
        },
        "verdict": {
            "reddit_buzz_leader": leader,
            "mention_advantage": f"{advantage_pct:.1f}%",
            "interpretation": (
                f"{leader} has {advantage_pct:.0f}% more Reddit mentions" 
                if leader != "Tied" 
                else "Equal Reddit presence"
            )
        }
    }


async def get_community_sentiment(
    topic: str,
    subreddit: str = "Boxing",
    limit: int = 100
) -> Dict[str, Any]:
    """
    Analyze community sentiment on a topic from comments and posts.
    
    Args:
        topic: Topic to analyze (fighter, event, etc.)
        subreddit: Subreddit to analyze
        limit: Number of posts to analyze
    
    Returns:
        Sentiment analysis from community discussions
    """
    validate_reddit_credentials()
    
    reddit = await get_reddit_client()
    
    try:
        subreddit_obj = reddit.subreddit(subreddit)
        results = subreddit_obj.search(topic, time_filter="month", limit=limit)
        
        posts_analyzed = 0
        positive_indicators = 0
        negative_indicators = 0
        neutral_posts = 0
        total_engagement = 0
        
        sample_positive = []
        sample_negative = []
        
        # Simple sentiment indicators (should be enhanced with NLP later)
        positive_words = ['great', 'amazing', 'best', 'incredible', 'fantastic', 'love', 'impressive', 'dominant', 'skilled']
        negative_words = ['terrible', 'worst', 'boring', 'overrated', 'disappointing', 'weak', 'lost', 'bad', 'poor']
        
        for submission in results:
            posts_analyzed += 1
            total_engagement += submission.score + submission.num_comments
            
            # Analyze title and text for sentiment
            text = (submission.title + " " + submission.selftext).lower()
            
            pos_count = sum(1 for word in positive_words if word in text)
            neg_count = sum(1 for word in negative_words if word in text)
            
            if pos_count > neg_count:
                positive_indicators += 1
                if len(sample_positive) < 3:
                    sample_positive.append(submission.title)
            elif neg_count > pos_count:
                negative_indicators += 1
                if len(sample_negative) < 3:
                    sample_negative.append(submission.title)
            else:
                neutral_posts += 1
        
        # Calculate sentiment score
        if posts_analyzed > 0:
            positive_pct = (positive_indicators / posts_analyzed) * 100
            negative_pct = (negative_indicators / posts_analyzed) * 100
            neutral_pct = (neutral_posts / posts_analyzed) * 100
        else:
            positive_pct = negative_pct = neutral_pct = 0
        
        # Determine overall sentiment
        if positive_pct > 50:
            overall_sentiment = "Positive"
        elif negative_pct > 50:
            overall_sentiment = "Negative"
        elif positive_pct > negative_pct:
            overall_sentiment = "Mostly Positive"
        elif negative_pct > positive_pct:
            overall_sentiment = "Mostly Negative"
        else:
            overall_sentiment = "Neutral/Mixed"
        
        return {
            "topic": topic,
            "subreddit": subreddit,
            "posts_analyzed": posts_analyzed,
            "sentiment_breakdown": {
                "positive_percentage": round(positive_pct, 1),
                "negative_percentage": round(negative_pct, 1),
                "neutral_percentage": round(neutral_pct, 1)
            },
            "overall_sentiment": overall_sentiment,
            "total_engagement": total_engagement,
            "sample_posts": {
                "positive": sample_positive,
                "negative": sample_negative
            },
            "note": "Sentiment analysis uses keyword matching. For more accurate results, consider using NLP libraries."
        }
        
    except Exception as e:
        raise ValueError(f"Sentiment analysis failed: {str(e)}")


# Create MCP server
app = Server("boxing-reddit")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Reddit boxing analysis tools."""
    
    return [
        Tool(
            name="search_boxing_posts",
            description=(
                "Search Reddit for boxing-related posts. "
                "Requires Reddit API credentials (checked when called). "
                "Returns posts with titles, scores, comments, and engagement metrics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (fighter name, event, matchup)"
                    },
                    "subreddit": {
                        "type": "string",
                        "description": "Subreddit to search (default: Boxing)",
                        "default": "Boxing"
                    },
                    "time_filter": {
                        "type": "string",
                        "description": "Time period: hour, day, week, month, year, all",
                        "default": "week"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max posts to return (1-100)",
                        "default": 25
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort by: relevance, hot, top, new, comments",
                        "default": "relevance"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_hot_boxing_posts",
            description=(
                "Get hot/trending posts from boxing subreddits. "
                "Requires Reddit API credentials (checked when called). "
                "Shows what's currently popular in the boxing community."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "subreddit": {
                        "type": "string",
                        "description": "Subreddit name",
                        "default": "Boxing"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of posts (1-100)",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="get_fighter_mentions",
            description=(
                "Search for mentions of a specific fighter across boxing subreddits. "
                "Requires Reddit API credentials (checked when called). "
                "Aggregates mentions with engagement metrics and sentiment indicators."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fighter_name": {
                        "type": "string",
                        "description": "Fighter's name to search for"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Days to look back (1-30)",
                        "default": 7
                    },
                    "min_score": {
                        "type": "integer",
                        "description": "Minimum post score to include",
                        "default": 10
                    }
                },
                "required": ["fighter_name"]
            }
        ),
        Tool(
            name="compare_fighter_buzz",
            description=(
                "Compare Reddit buzz between two fighters. "
                "Requires Reddit API credentials (checked when called). "
                "Shows which fighter has more social media presence and engagement."
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
                        "description": "Days to analyze (1-30)",
                        "default": 7
                    }
                },
                "required": ["fighter1", "fighter2"]
            }
        ),
        Tool(
            name="get_community_sentiment",
            description=(
                "Analyze community sentiment on a boxing topic from Reddit discussions. "
                "Requires Reddit API credentials (checked when called). "
                "Uses keyword-based sentiment analysis on posts and comments."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to analyze (fighter, event, etc.)"
                    },
                    "subreddit": {
                        "type": "string",
                        "description": "Subreddit to analyze",
                        "default": "Boxing"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Posts to analyze (1-100)",
                        "default": 50
                    }
                },
                "required": ["topic"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a Reddit analysis tool - ALL require real API data."""
    try:
        if name == "search_boxing_posts":
            result = await search_boxing_posts(
                query=arguments["query"],
                subreddit=arguments.get("subreddit", "Boxing"),
                time_filter=arguments.get("time_filter", "week"),
                limit=arguments.get("limit", 25),
                sort=arguments.get("sort", "relevance")
            )
        
        elif name == "get_hot_boxing_posts":
            result = await get_hot_boxing_posts(
                subreddit=arguments.get("subreddit", "Boxing"),
                limit=arguments.get("limit", 25)
            )
        
        elif name == "get_fighter_mentions":
            result = await get_fighter_mentions(
                fighter_name=arguments["fighter_name"],
                days_back=arguments.get("days_back", 7),
                min_score=arguments.get("min_score", 10)
            )
        
        elif name == "compare_fighter_buzz":
            result = await compare_fighter_buzz(
                fighter1=arguments["fighter1"],
                fighter2=arguments["fighter2"],
                days_back=arguments.get("days_back", 7)
            )
        
        elif name == "get_community_sentiment":
            result = await get_community_sentiment(
                topic=arguments["topic"],
                subreddit=arguments.get("subreddit", "Boxing"),
                limit=arguments.get("limit", 50)
            )
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    except ValueError as e:
        # Return error
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "message": "This server requires real Reddit API credentials. No demo/fake data is provided."
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