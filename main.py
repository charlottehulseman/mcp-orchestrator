#!/usr/bin/env python3
"""
Boxing Intelligence Platform - Main Integration
Complete multi-server MCP system with LangChain orchestration and observability
NOW WITH REDDIT SOCIAL MEDIA ANALYSIS!
"""

import asyncio
import os
import time
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import observability
try:
    from observability.monitoring import setup_langsmith, get_monitor
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    print("   Observability module not found (optional)")
    print("   Install: cp monitoring.py observability/")


async def setup_boxing_platform():
    """
    Initialize the Boxing Intelligence Platform with ALL FOUR servers.
    
    Returns:
        tuple: (client, tools, agent) ready for queries
    """
    print("\n" + "="*70)
    print("🥊 BOXING INTELLIGENCE PLATFORM")
    print("="*70)
    print("\n Initializing multi-server system...\n")
    
    # Get project root
    project_root = Path(__file__).parent
    
    # Configure all FOUR boxing servers - ALL USING STDIO
    server_config = {
        "boxing_analytics": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_data.py")],
        },
        "betting_odds": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_odds.py")],
        },
        "fight_news": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_news.py")],
        },
        "reddit_social": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "reddit.py")],
        }
    }
    
    print("   Connecting to servers:")
    print("   Boxing Analytics (stdio)")
    print("   Betting & Odds (stdio)")
    print("   Fight News (stdio)")
    print("   Reddit Social Media (stdio) ✨ NEW")
    print()
    
    # Create MCP client
    client = MultiServerMCPClient(server_config)
    
    # Load all tools
    print("🔧 Loading tools from all servers...")
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} tools!\n")
    
    # Show tools by server
    print("📊 Available Tools:")
    
    # Group tools by server (approximate by tool name patterns)
    analytics_tools = [t for t in tools if any(x in t.name for x in ['fighter', 'compare', 'career', 'upcoming', 'trajectory', 'opponent', 'title'])]
    odds_tools = [t for t in tools if any(x in t.name for x in ['odds', 'betting', 'predict', 'value', 'trend'])]
    news_tools = [t for t in tools if any(x in t.name for x in ['news', 'hype', 'prediction', 'press']) and 'reddit' not in t.name.lower()]
    reddit_tools = [t for t in tools if any(x in t.name for x in ['boxing_posts', 'hot_boxing', 'fighter_mentions', 'fighter_buzz', 'community_sentiment'])]
    
    if analytics_tools:
        print(f"\n   Boxing Analytics ({len(analytics_tools)} tools):")
        for tool in analytics_tools[:4]:
            print(f"      • {tool.name}")
    
    if odds_tools:
        print(f"\n   Betting & Odds ({len(odds_tools)} tools):")
        for tool in odds_tools[:3]:
            print(f"      • {tool.name}")
    
    if news_tools:
        print(f"\n   Fight News ({len(news_tools)} tools):")
        for tool in news_tools[:3]:
            print(f"      • {tool.name}")
    
    if reddit_tools:
        print(f"\n   Reddit Social Media ({len(reddit_tools)} tools) ✨ NEW:")
        for tool in reddit_tools:
            print(f"      • {tool.name}")
    
    remaining = len(tools) - len(analytics_tools) - len(odds_tools) - len(news_tools) - len(reddit_tools)
    if remaining > 0:
        print(f"\n   ... and {remaining} more")
    
    # Create Claude agent with all tools
    print("\n🤖 Creating Claude Sonnet 4.5 agent with all tools...")
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0
    )
    agent = model.bind_tools(tools)
    print("Agent ready!\n")
    
    print("="*70)
    print("✨ BOXING INTELLIGENCE PLATFORM READY!")
    print("="*70)
    print()
    
    return client, tools, agent


async def demo_simple_query(agent, tools):
    """Run a simple single-server query."""
    print("\n" + "="*70)
    print("DEMO 1: Simple Query (Single Server)")
    print("="*70)
    
    query = "What are Tyson Fury's career stats?"
    print(f"\nQuery: {query}\n")
    print("Analyzing...\n")
    
    # Track query
    if OBSERVABILITY_AVAILABLE:
        monitor = get_monitor()
        monitor.log_query(query)
    
    # Create tool name -> tool mapping for execution
    tool_map = {tool.name: tool for tool in tools}
    
    messages = [HumanMessage(content=query)]
    
    # Keep invoking until no more tool calls
    while True:
        response = await agent.ainvoke(messages)
        messages.append(response)
        
        # Check if there are tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                # Time tool execution
                start_time = time.time()
                
                # Get the tool and execute it
                tool = tool_map.get(tool_name)
                if tool:
                    result = await tool.ainvoke(tool_args)
                else:
                    result = f"Error: Tool {tool_name} not found"
                
                # Track tool call performance
                if OBSERVABILITY_AVAILABLE:
                    duration_ms = (time.time() - start_time) * 1000
                    monitor.log_tool_call(tool_name, duration_ms)
                
                # Add tool result to messages
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call['id']
                ))
        else:
            break
    
    print("Response:")
    print("-" * 70)
    print(response.content)
    print("-" * 70)


