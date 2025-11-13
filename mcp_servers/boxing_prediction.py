#!/usr/bin/env python3
"""
ADVANCED BOXING ANALYSIS TOOLS

These tools leverage the enhanced database with complete fight histories,
title records, and deep data to provide sophisticated analytics.

"""

import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import statistics

DB_PATH = "data/boxing_data.db"


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


async def analyze_career_trajectory(name: str, window: int = 5) -> Dict[str, Any]:
    """
    Analyze fighter's career trajectory using rolling window analysis.
    Shows if fighter is improving, declining, or at peak.
    
    Args:
        name: Fighter's name
        window: Number of fights for rolling average (default 5)
    
    Returns:
        Career trajectory analysis with trend indicators
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get fighter
    cursor.execute("SELECT id FROM fighters WHERE LOWER(name) LIKE LOWER(?)", (f"%{name}%",))
    fighter = cursor.fetchone()
    if not fighter:
        return {"error": f"Fighter '{name}' not found"}
    
    fighter_id = fighter['id']
    
    # Get all fights chronologically
    cursor.execute("""
        SELECT 
            f.date,
            f.method,
            f.round,
            CASE 
                WHEN f.winner_id = ? THEN 'Win'
                WHEN f.winner_id IS NULL THEN 'Draw'
                ELSE 'Loss'
            END as result,
            f.title_fight,
            CASE 
                WHEN f.fighter1_id = ? THEN f2.name 
                ELSE f1.name 
            END as opponent,
            CASE 
                WHEN f.fighter1_id = ? THEN f2.record_wins 
                ELSE f1.record_wins 
            END as opponent_wins
        FROM fights f
        LEFT JOIN fighters f1 ON f.fighter1_id = f1.id
        LEFT JOIN fighters f2 ON f.fighter2_id = f2.id
        WHERE (f.fighter1_id = ? OR f.fighter2_id = ?)
        AND f.status = 'FINISHED'
        AND f.date IS NOT NULL
        ORDER BY f.date ASC
    """, (fighter_id, fighter_id, fighter_id, fighter_id, fighter_id))
    
    fights = [dict(f) for f in cursor.fetchall()]
    conn.close()
    
    if len(fights) < window:
        return {
            "fighter": name,
            "total_fights": len(fights),
            "error": f"Not enough fights for trajectory analysis (need at least {window})"
        }
    
    # Calculate rolling statistics
    rolling_win_rate = []
    rolling_ko_rate = []
    rolling_opponent_quality = []
    
    for i in range(window - 1, len(fights)):
        window_fights = fights[i - window + 1:i + 1]
        
        # Win rate in window
        wins = sum(1 for f in window_fights if f['result'] == 'Win')
        win_rate = wins / len(window_fights)
        rolling_win_rate.append(win_rate)
        
        # KO rate in window
        kos = sum(1 for f in window_fights if f['result'] == 'Win' and f['method'] in ['KO', 'TKO', 'RTD'])
        ko_rate = kos / len(window_fights)
        rolling_ko_rate.append(ko_rate)
        
        # Average opponent quality (by wins)
        avg_opp_wins = statistics.mean([f['opponent_wins'] or 0 for f in window_fights])
        rolling_opponent_quality.append(avg_opp_wins)
    
    # Determine trend
    recent_win_rate = statistics.mean(rolling_win_rate[-3:]) if len(rolling_win_rate) >= 3 else rolling_win_rate[-1]
    early_win_rate = statistics.mean(rolling_win_rate[:3]) if len(rolling_win_rate) >= 3 else rolling_win_rate[0]
    
    trend_diff = recent_win_rate - early_win_rate
    
    if trend_diff > 0.15:
        trend = "Improving"
        trend_strength = "Strong"
    elif trend_diff > 0.05:
        trend = "Improving"
        trend_strength = "Moderate"
    elif trend_diff < -0.15:
        trend = "Declining"
        trend_strength = "Strong"
    elif trend_diff < -0.05:
        trend = "Declining"
        trend_strength = "Moderate"
    else:
        trend = "Stable"
        trend_strength = "Consistent"
    
    # Career phases
    total = len(fights)
    early_phase = fights[:total//3]
    mid_phase = fights[total//3:2*total//3]
    late_phase = fights[2*total//3:]
    
    def phase_stats(phase_fights):
        wins = sum(1 for f in phase_fights if f['result'] == 'Win')
        return {
            "fights": len(phase_fights),
            "wins": wins,
            "win_rate": wins / len(phase_fights) if phase_fights else 0,
            "title_fights": sum(1 for f in phase_fights if f['title_fight'])
        }
    
    return {
        "fighter": name,
        "total_fights_analyzed": len(fights),
        "career_span": {
            "first_fight": fights[0]['date'],
            "last_fight": fights[-1]['date'],
            "years_active": (datetime.strptime(fights[-1]['date'], "%Y-%m-%d") - 
                           datetime.strptime(fights[0]['date'], "%Y-%m-%d")).days / 365
        },
        "current_trajectory": {
            "trend": trend,
            "trend_strength": trend_strength,
            "recent_win_rate": round(recent_win_rate * 100, 1),
            "change_from_early_career": round(trend_diff * 100, 1)
        },
        "career_phases": {
            "early_career": phase_stats(early_phase),
            "mid_career": phase_stats(mid_phase),
            "late_career": phase_stats(late_phase)
        },
        "recent_form": {
            "last_5_fights": [{
                "date": f['date'],
                "opponent": f['opponent'],
                "result": f['result'],
                "method": f['method']
            } for f in fights[-5:]],
            "last_5_record": f"{sum(1 for f in fights[-5:] if f['result'] == 'Win')}-{sum(1 for f in fights[-5:] if f['result'] == 'Loss')}"
        },
        "interpretation": f"{name} is currently {trend.lower()} with {trend_strength.lower()} momentum based on rolling {window}-fight analysis."
    }


async def compare_common_opponents(fighter1: str, fighter2: str) -> Dict[str, Any]:
    """
    Find and compare performance against common opponents.
    Critical for indirect fighter comparison.
    
    Args:
        fighter1: First fighter's name
        fighter2: Second fighter's name
    
    Returns:
        Detailed comparison of performance vs shared opponents
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get both fighters
    cursor.execute("SELECT id, name FROM fighters WHERE LOWER(name) LIKE LOWER(?)", (f"%{fighter1}%",))
    f1 = cursor.fetchone()
    
    cursor.execute("SELECT id, name FROM fighters WHERE LOWER(name) LIKE LOWER(?)", (f"%{fighter2}%",))
    f2 = cursor.fetchone()
    
    if not f1 or not f2:
        return {"error": "One or both fighters not found"}
    
    f1_id, f1_name = f1['id'], f1['name']
    f2_id, f2_name = f2['id'], f2['name']
    
    # Find common opponents
    cursor.execute("""
        SELECT DISTINCT
            CASE 
                WHEN fights1.fighter1_id = ? THEN f1.name
                ELSE f2.name
            END as opponent_name,
            CASE 
                WHEN fights1.fighter1_id = ? THEN fights1.fighter2_id
                ELSE fights1.fighter1_id
            END as opponent_id
        FROM fights fights1
        LEFT JOIN fighters f1 ON fights1.fighter1_id = f1.id
        LEFT JOIN fighters f2 ON fights1.fighter2_id = f2.id
        WHERE (fights1.fighter1_id = ? OR fights1.fighter2_id = ?)
        
        INTERSECT
        
        SELECT DISTINCT
            CASE 
                WHEN fights2.fighter1_id = ? THEN f1.name
                ELSE f2.name
            END as opponent_name,
            CASE 
                WHEN fights2.fighter1_id = ? THEN fights2.fighter2_id
                ELSE fights2.fighter1_id
            END as opponent_id
        FROM fights fights2
        LEFT JOIN fighters f1 ON fights2.fighter1_id = f1.id
        LEFT JOIN fighters f2 ON fights2.fighter2_id = f2.id
        WHERE (fights2.fighter1_id = ? OR fights2.fighter2_id = ?)
    """, (f1_id, f1_id, f1_id, f1_id, f2_id, f2_id, f2_id, f2_id))
    
    common_opponents = cursor.fetchall()
    
    if not common_opponents:
        conn.close()
        return {
            "fighter1": f1_name,
            "fighter2": f2_name,
            "common_opponents_count": 0,
            "analysis": "No common opponents found - direct statistical comparison recommended"
        }
    
    # Get details for each common opponent
    comparisons = []
    f1_score = 0
    f2_score = 0
    
    for opponent in common_opponents:
        opp_name = opponent['opponent_name']
        opp_id = opponent['opponent_id']
        
        # Get fighter1's result vs this opponent
        cursor.execute("""
            SELECT 
                f.date, f.method, f.round,
                CASE 
                    WHEN f.winner_id = ? THEN 'Win'
                    WHEN f.winner_id IS NULL THEN 'Draw'
                    ELSE 'Loss'
                END as result
            FROM fights f
            WHERE (f.fighter1_id = ? AND f.fighter2_id = ?)
               OR (f.fighter2_id = ? AND f.fighter1_id = ?)
            ORDER BY f.date DESC
            LIMIT 1
        """, (f1_id, f1_id, opp_id, f1_id, opp_id))
        f1_result = dict(cursor.fetchone())
        
        # Get fighter2's result vs this opponent
        cursor.execute("""
            SELECT 
                f.date, f.method, f.round,
                CASE 
                    WHEN f.winner_id = ? THEN 'Win'
                    WHEN f.winner_id IS NULL THEN 'Draw'
                    ELSE 'Loss'
                END as result
            FROM fights f
            WHERE (f.fighter1_id = ? AND f.fighter2_id = ?)
               OR (f.fighter2_id = ? AND f.fighter1_id = ?)
            ORDER BY f.date DESC
            LIMIT 1
        """, (f2_id, f2_id, opp_id, f2_id, opp_id))
        f2_result = dict(cursor.fetchone())
        
        # Compare results
        comparison = {
            "opponent": opp_name,
            f"{f1_name}_result": f1_result['result'],
            f"{f1_name}_method": f1_result['method'],
            f"{f1_name}_round": f1_result['round'],
            f"{f2_name}_result": f2_result['result'],
            f"{f2_name}_method": f2_result['method'],
            f"{f2_name}_round": f2_result['round'],
        }
        
        # Score the comparison
        if f1_result['result'] == 'Win' and f2_result['result'] != 'Win':
            f1_score += 1
            comparison['advantage'] = f1_name
        elif f2_result['result'] == 'Win' and f1_result['result'] != 'Win':
            f2_score += 1
            comparison['advantage'] = f2_name
        elif f1_result['result'] == 'Win' and f2_result['result'] == 'Win':
            # Both won - compare methods
            if f1_result['method'] in ['KO', 'TKO'] and f2_result['method'] not in ['KO', 'TKO']:
                f1_score += 0.5
                comparison['advantage'] = f"{f1_name} (more impressive win)"
            elif f2_result['method'] in ['KO', 'TKO'] and f1_result['method'] not in ['KO', 'TKO']:
                f2_score += 0.5
                comparison['advantage'] = f"{f2_name} (more impressive win)"
            else:
                comparison['advantage'] = "Even"
        else:
            comparison['advantage'] = "Even"
        
        comparisons.append(comparison)
    
    conn.close()
    
    # Determine overall advantage
    if f1_score > f2_score:
        overall_advantage = f1_name
        confidence = min(0.6 + (f1_score - f2_score) * 0.1, 0.9)
    elif f2_score > f1_score:
        overall_advantage = f2_name
        confidence = min(0.6 + (f2_score - f1_score) * 0.1, 0.9)
    else:
        overall_advantage = "Even"
        confidence = 0.5
    
    return {
        "fighter1": f1_name,
        "fighter2": f2_name,
        "common_opponents_count": len(common_opponents),
        "score": {
            f1_name: f1_score,
            f2_name: f2_score
        },
        "overall_advantage": overall_advantage,
        "confidence": round(confidence, 2),
        "detailed_comparisons": comparisons,
        "analysis": f"Based on {len(common_opponents)} common opponents, {overall_advantage} has performed better with {confidence:.0%} confidence."
    }


