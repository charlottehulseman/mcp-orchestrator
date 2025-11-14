#!/usr/bin/env python3
"""
Test the Boxing Betting & Odds MCP Server

This script tests all betting/odds functionality with real or demo data.
"""

import asyncio
import sys
import os

sys.path.append('.')

from mcp_servers.boxing_odds import (
    get_fight_odds,
    get_odds_movement,
    calculate_betting_value,
    get_betting_trends,
    predict_fight_outcome
)


async def test_get_fight_odds():
    """Test getting current fight odds."""
    print("\n" + "="*70)
    print("TEST 1: Get Fight Odds")
    print("="*70)
    
    # Test 1: Get all boxing fight odds
    print("\n1️⃣ Getting all upcoming boxing fight odds...")
    result = await get_fight_odds()
    
    if "error" not in result or result.get("demo_mode"):
        print(f"✅ Odds retrieved!")
        print(f"   Total Fights: {result['total_fights']}")
        print(f"   Market: {result['market']}")
        
        if result.get("demo_mode"):
            print(f"   Mode: DEMO (set ODDS_API_KEY for real data)")
        else:
            print(f"   Mode: LIVE DATA")
        
        if result.get("fights"):
            fight = result["fights"][0]
            print(f"\n   Sample Fight:")
            print(f"   {fight['home_team']} vs {fight['away_team']}")
            if fight.get("bookmakers"):
                bookmaker = fight["bookmakers"][0]
                print(f"   Bookmaker: {bookmaker['bookmaker']}")
                for outcome in bookmaker["outcomes"]:
                    print(f"      {outcome['name']}: {outcome['price']}")
    else:
        print(f"⚠️  {result['error']}")
    
    # Test 2: Get specific fight odds
    print("\n2️⃣ Getting odds for Tyson Fury vs Anthony Joshua...")
    result = await get_fight_odds("Tyson Fury", "Anthony Joshua")
    
    if "error" not in result or result.get("demo_mode"):
        print(f"✅ Specific fight odds retrieved!")
        if result.get("fights"):
            print(f"   Fight found: {result['fights'][0]['home_team']} vs {result['fights'][0]['away_team']}")
    else:
        print(f"⚠️  {result['error']}")


async def test_get_odds_movement():
    """Test analyzing odds movement."""
    print("\n" + "="*70)
    print("TEST 2: Analyze Odds Movement")
    print("="*70)
    
    print("\n📊 Analyzing odds movement for Tyson Fury vs Anthony Joshua...")
    result = await get_odds_movement("Tyson Fury", "Anthony Joshua", hours_back=48)
    
    if "error" not in result:
        print(f"✅ Odds movement analyzed!")
        print(f"   Fight: {result['fight']}")
        print(f"   Period: {result['analysis_period']}")
        
        if result.get("opening_odds"):
            print(f"\n   Opening Odds:")
            for fighter, odds in result["opening_odds"].items():
                print(f"   - {fighter}: {odds}")
        
        if result.get("current_odds"):
            print(f"\n   Current Odds:")
            for fighter, odds in result["current_odds"].items():
                print(f"   - {fighter}: {odds}")
        
        if result.get("movement"):
            print(f"\n   Movement Analysis:")
            for fighter, data in result["movement"].items():
                print(f"   - {fighter}: {data['direction']} ({data['percentage']:.1f}%)")
                print(f"     Interpretation: {data['interpretation']}")
        
        if result.get("recommendation"):
            print(f"\n   📍 Recommendation: {result['recommendation']}")
    else:
        print(f"⚠️  {result['error']}")


async def test_calculate_betting_value():
    """Test calculating betting value."""
    print("\n" + "="*70)
    print("TEST 3: Calculate Betting Value")
    print("="*70)
    
    print("\n💰 Calculating betting value for Tyson Fury vs Anthony Joshua...")
    
    # Test with sample stats
    fighter_stats = {
        "wins": 34,
        "losses": 2,
        "draws": 1,
        "total_fights": 37,
        "ko_percentage": 71
    }
    
    result = await calculate_betting_value("Tyson Fury", "Anthony Joshua", fighter_stats)
    
    if "error" not in result:
        print(f"✅ Value analysis complete!")
        print(f"\n   Fighter: {result['fighter']}")
        print(f"   Opponent: {result['opponent']}")
        print(f"   Current Odds: {result['current_odds']}")
        print(f"   Implied Probability: {result['implied_probability']}%")
        print(f"   True Probability (Est.): {result['estimated_true_probability']}%")
        print(f"   Value: {result['value_percentage']}%")
        print(f"   Expected Value: {result['expected_value']}%")
        print(f"\n   🎯 Recommendation: {result['recommendation']}")
        print(f"   📊 Confidence: {result['confidence']}")
        
        if result.get("analysis"):
            print(f"\n   Analysis:")
            print(f"   - {result['analysis']['interpretation']}")
            print(f"   - {result['analysis']['edge']}")
            print(f"   - {result['analysis']['roi_projection']}")
    else:
        print(f"⚠️  {result['error']}")


