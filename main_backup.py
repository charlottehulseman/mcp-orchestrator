#!/usr/bin/env python3
"""
Boxing Intelligence Platform - Main Integration
Complete multi-server MCP system with LangChain orchestration and observability
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
    Initialize the Boxing Intelligence Platform with all three servers.
    
    Returns:
        tuple: (client, tools, agent) ready for queries
    """
    print("\n" + "="*70)
    print("🥊 BOXING INTELLIGENCE PLATFORM")
    print("="*70)
    print("\n Initializing multi-server system...\n")
    
    # Get project root
    project_root = Path(__file__).parent
    
    # Configure all three boxing servers - ALL USING STDIO
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
        }
    }
    
    print("   Connecting to servers:")
    print("   Boxing Analytics (stdio)")
    print("   Betting & Odds (stdio)")
    print("   Fight News (stdio)")
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
    analytics_tools = [t for t in tools if any(x in t.name for x in ['fighter', 'compare', 'career', 'upcoming'])]
    odds_tools = [t for t in tools if any(x in t.name for x in ['odds', 'betting', 'predict', 'value', 'trend'])]
    news_tools = [t for t in tools if any(x in t.name for x in ['news', 'social', 'hype', 'prediction', 'press'])]
    
    if analytics_tools:
        print(f"\n   Boxing Analytics ({len(analytics_tools)} tools):")
        for tool in analytics_tools[:3]:
            print(f"      • {tool.name}")
    
    if odds_tools:
        print(f"\n   Betting & Odds ({len(odds_tools)} tools):")
        for tool in odds_tools[:3]:
            print(f"      • {tool.name}")
    
    if news_tools:
        print(f"\n   Fight News ({len(news_tools)} tools):")
        for tool in news_tools[:3]:
            print(f"      • {tool.name}")
    
    print(f"\n   ... and {len(tools) - len(analytics_tools) - len(odds_tools) - len(news_tools)} more")
    
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


async def demo_multi_server_query(agent, tools):
    """Run a complex multi-server query."""
    print("\n" + "="*70)
    print("DEMO 2: Multi-Server Query (All Three Servers)")
    print("="*70)
    
    query = """
Analyze the Tyson Fury vs Anthony Joshua fight for a betting decision:

1. Compare their fighter statistics and recent performance
2. Check the current betting odds and calculate if there's value
3. What does the media and experts say about each fighter?
4. Give me a comprehensive betting recommendation

Use all available intelligence sources.
    """
    
    print(f"\nQuery: Multi-server fight analysis")
    print("="*70)
    print(query.strip())
    print("="*70)
    print("\nAgent orchestrating across all servers...\n")
    
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
    
    print("Intelligence Report:")
    print("="*70)
    print(response.content)
    print("="*70)


async def interactive_mode(agent, tools):
    """Run interactive query mode."""
    print("\n" + "="*70)
    print("Interactive mode:")
    print("="*70)
    print("\nAsk questions using all 3 servers.")
    print("Type 'quit' or 'exit' to stop.\n")
    print("Example queries:")
    print("  • 'Should I bet on Canelo vs Benavidez?'")
    print("  • 'Compare the media hype of Fury and Joshua'")
    print("  • 'Find value bets in upcoming fights'")
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
            print("\n\n Thanks for using the Boxing Intelligence Platform!")
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
        print("   ⚠️  ODDS_API_KEY not set (using demo data)")
    
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
        print("  2. Dependencies installed: pip install langchain-mcp-adapters langchain-anthropic")
        print("  3. Database exists: python scripts/init_boxing_db.py")
        print("  4. HTTP server is running: python mcp_servers/boxing_odds.py")
        return
    
    # Run demos or interactive mode
    print("Choose mode:")
    print("  1. Run demos (simple + multi-server queries)")
    print("  2. Interactive mode (ask your own questions)")
    print("  3. Quick test (one multi-server query)")
    
    choice = input("\nEnter choice (1/2/3) or press Enter for demos: ").strip()
    
    if choice == "2":
        await interactive_mode(agent, tools)
    elif choice == "3":
        await demo_multi_server_query(agent, tools)
        # Show performance summary if observability is available
        if OBSERVABILITY_AVAILABLE:
            monitor = get_monitor()
            monitor.print_summary()
    else:
        # Run both demos
        await demo_simple_query(agent, tools)
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