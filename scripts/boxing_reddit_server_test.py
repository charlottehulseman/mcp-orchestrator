#!/usr/bin/env python3
"""
Test script for Reddit MCP Server

Validates Reddit API credentials and tests all tools.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_credentials():
    """Check if Reddit credentials are set."""
    print("🔍 Checking Reddit API Credentials...")
    print("-" * 70)
    
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")
    
    if not client_id:
        print("❌ REDDIT_CLIENT_ID not set")
        return False
    else:
        print(f"✅ REDDIT_CLIENT_ID: {client_id[:6]}...")
    
    if not client_secret:
        print("❌ REDDIT_CLIENT_SECRET not set")
        return False
    else:
        print(f"✅ REDDIT_CLIENT_SECRET: {client_secret[:6]}...")
    
    if not user_agent:
        print("⚠️  REDDIT_USER_AGENT not set (using default)")
    else:
        print(f"✅ REDDIT_USER_AGENT: {user_agent}")
    
    print("-" * 70)
    return bool(client_id and client_secret)


async def test_basic_connection():
    """Test basic Reddit connection."""
    print("\n🔌 Testing Reddit API Connection...")
    print("-" * 70)
    
    try:
        import praw
    except ImportError:
        print("❌ PRAW library not installed")
        print("   Install with: pip install praw")
        return False
    
    try:
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "boxing-test/1.0")
        )
        
        # Test: Get a few posts from r/Boxing
        subreddit = reddit.subreddit("Boxing")
        posts = list(subreddit.hot(limit=3))
        
        print(f"✅ Successfully connected to Reddit API")
        print(f"✅ Retrieved {len(posts)} posts from r/Boxing")
        print("\nSample posts:")
        for i, post in enumerate(posts, 1):
            print(f"   {i}. {post.title[:60]}...")
        
        print("-" * 70)
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("-" * 70)
        return False


async def test_reddit_tools():
    """Test Reddit MCP server tools."""
    print("\n🛠️  Testing Reddit MCP Server Tools...")
    print("-" * 70)
    
    # Import the functions from reddit server
    try:
        from mcp_servers.reddit import (
            search_boxing_posts,
            get_hot_boxing_posts,
            get_fighter_mentions,
            compare_fighter_buzz,
            get_community_sentiment
        )
    except ImportError:
        print("❌ Cannot import reddit server")
        print("   Make sure reddit.py is in mcp_servers/")
        return False
    
    try:
        # Test 1: Search posts
        print("\n📝 Test 1: search_boxing_posts")
        result = await search_boxing_posts(
            query="Tyson Fury",
            subreddit="Boxing",
            limit=5
        )
        print(f"   ✅ Found {result['total_posts']} posts")
        if result['posts']:
            print(f"   Sample: {result['posts'][0]['title'][:60]}...")
        
        # Test 2: Hot posts
        print("\n🔥 Test 2: get_hot_boxing_posts")
        result = await get_hot_boxing_posts(
            subreddit="Boxing",
            limit=5
        )
        print(f"   ✅ Retrieved {result['total_posts']} hot posts")
        if result['posts']:
            print(f"   Top post: {result['posts'][0]['title'][:60]}...")
        
        # Test 3: Fighter mentions
        print("\n👤 Test 3: get_fighter_mentions")
        result = await get_fighter_mentions(
            fighter_name="Canelo",
            days_back=7,
            min_score=5
        )
        print(f"   ✅ Found {result['total_mentions']} mentions")
        print(f"   Engagement: {result['analysis']['engagement_level']}")
        print(f"   Sentiment: {result['analysis']['sentiment_indicator']}")
        
        # Test 4: Compare buzz
        print("\n⚖️  Test 4: compare_fighter_buzz")
        result = await compare_fighter_buzz(
            fighter1="Tyson Fury",
            fighter2="Oleksandr Usyk",
            days_back=7
        )
        print(f"   ✅ Compared buzz for 2 fighters")
        print(f"   Leader: {result['verdict']['reddit_buzz_leader']}")
        
        # Test 5: Sentiment analysis
        print("\n💭 Test 5: get_community_sentiment")
        result = await get_community_sentiment(
            topic="Tyson Fury",
            subreddit="Boxing",
            limit=20
        )
        print(f"   ✅ Analyzed {result['posts_analyzed']} posts")
        print(f"   Overall sentiment: {result['overall_sentiment']}")
        print(f"   Positive: {result['sentiment_breakdown']['positive_percentage']}%")
        print(f"   Negative: {result['sentiment_breakdown']['negative_percentage']}%")
        
        print("-" * 70)
        print("\n✨ All Reddit tools working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        import traceback
        traceback.print_exc()
        print("-" * 70)
        return False


async def test_mcp_server():
    """Test the full MCP server."""
    print("\n🖥️  Testing Full MCP Server...")
    print("-" * 70)
    
    try:
        # This would require running the actual MCP server
        # For now, we just import to check for errors
        from mcp_servers import reddit
        print("✅ Reddit MCP server module loads successfully")
        print("✅ All required dependencies available")
        print("-" * 70)
        return True
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        print("-" * 70)
        return False


async def main():
    """Run all tests."""
    print("="*70)
    print("🥊 BOXING INTELLIGENCE - REDDIT SERVER TEST")
    print("="*70)
    
    # Check credentials
    if not check_credentials():
        print("\n❌ Missing Reddit API credentials")
        print("\nSetup instructions:")
        print("  1. See REDDIT_SETUP.md for detailed guide")
        print("  2. Go to: https://www.reddit.com/prefs/apps")
        print("  3. Create a 'script' app")
        print("  4. Add credentials to .env file:")
        print("     REDDIT_CLIENT_ID=your_client_id")
        print("     REDDIT_CLIENT_SECRET=your_secret")
        print("     REDDIT_USER_AGENT=boxing-app/1.0 by /u/yourname")
        sys.exit(1)
    
    # Test connection
    connection_ok = await test_basic_connection()
    if not connection_ok:
        print("\n❌ Reddit API connection failed")
        print("\nTroubleshooting:")
        print("  1. Verify credentials at: https://www.reddit.com/prefs/apps")
        print("  2. Check for typos in .env file")
        print("  3. Ensure no extra spaces or quotes")
        print("  4. Try recreating the Reddit app")
        sys.exit(1)
    
    # Test tools
    tools_ok = await test_reddit_tools()
    if not tools_ok:
        print("\n⚠️  Some Reddit tools failed")
        print("    The connection works but there may be issues with specific tools")
    
    # Test MCP server
    server_ok = await test_mcp_server()
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Credentials: {'✅' if check_credentials() else '❌'}")
    print(f"Connection:  {'✅' if connection_ok else '❌'}")
    print(f"Tools:       {'✅' if tools_ok else '⚠️'}")
    print(f"MCP Server:  {'✅' if server_ok else '❌'}")
    print("="*70)
    
    if connection_ok and tools_ok and server_ok:
        print("\n🎉 All tests passed! Reddit server is ready to use.")
        print("\nNext steps:")
        print("  1. Run: python main.py")
        print("  2. Try Reddit queries like:")
        print("     - 'What's trending on r/Boxing?'")
        print("     - 'Compare Reddit buzz: Fury vs Usyk'")
        print("     - 'Sentiment analysis on Canelo'")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())