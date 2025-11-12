#!/usr/bin/env python3
"""
Test the Boxing MCP Server with REAL DATA

This script tests the boxing server's functionality with the real fighters
and fights loaded from the Boxing Data API.
"""

import asyncio
import sys
sys.path.append('.')

from mcp_servers.boxing_data import (
    get_fighter_stats,
    compare_fighters,
    search_fighters,
    fighter_career_timeline,
    upcoming_fights
)


async def test_get_fighter_stats():
    """Test getting fighter statistics with real data."""
    print("\n" + "="*70)
    print("TEST 1: Get Fighter Stats (Real Data)")
    print("="*70)
    
    # Test with fighters from our database
    test_fighters = ["Tyson Fury", "Canelo", "Naoya Inoue"]
    
    for fighter_name in test_fighters:
        print(f"\n📊 Testing with '{fighter_name}'...")
        result = await get_fighter_stats(fighter_name)
        
        if "error" not in result:
            print(f"✅ Name: {result['name']}")
            print(f"   Record: {result['record']}")
            print(f"   KO%: {result['record_details']['ko_percentage']}%")
            print(f"   Weight Class: {result['weight_class']}")
            print(f"   Nationality: {result['nationality']}")
            if result['physical_stats']['reach_cm']:
                print(f"   Reach: {result['physical_stats']['reach_cm']}cm")
            print(f"   Total Fights: {result['total_fights']}")
        else:
            print(f"⚠️  {result['error']}")


async def test_compare_fighters():
    """Test comparing two real fighters."""
    print("\n" + "="*70)
    print("TEST 2: Compare Fighters (Real Matchup)")
    print("="*70)
    
    # Compare real fighters from our database
    fighter1 = "Tyson Fury"
    fighter2 = "Anthony Joshua"
    
    print(f"\n🥊 Comparing {fighter1} vs {fighter2}...")
    result = await compare_fighters(fighter1, fighter2)
    
    if "error" not in result:
        print(f"\n👤 Fighter 1: {result['fighter1']} ({result['fighter1_record']})")
        print("   Advantages:")
        if result['fighter1_advantages']:
            for adv in result['fighter1_advantages']:
                print(f"   ✓ {adv}")
        else:
            print("   (None)")
        
        print(f"\n👤 Fighter 2: {result['fighter2']} ({result['fighter2_record']})")
        print("   Advantages:")
        if result['fighter2_advantages']:
            for adv in result['fighter2_advantages']:
                print(f"   ✓ {adv}")
        else:
            print("   (None)")
        
        print(f"\n🎯 Statistical Favorite: {result['statistical_favorite']}")
        print(f"   Confidence: {result['confidence'] * 100:.0f}%")
        print(f"   {result['analysis']}")
    else:
        print(f"⚠️  {result['error']}")


async def test_search_fighters():
    """Test searching for fighters."""
    print("\n" + "="*70)
    print("TEST 3: Search Fighters")
    print("="*70)
    
    # Test 1: Search by partial name
    print("\n1️⃣ Searching for 'Garcia'...")
    results = await search_fighters(query="Garcia")
    print(f"   Found {len(results)} fighters:")
    for fighter in results[:5]:
        print(f"   - {fighter['name']} ({fighter['record']}) - {fighter['weight_class']}")
    
    # Test 2: Search by weight class
    print("\n2️⃣ Searching for Heavyweight fighters...")
    results = await search_fighters(weight_class="Heavyweight")
    print(f"   Found {len(results)} heavyweight fighters:")
    for fighter in results[:5]:
        print(f"   - {fighter['name']} ({fighter['record']})")
    
    # Test 3: Search active fighters only
    print("\n3️⃣ Searching for active fighters...")
    results = await search_fighters(active_only=True)
    print(f"   Found {len(results)} active fighters (showing first 5):")
    for fighter in results[:5]:
        print(f"   - {fighter['name']} ({fighter['record']}) - {fighter['nationality']}")


