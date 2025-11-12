#!/usr/bin/env python3
"""
Diagnostic script to test MCP adapter connections individually
"""

import asyncio
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient


async def test_server(name, config):
    """Test a single server connection."""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")
    print(f"Config: {config}")
    
    try:
        client = MultiServerMCPClient({name: config})
        print("✅ Client created")
        
        tools = await client.get_tools()
        print(f"✅ Tools loaded: {len(tools)}")
        
        for tool in tools:
            print(f"   • {tool.name}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test each server individually."""
    project_root = Path.cwd()
    
    print("\n" + "="*70)
    print("MCP ADAPTER DIAGNOSTIC TEST")
    print("="*70)
    
    # Test 1: Boxing Analytics (stdio)
    success1 = await test_server(
        "boxing_analytics",
        {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_data.py")],
        }
    )
    
    # Test 2: Betting Odds (stdio - not HTTP!)
    success2 = await test_server(
        "betting_odds",
        {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_odds.py")],
        }
    )
    
    # Test 3: Fight News (stdio)
    success3 = await test_server(
        "fight_news",
        {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_news.py")],
        }
    )
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Boxing Analytics: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Betting & Odds:   {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"Fight News:       {'✅ PASS' if success3 else '❌ FAIL'}")
    
    if success1 and success2 and success3:
        print("\n✅ All servers working! Main platform should work.")
    else:
        print("\n❌ Some servers failed. Fix these before running main platform.")


if __name__ == "__main__":
    asyncio.run(main())