async def demo_reddit_social_query(agent, tools):
    """Run a Reddit social media analysis query."""
    print("\n" + "="*70)
    print("DEMO 2: Reddit Social Media Analysis ✨ NEW")
    print("="*70)
    
    query = """
What's the Reddit community sentiment on Tyson Fury? 

1. Search for recent posts about him
2. Compare his Reddit buzz to Oleksandr Usyk
3. What's the overall community sentiment?

Give me a comprehensive social media intelligence report.
    """
    
    print(f"\nQuery: Reddit sentiment analysis")
    print("="*70)
    print(query.strip())
    print("="*70)
    print("\nAgent analyzing Reddit data...\n")
    
    # Track query
    if OBSERVABILITY_AVAILABLE:
        monitor = get_monitor()
        monitor.log_query(query)
    
    # Create tool name -> tool mapping for execution
    tool_map = {tool.name: tool for tool in tools}
    
    messages = [HumanMessage(content=query)]
    
    # Keep invoking until no more tool calls
    while True:
        response = await agent.ainvoke(messages)
        messages.append(response)
        
        # Check if there are tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                # Time tool execution
                start_time = time.time()
                
                # Get the tool and execute it
                tool = tool_map.get(tool_name)
                if tool:
                    result = await tool.ainvoke(tool_args)
                else:
                    result = f"Error: Tool {tool_name} not found"
                
                # Track tool call performance
                if OBSERVABILITY_AVAILABLE:
                    duration_ms = (time.time() - start_time) * 1000
                    monitor.log_tool_call(tool_name, duration_ms)
                
                # Add tool result to messages
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call['id']
                ))
        else:
            break
    
    print("Reddit Intelligence Report:")
    print("="*70)
    print(response.content)
    print("="*70)


async def demo_multi_server_query(agent, tools):
    """Run a complex multi-server query using ALL FOUR servers."""
    print("\n" + "="*70)
    print("DEMO 3: Multi-Server Query (All Four Servers)")
    print("="*70)
    
    query = """
Complete intelligence analysis for Tyson Fury vs Anthony Joshua:

1. Compare their fighter statistics and career trajectories
2. Check current betting odds and value opportunities
3. What's the news media saying about each fighter?
4. What's the Reddit community sentiment and buzz comparison?
5. Give me a comprehensive decision recommendation

Use ALL available intelligence sources across all four servers.
    """
    
    print(f"\nQuery: Complete multi-source fight analysis")
    print("="*70)
    print(query.strip())
    print("="*70)
    print("\nAgent orchestrating across ALL FOUR servers...\n")
    
    # Track query
    if OBSERVABILITY_AVAILABLE:
        monitor = get_monitor()
        monitor.log_query(query)
    
    # Create tool name -> tool mapping for execution
    tool_map = {tool.name: tool for tool in tools}
    
    messages = [HumanMessage(content=query)]
    
    # Keep invoking until no more tool calls
    while True:
        response = await agent.ainvoke(messages)
        messages.append(response)
        
        # Check if there are tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                # Time tool execution
                start_time = time.time()
                
                # Get the tool and execute it
                tool = tool_map.get(tool_name)
                if tool:
                    result = await tool.ainvoke(tool_args)
                else:
                    result = f"Error: Tool {tool_name} not found"
                
                # Track tool call performance
                if OBSERVABILITY_AVAILABLE:
                    duration_ms = (time.time() - start_time) * 1000
                    monitor.log_tool_call(tool_name, duration_ms)
                
                # Add tool result to messages
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call['id']
                ))
        else:
            # No more tool calls, we have the final answer
            break
    
    print("Complete Intelligence Report:")
    print("="*70)
    print(response.content)
    print("="*70)


