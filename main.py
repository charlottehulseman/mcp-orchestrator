#!/usr/bin/env python3
"""
Boxing Intelligence Platform
Multi-server MCP system with LangChain orchestration
"""

import asyncio
import os
import time
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, ToolMessage
from dotenv import load_dotenv

load_dotenv()

# Optional observability
try:
    from observability.monitoring import setup_langsmith, get_monitor
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False


async def setup_platform():
    """Initialize the Boxing Intelligence Platform with all MCP servers."""
    print("\n" + "="*70)
    print("BOXING INTELLIGENCE PLATFORM")
    print("="*70)
    
    project_root = Path(__file__).parent
    
    # Configure MCP servers
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
    
    print("\nInitializing servers...")
    client = MultiServerMCPClient(server_config)
    
    print("Loading tools...")
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} tools from {len(server_config)} servers")
    
    # Create Claude agent
    model = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    agent = model.bind_tools(tools)
    
    print("="*70)
    print("Platform ready\n")
    
    return client, tools, agent


async def execute_query(query: str, agent, tools):
    """Execute a query using the agent and tools."""
    
    if OBSERVABILITY_AVAILABLE:
        get_monitor().log_query(query)
    
    tool_map = {tool.name: tool for tool in tools}
    messages = [HumanMessage(content=query)]
    
    while True:
        response = await agent.ainvoke(messages)
        messages.append(response)
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                start_time = time.time()
                tool = tool_map.get(tool_name)
                result = await tool.ainvoke(tool_args) if tool else f"Error: Tool {tool_name} not found"
                
                if OBSERVABILITY_AVAILABLE:
                    duration_ms = (time.time() - start_time) * 1000
                    get_monitor().log_tool_call(tool_name, duration_ms)
                
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call['id']))
        else:
            break
    
    return response.content


async def demo_simple_query(agent, tools):
    """Demo: Simple single-server query."""
    print("\n" + "="*70)
    print("DEMO 1: Simple Query")
    print("="*70)
    
    query = "What are Tyson Fury's career stats?"
    print(f"\nQuery: {query}\n")
    
    result = await execute_query(query, agent, tools)
    
    print("Response:")
    print("-" * 70)
    print(result)
    print("-" * 70)


async def demo_reddit_query(agent, tools):
    """Demo: Reddit social media analysis."""
    print("\n" + "="*70)
    print("DEMO 2: Reddit Social Media Analysis")
    print("="*70)
    
    query = """What's the Reddit community sentiment on Tyson Fury? 
    Compare his Reddit buzz to Oleksandr Usyk and provide a social media intelligence report."""
    
    print(f"\nQuery: Reddit sentiment analysis\n")
    
    result = await execute_query(query, agent, tools)
    
    print("Response:")
    print("-" * 70)
    print(result)
    print("-" * 70)


async def demo_multi_server_query(agent, tools):
    """Demo: Complex multi-server query."""
    print("\n" + "="*70)
    print("DEMO 3: Multi-Server Query")
    print("="*70)
    
    query = """Complete intelligence analysis for Tyson Fury vs Anthony Joshua:
    1. Compare their fighter statistics and career trajectories
    2. Check current betting odds and value opportunities
    3. What's the news media saying about each fighter?
    4. What's the Reddit community sentiment and buzz comparison?
    5. Provide a comprehensive decision recommendation"""
    
    print(f"\nQuery: Complete multi-source analysis\n")
    
    result = await execute_query(query, agent, tools)
    
    print("Response:")
    print("-" * 70)
    print(result)
    print("-" * 70)


async def interactive_mode(agent, tools):
    """Interactive query mode."""
    print("\n" + "="*70)
    print("INTERACTIVE MODE")
    print("="*70)
    print("\nType your questions or 'quit' to exit.")
    print("\nExample queries:")
    print("  - Should I bet on Canelo vs Benavidez?")
    print("  - Compare Reddit sentiment: Fury vs Usyk")
    print("  - What are people saying about Crawford on Reddit?")
    print()
    
    while True:
        try:
            query = input("Query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nExiting...")
                if OBSERVABILITY_AVAILABLE:
                    get_monitor().print_summary()
                break
            
            if not query:
                continue
            
            print()
            result = await execute_query(query, agent, tools)
            
            print("\nResponse:")
            print("-" * 70)
            print(result)
            print("-" * 70)
            print()
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            if OBSERVABILITY_AVAILABLE:
                get_monitor().print_summary()
            break
        except Exception as e:
            print(f"\nError: {e}\n")


async def main():
    """Main entry point."""
    
    # Setup observability
    if OBSERVABILITY_AVAILABLE:
        print("\nSetting up observability...")
        setup_langsmith()
    
    # Pre-flight checks
    print("\nPre-flight checks:")
    
    checks_passed = True
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("  [FAIL] ANTHROPIC_API_KEY not set")
        checks_passed = False
    else:
        print("  [OK] ANTHROPIC_API_KEY")
    
    if os.getenv("ODDS_API_KEY"):
        print("  [OK] ODDS_API_KEY")
    else:
        print("  [WARN] ODDS_API_KEY not set (limited betting features)")
    
    if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
        print("  [OK] REDDIT_CLIENT_ID/SECRET")
    else:
        print("  [WARN] Reddit API not set (limited social features)")
    
    if os.getenv("NEWS_API_KEY"):
        print("  [OK] NEWS_API_KEY")
    else:
        print("  [WARN] NEWS_API_KEY not set (limited news features)")
    
    if Path("data/boxing_data.db").exists():
        print("  [OK] Boxing database")
    else:
        print("  [WARN] Boxing database not found")
    
    if not checks_passed:
        print("\nCritical checks failed. Exiting.")
        return
    
    # Setup platform
    try:
        client, tools, agent = await setup_platform()
    except Exception as e:
        print(f"\nFailed to setup platform: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Run mode selection
    print("\nSelect mode:")
    print("  1 - Run all demos")
    print("  2 - Interactive mode")
    print("  3 - Reddit demo only")
    print("  4 - Multi-server demo only")
    
    choice = input("\nChoice (1-4, default=1): ").strip() or "1"
    
    if choice == "2":
        await interactive_mode(agent, tools)
    elif choice == "3":
        await demo_reddit_query(agent, tools)
        if OBSERVABILITY_AVAILABLE:
            get_monitor().print_summary()
    elif choice == "4":
        await demo_multi_server_query(agent, tools)
        if OBSERVABILITY_AVAILABLE:
            get_monitor().print_summary()
    else:
        await demo_simple_query(agent, tools)
        await demo_reddit_query(agent, tools)
        await demo_multi_server_query(agent, tools)
        
        if OBSERVABILITY_AVAILABLE:
            get_monitor().print_summary()
        
        cont = input("\nTry interactive mode? (y/n): ").strip().lower()
        if cont == 'y':
            await interactive_mode(agent, tools)


if __name__ == "__main__":
    asyncio.run(main())