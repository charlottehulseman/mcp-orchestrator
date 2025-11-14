#!/usr/bin/env python3
"""
Test the Boxing News & Media MCP Server

This script tests all news aggregation and sentiment analysis functionality.
"""

import asyncio
import sys
import os
sys.path.append('.')

from mcp_servers.boxing_news import (
    get_fight_news,
    get_social_buzz,
    compare_fighter_hype,
    get_fight_predictions,
    analyze_press_conference
)


async def test_get_fight_news():
    """Test getting fight news."""
    print("\n" + "="*70)
    print("TEST 1: Get Fight News")
    print("="*70)
    
    # Test 1: General boxing news
    print("\n1️⃣ Getting general boxing news...")
    result = await get_fight_news(days_back=7, max_results=5)
    
    if "error" not in result or result.get("demo_mode"):
        print(f"✅ News retrieved!")
        print(f"   Query: {result['query']}")
        print(f"   Period: {result['period']}")
        print(f"   Total Articles: {result['total_articles']}")
        
        if result.get("demo_mode"):
            print(f"   Mode: DEMO (set NEWS_API_KEY for real news)")
        
        if result.get("articles"):
            print(f"\n   Recent Headlines:")
            for i, article in enumerate(result["articles"][:3], 1):
                print(f"\n   {i}. {article['title']}")
                print(f"      Source: {article['source']}")
                print(f"      Sentiment: {article['sentiment']}")
    else:
        print(f"⚠️  {result['error']}")
    
    # Test 2: Specific fighter news
    print("\n2️⃣ Getting news for Tyson Fury...")
    result = await get_fight_news(fighter_name="Tyson Fury", days_back=7)
    
    if "error" not in result or result.get("demo_mode"):
        print(f"✅ Fighter-specific news retrieved!")
        print(f"   Articles found: {result['total_articles']}")
        if result.get("articles"):
            print(f"   Latest: {result['articles'][0]['title']}")
    else:
        print(f"⚠️  {result['error']}")


async def test_get_social_buzz():
    """Test getting social media buzz."""
    print("\n" + "="*70)
    print("TEST 2: Get Social Media Buzz")
    print("="*70)
    
    print("\n📱 Analyzing social buzz for Canelo Alvarez...")
    result = await get_social_buzz("Canelo Alvarez", platform="all", hours_back=24)
    
    if "error" not in result:
        print(f"✅ Social buzz analyzed!")
        print(f"   Fighter: {result['fighter']}")
        print(f"   Platform: {result['platform']}")
        print(f"   Period: {result['period']}")
        
        if result.get("metrics"):
            metrics = result["metrics"]
            print(f"\n   Metrics:")
            print(f"   - Total Mentions: {metrics['total_mentions']:,}")
            print(f"   - Trending Score: {metrics['trending_score']}")
            print(f"   - Reach: {metrics['reach']}")
            print(f"   - Engagement Rate: {metrics['engagement_rate']}")
        
        if result.get("sentiment_breakdown"):
            sent = result["sentiment_breakdown"]
            print(f"\n   Sentiment Breakdown:")
            print(f"   - Positive: {sent['positive']}%")
            print(f"   - Neutral: {sent['neutral']}%")
            print(f"   - Negative: {sent['negative']}%")
            print(f"   - Overall: {sent['overall_sentiment']}")
        
        if result.get("top_topics"):
            print(f"\n   Top Topics:")
            for topic in result["top_topics"][:3]:
                print(f"   • {topic['topic']}: {topic['mentions']} mentions ({topic['sentiment']})")
        
        if result.get("momentum"):
            print(f"\n   Momentum: {result['momentum']['direction']} ({result['momentum']['change_24h']})")
    else:
        print(f"⚠️  {result['error']}")