async def interactive_mode(agent, tools):
    """Run interactive query mode."""
    print("\n" + "="*70)
    print("Interactive mode:")
    print("="*70)
    print("\nAsk questions using all 4 servers.")
    print("Type 'quit' or 'exit' to stop.\n")
    print("Example queries:")
    print("  • 'Should I bet on Canelo vs Benavidez?'")
    print("  • 'Compare Reddit sentiment: Fury vs Usyk'")
    print("  • 'What are people saying about Crawford on Reddit?'")
    print("  • 'Find value bets with social media confirmation'")
    print()
    
    # Create tool name -> tool mapping for execution
    tool_map = {tool.name: tool for tool in tools}
    
    while True:
        try:
            query = input("Your boxing query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nThanks for using the Boxing Intelligence Platform!")
                # Show performance summary if observability is available
                if OBSERVABILITY_AVAILABLE:
                    monitor = get_monitor()
                    monitor.print_summary()
                break
            
            if not query:
                continue
            
            # Track query
            if OBSERVABILITY_AVAILABLE:
                monitor = get_monitor()
                monitor.log_query(query)
            
            print("\nAnalyzing...\n")
            
            messages = [HumanMessage(content=query)]
            
            # Keep invoking until no more tool calls
            while True:
                response = await agent.ainvoke(messages)
                messages.append(response)
                
                # Check if there are tool calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    # Execute tool calls
                    for tool_call in response.tool_calls:
                        tool_name = tool_call['name']
                        tool_args = tool_call['args']
                        
                        # Time tool execution
                        start_time = time.time()
                        
                        # Get the tool and execute it
                        tool = tool_map.get(tool_name)
                        if tool:
                            result = await tool.ainvoke(tool_args)
                        else:
                            result = f"Error: Tool {tool_name} not found"
                        
                        # Track tool call performance
                        if OBSERVABILITY_AVAILABLE:
                            duration_ms = (time.time() - start_time) * 1000
                            monitor.log_tool_call(tool_name, duration_ms)
                        
                        # Add tool result to messages
                        from langchain_core.messages import ToolMessage
                        messages.append(ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call['id']
                        ))
                else:
                    # No more tool calls, we have the final answer
                    break
            
            print("Response:")
            print("-" * 70)
            print(response.content)
            print("-" * 70)
            print()
            
        except KeyboardInterrupt:
            print("\n\nThanks for using the Boxing Intelligence Platform!")
            # Show performance summary if observability is available
            if OBSERVABILITY_AVAILABLE:
                monitor = get_monitor()
                monitor.print_summary()
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            if OBSERVABILITY_AVAILABLE:
                monitor = get_monitor()
                monitor.log_error(str(e), {"query": query})


async def main():
    """Main entry point."""
    
    # Setup observability (LangSmith)
    print("\n🔍 Checking observability setup...")
    if OBSERVABILITY_AVAILABLE:
        setup_langsmith()
    print()
    
    # Pre-flight checks
    print("\n📋 Pre-flight Checks:")
    
    # Check ANTHROPIC_API_KEY
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("   ❌ ANTHROPIC_API_KEY not set!")
        print("      Set with: export ANTHROPIC_API_KEY='your_key_here'")
        return
    print("   ✅ ANTHROPIC_API_KEY set")
    
    # Check ODDS_API_KEY (optional)
    if os.getenv("ODDS_API_KEY"):
        print("   ✅ ODDS_API_KEY set (live betting data)")
    else:
        print("   ⚠️  ODDS_API_KEY not set (limited betting features)")
    
    # Check REDDIT credentials (optional)
    if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
        print("   ✅ REDDIT_CLIENT_ID/SECRET set (live social media data)")
    else:
        print("   ⚠️  Reddit API not set (see REDDIT_SETUP.md)")
    
    # Check NEWS_API_KEY (optional)
    if os.getenv("NEWS_API_KEY"):
        print("   ✅ NEWS_API_KEY set (live news data)")
    else:
        print("   ⚠️  NEWS_API_KEY not set (limited news features)")
    
    # Check boxing database
    if Path("data/boxing_data.db").exists():
        print("   ✅ Boxing database found (232 fighters)")
    else:
        print("   ⚠️  Boxing database not found")
        print("      Create with: python scripts/init_boxing_db.py")
    
    print()
    
    # Setup platform
    try:
        client, tools, agent = await setup_boxing_platform()
    except Exception as e:
        print(f"\n❌ Failed to setup platform: {e}")
        print(f"\nDetailed error: {type(e).__name__}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        print("\nMake sure:")
        print("  1. All server files exist in mcp_servers/")
        print("  2. Dependencies installed: pip install -r requirements.txt")
        print("  3. Database exists: python scripts/init_boxing_db.py")
        print("  4. Reddit setup complete: see REDDIT_SETUP.md")
        return
    
    # Run demos or interactive mode
    print("Choose mode:")
    print("  1. Run all demos (simple + reddit + multi-server)")
    print("  2. Interactive mode (ask your own questions)")
    print("  3. Reddit demo only")
    print("  4. Multi-server demo only")
    
    choice = input("\nEnter choice (1/2/3/4) or press Enter for all demos: ").strip()
    
    if choice == "2":
        await interactive_mode(agent, tools)
    elif choice == "3":
        await demo_reddit_social_query(agent, tools)
        if OBSERVABILITY_AVAILABLE:
            monitor = get_monitor()
            monitor.print_summary()
    elif choice == "4":
        await demo_multi_server_query(agent, tools)
        if OBSERVABILITY_AVAILABLE:
            monitor = get_monitor()
            monitor.print_summary()
    else:
        # Run all demos
        await demo_simple_query(agent, tools)
        await demo_reddit_social_query(agent, tools)
        await demo_multi_server_query(agent, tools)
        
        # Show performance summary if observability is available
        if OBSERVABILITY_AVAILABLE:
            monitor = get_monitor()
            monitor.print_summary()
        
        # Offer interactive mode
        print("\n" + "="*70)
        cont = input("\nWould you like to try interactive mode? (y/n): ").strip().lower()
        if cont == 'y':
            await interactive_mode(agent, tools)


if __name__ == "__main__":
    asyncio.run(main())