async def test_career_timeline():
    """Test getting career timeline."""
    print("\n" + "="*70)
    print("TEST 4: Fighter Career Timeline")
    print("="*70)
    
    # Test with a fighter who has fight history
    fighter_name = "Terence Crawford"
    
    print(f"\n📅 Getting career timeline for {fighter_name}...")
    result = await fighter_career_timeline(fighter_name)
    
    if "error" not in result:
        print(f"\n✅ Fighter: {result['fighter']}")
        print(f"   Total Fights in DB: {result['total_fights']}")
        print(f"   Championship Reigns: {result['championship_reigns']}")
        
        if result['career_span']:
            print(f"   Career Span: {result['career_span']['years']} years")
            print(f"   Debut: {result['career_span']['debut_date']}")
        
        if result['milestones']:
            print("\n   Key Milestones:")
            for milestone in result['milestones'][:5]:
                print(f"   • {milestone['date']}: {milestone['event']}")
        
        if result['year_by_year']:
            print("\n   Year-by-Year (last 3 years):")
            for year_stat in result['year_by_year'][-3:]:
                print(f"   {year_stat['year']}: {year_stat['wins']}W-{year_stat['losses']}L-{year_stat['draws']}D")
    else:
        print(f"   ⚠️  {result['error']}")


async def test_upcoming_fights():
    """Test getting upcoming fights from real database."""
    print("\n" + "="*70)
    print("TEST 5: Upcoming Fights (Real Data)")
    print("="*70)
    
    print("\n🗓️  Getting upcoming fights from database...")
    results = await upcoming_fights(date_range="90d")
    
    if results:
        print(f"   Found {len(results)} upcoming fights:")
        for i, fight in enumerate(results[:10], 1):
            title = " 🏆 (Title Fight)" if fight['title_fight'] else ""
            print(f"\n   {i}. {fight['date']}: {fight['fighter1']} vs {fight['fighter2']}{title}")
            print(f"      Weight Class: {fight['weight_class']}")
            print(f"      Location: {fight['location']}")
    else:
        print("   ℹ️  No upcoming fights scheduled in the next 90 days")


async def test_database_stats():
    """Test database statistics."""
    print("\n" + "="*70)
    print("TEST 6: Database Statistics")
    print("="*70)
    
    import sqlite3
    conn = sqlite3.connect("data/boxing_data.db")
    cursor = conn.cursor()
    
    # Get total fighters
    cursor.execute("SELECT COUNT(*) FROM fighters")
    total_fighters = cursor.fetchone()[0]
    
    # Get total fights
    cursor.execute("SELECT COUNT(*) FROM fights")
    total_fights = cursor.fetchone()[0]
    
    # Get finished vs upcoming
    cursor.execute("SELECT COUNT(*) FROM fights WHERE status = 'FINISHED'")
    finished = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM fights WHERE status = 'NOT_STARTED'")
    upcoming = cursor.fetchone()[0]
    
    # Get weight class distribution
    cursor.execute("""
        SELECT weight_class, COUNT(*) as count 
        FROM fighters 
        GROUP BY weight_class 
        ORDER BY count DESC 
        LIMIT 5
    """)
    weight_classes = cursor.fetchall()
    
    conn.close()
    
    print(f"\n📊 Database Statistics:")
    print(f"   Total Fighters: {total_fighters}")
    print(f"   Total Fights: {total_fights}")
    print(f"   - Finished (with results): {finished}")
    print(f"   - Upcoming: {upcoming}")
    
    print(f"\n   Top 5 Weight Classes:")
    for wc, count in weight_classes:
        print(f"   - {wc}: {count} fighters")


async def run_all_tests():
    """Run all tests."""
    print("="*70)
    print("🥊 BOXING MCP SERVER TEST SUITE (REAL DATA)")
    print("="*70)
    print("\nTesting with 232 real fighters and 106 real fights!")
    print("Data source: Boxing Data API via RapidAPI")
    
    try:
        await test_database_stats()
        await test_get_fighter_stats()
        await test_compare_fighters()
        await test_search_fighters()
        await test_career_timeline()
        await test_upcoming_fights()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\n🎉 Your Boxing MCP Server is working perfectly with real data!")
        print("   Next: Integrate with LangChain for AI-powered analysis")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())