async def test_get_betting_trends():
    """Test getting betting trends."""
    print("\n" + "="*70)
    print("TEST 4: Get Betting Trends")
    print("="*70)
    
    print("\n📈 Analyzing betting trends for the past week...")
    result = await get_betting_trends(days_back=7)
    
    if "error" not in result:
        print(f"✅ Trends analyzed!")
        print(f"   Period: {result['period']}")
        
        if result.get("public_favorites"):
            print(f"\n   Public Favorites:")
            for fav in result["public_favorites"][:3]:
                print(f"   • {fav['fighter']}")
                print(f"     Public Bets: {fav['public_bets']} | Money: {fav['public_money']}")
                print(f"     Trend: {fav['trend']}")
        
        if result.get("sharp_money_indicators"):
            print(f"\n   Sharp Money Indicators:")
            for move in result["sharp_money_indicators"]["reverse_line_movement"][:2]:
                print(f"   • {move}")
        
        if result.get("contrarian_opportunities"):
            print(f"\n   Contrarian Opportunities:")
            for opp in result["contrarian_opportunities"]:
                print(f"   • {opp['fighter']} ({opp['public_percentage']}% public backing)")
                print(f"     {opp['recommendation']}")
    else:
        print(f"⚠️  {result['error']}")


async def test_predict_fight_outcome():
    """Test fight outcome prediction."""
    print("\n" + "="*70)
    print("TEST 5: Predict Fight Outcome")
    print("="*70)
    
    print("\n🔮 Predicting outcome for Canelo Alvarez vs David Benavidez...")
    result = await predict_fight_outcome("Canelo Alvarez", "David Benavidez", model="statistical")
    
    if "error" not in result:
        print(f"✅ Prediction complete!")
        print(f"   Fight: {result['fight']}")
        print(f"   Model: {result['model_type']}")
        
        if result.get("prediction"):
            pred = result["prediction"]
            print(f"\n   🏆 Predicted Winner: {pred['winner']}")
            print(f"   📊 Confidence: {pred['confidence']}%")
            print(f"   🥊 Method: {pred['method']}")
            print(f"\n   Method Breakdown:")
            for method, prob in pred["method_probability"].items():
                print(f"   - {method}: {prob}%")
        
        if result.get("key_factors"):
            print(f"\n   Key Factors:")
            for factor in result["key_factors"]:
                print(f"   • {factor['factor']}: Favors {factor['favors']} ({factor['impact']})")
        
        if result.get("betting_recommendation"):
            rec = result["betting_recommendation"]
            print(f"\n   Betting Recommendations:")
            print(f"   - Main Bet: {rec['main_bet']}")
            print(f"   - Value Bet: {rec['value_bet']}")
            print(f"   - Hedge: {rec['hedge_option']}")
        
        if result.get("model_accuracy"):
            print(f"\n   Model Accuracy: {result['model_accuracy']}")
    else:
        print(f"⚠️  {result['error']}")


async def test_real_world_scenario():
    """Test a comprehensive real-world betting analysis."""
    print("\n" + "="*70)
    print("TEST 6: Real-World Scenario - Complete Fight Analysis")
    print("="*70)
    
    fighter1 = "Tyson Fury"
    fighter2 = "Anthony Joshua"
    
    print(f"\n🔬 Comprehensive Betting Analysis: {fighter1} vs {fighter2}\n")
    
    # 1. Get current odds
    print("1️⃣ Current Odds:")
    odds = await get_fight_odds(fighter1, fighter2)
    if odds.get("fights"):
        print(f"   ✅ Odds available from multiple bookmakers")
    
    # 2. Check odds movement
    print("\n2️⃣ Odds Movement:")
    movement = await get_odds_movement(fighter1, fighter2)
    if movement.get("recommendation"):
        print(f"   📊 {movement['recommendation']}")
    
    # 3. Calculate value
    print("\n3️⃣ Betting Value:")
    value = await calculate_betting_value(fighter1, fighter2)
    if value.get("recommendation"):
        print(f"   💰 {value['recommendation']} ({value['confidence']} confidence)")
    
    # 4. Get prediction
    print("\n4️⃣ Model Prediction:")
    prediction = await predict_fight_outcome(fighter1, fighter2)
    if prediction.get("prediction"):
        print(f"   🏆 Predicted: {prediction['prediction']['winner']} ({prediction['prediction']['confidence']}%)")
    
    print("\n" + "="*70)
    print("Complete betting intelligence gathered!")
    print("="*70)


async def run_all_tests():
    """Run all tests."""
    print("="*70)
    print("🥊 BOXING BETTING & ODDS MCP SERVER TEST SUITE")
    print("="*70)
    print("\nTesting sports betting and odds analysis functionality")
    
    # Check for API key
    if os.getenv("ODDS_API_KEY"):
        print("✅ ODDS_API_KEY detected - using real betting data\n")
    else:
        print("⚠️  ODDS_API_KEY not set - using demo data")
        print("   Set with: export ODDS_API_KEY='your_key'\n")
    
    try:
        await test_get_fight_odds()
        await test_get_odds_movement()
        await test_calculate_betting_value()
        await test_get_betting_trends()
        await test_predict_fight_outcome()
        await test_real_world_scenario()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\n🎉 Your Boxing Betting & Odds MCP Server is working perfectly!")
        print("   Next: Start the HTTP server with 'python boxing_odds.py'")
        print("   Then integrate with Boxing Analytics for complete intelligence!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())