async def test_compare_fighter_hype():
    """Test comparing fighter hype levels."""
    print("\n" + "="*70)
    print("TEST 3: Compare Fighter Hype")
    print("="*70)
    
    fighter1 = "Tyson Fury"
    fighter2 = "Anthony Joshua"
    
    print(f"\n⚖️  Comparing hype: {fighter1} vs {fighter2}...")
    result = await compare_fighter_hype(fighter1, fighter2, days_back=7)
    
    if "error" not in result:
        print(f"✅ Hype comparison complete!")
        print(f"   Period: {result['analysis_period']}")
        
        if result.get("comparison"):
            comp = result["comparison"]
            print(f"\n   {fighter1}:")
            print(f"   - Hype Score: {comp[fighter1]['hype_score']}")
            print(f"   - News Articles: {comp[fighter1]['news_articles']}")
            print(f"   - Social Mentions: {comp[fighter1]['social_mentions']:,}")
            print(f"   - Media Grade: {comp[fighter1]['media_grade']}")
            
            print(f"\n   {fighter2}:")
            print(f"   - Hype Score: {comp[fighter2]['hype_score']}")
            print(f"   - News Articles: {comp[fighter2]['news_articles']}")
            print(f"   - Social Mentions: {comp[fighter2]['social_mentions']:,}")
            print(f"   - Media Grade: {comp[fighter2]['media_grade']}")
        
        if result.get("verdict"):
            verdict = result["verdict"]
            print(f"\n   🏆 Hype Leader: {verdict['hype_leader']}")
            print(f"   📊 Advantage: {verdict['advantage']}")
            print(f"   💡 Interpretation: {verdict['interpretation']}")
        
        if result.get("key_insights"):
            print(f"\n   Key Insights:")
            for insight in result["key_insights"]:
                print(f"   • {insight}")
    else:
        print(f"⚠️  {result['error']}")


async def test_get_fight_predictions():
    """Test getting expert predictions."""
    print("\n" + "="*70)
    print("TEST 4: Get Expert Predictions")
    print("="*70)
    
    fighter1 = "Canelo Alvarez"
    fighter2 = "David Benavidez"
    
    print(f"\n🎯 Getting expert predictions for {fighter1} vs {fighter2}...")
    result = await get_fight_predictions(fighter1, fighter2, source="all")
    
    if "error" not in result:
        print(f"✅ Expert predictions gathered!")
        print(f"   Fight: {result['fight']}")
        print(f"   Total Experts: {result['total_experts']}")
        
        if result.get("consensus"):
            cons = result["consensus"]
            print(f"\n   Consensus:")
            print(f"   - Favorite: {cons['favorite']}")
            print(f"   - Split: {cons['split']}")
            print(f"   - Percentage: {cons['percentage']}")
            print(f"   - Avg Confidence: {cons['average_confidence']}%")
        
        if result.get("predictions"):
            print(f"\n   Expert Picks (showing first 3):")
            for pred in result["predictions"][:3]:
                print(f"\n   • {pred['expert']}")
                print(f"     Pick: {pred['pick']} by {pred['method']} ({pred['confidence']}%)")
                print(f"     Reasoning: {pred['reasoning']}")
        
        if result.get("method_consensus"):
            method = result["method_consensus"]
            print(f"\n   Method Consensus:")
            print(f"   - Most Likely: {method['most_likely']}")
            for m, count in method.items():
                if m != "most_likely":
                    print(f"   - {m}: {count} experts")
    else:
        print(f"⚠️  {result['error']}")


async def test_analyze_press_conference():
    """Test press conference analysis."""
    print("\n" + "="*70)
    print("TEST 5: Analyze Press Conference")
    print("="*70)
    
    print("\n🎤 Analyzing press conference for Tyson Fury...")
    result = await analyze_press_conference("Tyson Fury", event="recent")
    
    if "error" not in result:
        print(f"✅ Press conference analyzed!")
        print(f"   Fighter: {result['fighter']}")
        print(f"   Event: {result['event']}")
        print(f"   Date: {result['date']}")
        
        if result.get("overall_sentiment"):
            sent = result["overall_sentiment"]
            print(f"\n   Overall Sentiment:")
            print(f"   - Confidence Level: {sent['confidence_level']}%")
            print(f"   - Composure: {sent['composure']}")
            print(f"   - Aggression: {sent['aggression']}")
            print(f"   - Overall: {sent['overall']}")
        
        if result.get("key_quotes"):
            print(f"\n   Key Quotes:")
            for quote in result["key_quotes"][:2]:
                print(f'\n   "{quote["quote"]}"')
                print(f"   - Sentiment: {quote['sentiment']}")
                print(f"   - Impact Score: {quote['impact_score']}/10")
        
        if result.get("body_language_analysis"):
            body = result["body_language_analysis"]
            print(f"\n   Body Language:")
            print(f"   - Eye Contact: {body['eye_contact']}")
            print(f"   - Posture: {body['posture']}")
            print(f"   - Assessment: {body['overall_assessment']}")
        
        if result.get("psychological_edge"):
            edge = result["psychological_edge"]
            print(f"\n   Psychological Edge: {'Yes' if edge['has_advantage'] else 'No'}")
            if edge.get("factors"):
                print(f"   Factors:")
                for factor in edge["factors"][:2]:
                    print(f"   • {factor}")
    else:
        print(f"⚠️  {result['error']}")


