#!/usr/bin/env python3
"""
ADVANCED BOXING ANALYSIS TOOLS
Clean version with absolute paths for deployment
"""

import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import statistics

# CRITICAL: Use absolute path
DB_PATH = Path(__file__).parent.parent / "data" / "boxing_data.db"


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


async def analyze_career_trajectory(name: str, window: int = 5) -> Dict[str, Any]:
    """Analyze fighter's career trajectory using rolling window analysis."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM fighters WHERE LOWER(name) LIKE LOWER(?)", (f"%{name}%",))
    fighter = cursor.fetchone()
    if not fighter:
        return {"error": f"Fighter '{name}' not found"}
    
    fighter_id = fighter['id']
    
    cursor.execute("""
        SELECT 
            f.date, f.method, f.round,
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
    
    rolling_win_rate = []
    
    for i in range(window - 1, len(fights)):
        window_fights = fights[i - window + 1:i + 1]
        wins = sum(1 for f in window_fights if f['result'] == 'Win')
        win_rate = wins / len(window_fights)
        rolling_win_rate.append(win_rate)
    
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
    """Compare performance against common opponents."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM fighters WHERE LOWER(name) LIKE LOWER(?)", (f"%{fighter1}%",))
    f1 = cursor.fetchone()
    
    cursor.execute("SELECT id, name FROM fighters WHERE LOWER(name) LIKE LOWER(?)", (f"%{fighter2}%",))
    f2 = cursor.fetchone()
    
    if not f1 or not f2:
        return {"error": "One or both fighters not found"}
    
    f1_id, f1_name = f1['id'], f1['name']
    f2_id, f2_name = f2['id'], f2['name']
    
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
    
    comparisons = []
    f1_score = 0
    f2_score = 0
    
    for opponent in common_opponents:
        opp_name = opponent['opponent_name']
        opp_id = opponent['opponent_id']
        
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
        
        comparison = {
            "opponent": opp_name,
            f"{f1_name}_result": f1_result['result'],
            f"{f1_name}_method": f1_result['method'],
            f"{f2_name}_result": f2_result['result'],
            f"{f2_name}_method": f2_result['method'],
        }
        
        if f1_result['result'] == 'Win' and f2_result['result'] != 'Win':
            f1_score += 1
            comparison['advantage'] = f1_name
        elif f2_result['result'] == 'Win' and f1_result['result'] != 'Win':
            f2_score += 1
            comparison['advantage'] = f2_name
        else:
            comparison['advantage'] = "Even"
        
        comparisons.append(comparison)
    
    conn.close()
    
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
        "score": {f1_name: f1_score, f2_name: f2_score},
        "overall_advantage": overall_advantage,
        "confidence": round(confidence, 2),
        "detailed_comparisons": comparisons,
        "analysis": f"Based on {len(common_opponents)} common opponents, {overall_advantage} has performed better with {confidence:.0%} confidence."
    }


async def analyze_title_fight_performance(name: str) -> Dict[str, Any]:
    """Analyze championship fight performance vs regular fights."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM fighters WHERE LOWER(name) LIKE LOWER(?)", (f"%{name}%",))
    fighter = cursor.fetchone()
    if not fighter:
        return {"error": f"Fighter '{name}' not found"}
    
    fighter_id, fighter_name = fighter['id'], fighter['name']
    
    cursor.execute("""
        SELECT 
            f.date, f.method, f.round,
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
    
    title_wins = sum(1 for f in title_fights if f['result'] == 'Win')
    title_losses = sum(1 for f in title_fights if f['result'] == 'Loss')
    title_draws = sum(1 for f in title_fights if f['result'] == 'Draw')
    
    title_win_rate = title_wins / len(title_fights)
    
    if non_title_fights:
        non_title_wins = sum(1 for f in non_title_fights if f['result'] == 'Win')
        non_title_win_rate = non_title_wins / len(non_title_fights)
    else:
        non_title_win_rate = 0
    
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
        },
        "non_title_statistics": {
            "total_fights": len(non_title_fights),
            "win_rate": round(non_title_win_rate * 100, 1),
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