async def analyze_title_fight_performance(name: str) -> Dict[str, Any]:
    """
    Analyze fighter's performance specifically in championship fights.
    Shows if fighter "rises to the occasion" in big moments.
    
    Args:
        name: Fighter's name
    
    Returns:
        Title fight performance analysis
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get fighter
    cursor.execute("SELECT id, name FROM fighters WHERE LOWER(name) LIKE LOWER(?)", (f"%{name}%",))
    fighter = cursor.fetchone()
    if not fighter:
        return {"error": f"Fighter '{name}' not found"}
    
    fighter_id, fighter_name = fighter['id'], fighter['name']
    
    # Get all title fights
    cursor.execute("""
        SELECT 
            f.date,
            f.method,
            f.round,
            CASE 
                WHEN f.winner_id = ? THEN 'Win'
                WHEN f.winner_id IS NULL THEN 'Draw'
                ELSE 'Loss'
            END as result,
            CASE 
                WHEN f.fighter1_id = ? THEN f2.name 
                ELSE f1.name 
            END as opponent
        FROM fights f
        LEFT JOIN fighters f1 ON f.fighter1_id = f1.id
        LEFT JOIN fighters f2 ON f.fighter2_id = f2.id
        WHERE (f.fighter1_id = ? OR f.fighter2_id = ?)
        AND f.title_fight = 1
        AND f.status = 'FINISHED'
        ORDER BY f.date ASC
    """, (fighter_id, fighter_id, fighter_id, fighter_id))
    
    title_fights = [dict(f) for f in cursor.fetchall()]
    
    # Get all non-title fights for comparison
    cursor.execute("""
        SELECT 
            CASE 
                WHEN f.winner_id = ? THEN 'Win'
                WHEN f.winner_id IS NULL THEN 'Draw'
                ELSE 'Loss'
            END as result,
            f.method
        FROM fights f
        WHERE (f.fighter1_id = ? OR f.fighter2_id = ?)
        AND f.title_fight = 0
        AND f.status = 'FINISHED'
    """, (fighter_id, fighter_id, fighter_id))
    
    non_title_fights = [dict(f) for f in cursor.fetchall()]
    
    # Get title records
    cursor.execute("""
        SELECT title_name, organization, won_date, lost_date, defenses_count
        FROM titles
        WHERE fighter_id = ?
        ORDER BY won_date DESC
    """, (fighter_id,))
    
    titles = [dict(t) for t in cursor.fetchall()]
    
    conn.close()
    
    if not title_fights:
        return {
            "fighter": fighter_name,
            "title_fights": 0,
            "analysis": "No title fight experience in database"
        }
    
    # Calculate title fight stats
    title_wins = sum(1 for f in title_fights if f['result'] == 'Win')
    title_losses = sum(1 for f in title_fights if f['result'] == 'Loss')
    title_draws = sum(1 for f in title_fights if f['result'] == 'Draw')
    
    title_win_rate = title_wins / len(title_fights)
    title_ko_rate = sum(1 for f in title_fights if f['result'] == 'Win' and f['method'] in ['KO', 'TKO', 'RTD']) / len(title_fights)
    
    # Calculate non-title stats for comparison
    if non_title_fights:
        non_title_wins = sum(1 for f in non_title_fights if f['result'] == 'Win')
        non_title_win_rate = non_title_wins / len(non_title_fights)
        non_title_ko_rate = sum(1 for f in non_title_fights if f['result'] == 'Win' and f['method'] in ['KO', 'TKO', 'RTD']) / len(non_title_fights)
    else:
        non_title_win_rate = 0
        non_title_ko_rate = 0
    
    # Determine if fighter elevates in title fights
    performance_comparison = title_win_rate - non_title_win_rate
    
    if performance_comparison > 0.1:
        rises_to_occasion = True
        occasion_strength = "Significantly better"
    elif performance_comparison > 0:
        rises_to_occasion = True
        occasion_strength = "Slightly better"
    elif performance_comparison < -0.1:
        rises_to_occasion = False
        occasion_strength = "Significantly worse"
    elif performance_comparison < 0:
        rises_to_occasion = False
        occasion_strength = "Slightly worse"
    else:
        rises_to_occasion = None
        occasion_strength = "Same"
    
    return {
        "fighter": fighter_name,
        "title_fight_record": f"{title_wins}-{title_losses}-{title_draws}",
        "title_fight_statistics": {
            "total_title_fights": len(title_fights),
            "wins": title_wins,
            "losses": title_losses,
            "draws": title_draws,
            "win_rate": round(title_win_rate * 100, 1),
            "ko_rate": round(title_ko_rate * 100, 1)
        },
        "non_title_statistics": {
            "total_fights": len(non_title_fights),
            "win_rate": round(non_title_win_rate * 100, 1),
            "ko_rate": round(non_title_ko_rate * 100, 1)
        },
        "performance_comparison": {
            "rises_to_occasion": rises_to_occasion,
            "assessment": occasion_strength,
            "win_rate_difference": round(performance_comparison * 100, 1)
        },
        "championship_pedigree": {
            "titles_won": len(titles),
            "total_defenses": sum(t['defenses_count'] for t in titles),
            "current_titles": [t['title_name'] for t in titles if not t['lost_date']]
        },
        "title_fight_history": [{
            "date": f['date'],
            "opponent": f['opponent'],
            "result": f['result'],
            "method": f['method']
        } for f in title_fights],
        "analysis": f"{fighter_name} performs {occasion_strength.lower()} in title fights compared to regular fights, with a {title_win_rate:.0%} win rate in championship bouts."
    }


# Tool definitions for MCP server
ADVANCED_TOOLS = [
    {
        "name": "analyze_career_trajectory",
        "description": "Analyze a fighter's career trajectory to see if they're improving, declining, or at peak. Uses rolling window analysis of complete fight history.",
        "function": analyze_career_trajectory
    },
    {
        "name": "compare_common_opponents",
        "description": "Find shared opponents between two fighters and compare their performance. Critical for indirect matchup analysis.",
        "function": compare_common_opponents
    },
    {
        "name": "analyze_title_fight_performance",
        "description": "Analyze how a fighter performs specifically in championship fights vs regular fights. Shows if they rise to big occasions.",
        "function": analyze_title_fight_performance
    }
]


if __name__ == "__main__":
    """Test the advanced tools."""
    import asyncio
    
    print("="*70)
    print("TESTING ADVANCED ANALYSIS TOOLS")
    print("="*70)
    
    async def test():
        # Test 1: Career Trajectory
        print("\n📈 Test 1: Career Trajectory Analysis")
        print("-"*70)
        result = await analyze_career_trajectory("Tyson Fury")
        print(f"Fighter: {result.get('fighter')}")
        print(f"Trajectory: {result.get('current_trajectory', {}).get('trend')}")
        print(f"Recent Win Rate: {result.get('current_trajectory', {}).get('recent_win_rate')}%")
        
        # Test 2: Common Opponents
        print("\n🥊 Test 2: Common Opponents Comparison")
        print("-"*70)
        result = await compare_common_opponents("Tyson Fury", "Deontay Wilder")
        print(f"Common opponents: {result.get('common_opponents_count')}")
        print(f"Advantage: {result.get('overall_advantage')}")
        
        # Test 3: Title Fight Performance
        print("\n🏆 Test 3: Title Fight Performance")
        print("-"*70)
        result = await analyze_title_fight_performance("Canelo Alvarez")
        print(f"Title fight record: {result.get('title_fight_record')}")
        print(f"Rises to occasion: {result.get('performance_comparison', {}).get('rises_to_occasion')}")
        print(f"Total defenses: {result.get('championship_pedigree', {}).get('total_defenses')}")
    
    asyncio.run(test())