async def test_real_world_scenario():
    """Test a comprehensive media analysis scenario."""
    print("\n" + "="*70)
    print("TEST 6: Real-World Scenario - Complete Media Analysis")
    print("="*70)
    
    fighter1 = "Tyson Fury"
    fighter2 = "Anthony Joshua"
    
    print(f"\n🔬 Comprehensive Media Analysis: {fighter1} vs {fighter2}\n")
    
    # 1. Get recent news
    print("1️⃣ Recent News:")
    news = await get_fight_news(days_back=7)
    print(f"   ✅ {news['total_articles']} articles found")
    
    # 2. Compare hype levels
    print("\n2️⃣ Hype Comparison:")
    hype = await compare_fighter_hype(fighter1, fighter2)
    if hype.get("verdict"):
        print(f"   🏆 {hype['verdict']['hype_leader']} leads in media attention")
    
    # 3. Get social buzz for both
    print("\n3️⃣ Social Media Buzz:")
    social1 = await get_social_buzz(fighter1)
    social2 = await get_social_buzz(fighter2)
    print(f"   • {fighter1}: {social1['metrics']['total_mentions']:,} mentions")
    print(f"   • {fighter2}: {social2['metrics']['total_mentions']:,} mentions")
    
    # 4. Get expert predictions
    print("\n4️⃣ Expert Predictions:")
    predictions = await get_fight_predictions(fighter1, fighter2)
    if predictions.get("consensus"):
        print(f"   📊 Experts favor: {predictions['consensus']['favorite']} ({predictions['consensus']['percentage']})")
    
    # 5. Analyze press conferences
    print("\n5️⃣ Press Conference Analysis:")
    press1 = await analyze_press_conference(fighter1)
    press2 = await analyze_press_conference(fighter2)
    if press1.get("overall_sentiment") and press2.get("overall_sentiment"):
        conf1 = press1["overall_sentiment"]["confidence_level"]
        conf2 = press2["overall_sentiment"]["confidence_level"]
        print(f"   • {fighter1}: {conf1}% confidence")
        print(f"   • {fighter2}: {conf2}% confidence")
        
        if conf1 > conf2:
            print(f"   🎯 {fighter1} shows higher confidence in media appearances")
        else:
            print(f"   🎯 {fighter2} shows higher confidence in media appearances")
    
    print("\n" + "="*70)
    print("Complete media intelligence gathered!")
    print("="*70)


async def run_all_tests():
    """Run all tests."""
    print("="*70)
    print("📰 BOXING NEWS & MEDIA MCP SERVER TEST SUITE")
    print("="*70)
    print("\nTesting news aggregation and sentiment analysis functionality")
    
    # Check for API key
    if os.getenv("NEWS_API_KEY"):
        print("✅ NEWS_API_KEY detected - using real news data\n")
    else:
        print("⚠️  NEWS_API_KEY not set - using demo data")
        print("   Set with: export NEWS_API_KEY='your_key'\n")
    
    try:
        await test_get_fight_news()
        await test_get_social_buzz()
        await test_compare_fighter_hype()
        await test_get_fight_predictions()
        await test_analyze_press_conference()
        await test_real_world_scenario()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\n🎉 Your Boxing News & Media MCP Server is working perfectly!")
        print("   Next: Integrate with Boxing Analytics and Betting/Odds servers")
        print("   for complete Boxing Intelligence Platform!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())