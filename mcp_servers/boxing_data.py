#!/usr/bin/env python3
"""
ULTRA MINIMAL TEST - Just imports, no logic
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# CRITICAL FIX: Use absolute path to database
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "boxing_data.db"

# Debug logging
print(f"Server starting...", file=sys.stderr)
print(f"Project root: {PROJECT_ROOT}", file=sys.stderr)
print(f"Database path: {DB_PATH}", file=sys.stderr)
print(f"Database exists: {DB_PATH.exists()}", file=sys.stderr)

# Import prediction functions - these should be in boxing_prediction.py
try:
    sys.path.insert(0, str(PROJECT_ROOT))
    from mcp_servers.boxing_prediction import (
        analyze_career_trajectory,
        compare_common_opponents,
        analyze_title_fight_performance
    )
    PREDICTION_AVAILABLE = True
    print("Prediction module loaded", file=sys.stderr)
except ImportError as e:
    PREDICTION_AVAILABLE = False
    print(f"Warning: boxing_prediction.py not found ({e}), advanced tools disabled", file=sys.stderr)


def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dicts
    return conn


def format_record(wins: int, losses: int, draws: int) -> str:
    """Format a fighter's record as W-L-D string."""
    return f"{wins}-{losses}-{draws}"


async def get_fighter_stats(name: str) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a fighter.
    
    Args:
        name: Fighter's name (case-insensitive, partial match supported)
    
    Returns:
        Dictionary with fighter statistics
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Search for fighter (case-insensitive & partial match)
    cursor.execute("""
        SELECT * FROM fighters 
        WHERE LOWER(name) LIKE LOWER(?)
        ORDER BY 
            CASE WHEN LOWER(name) = LOWER(?) THEN 0 ELSE 1 END,
            record_wins DESC
        LIMIT 1
    """, (f"%{name}%", name))
    
    fighter = cursor.fetchone()
    
    if not fighter:
        conn.close()
        return {
            "error": f"Fighter '{name}' not found",
            "suggestion": "Try searching with a different spelling or check available fighters"
        }
    
    # Get fighter's titles
    cursor.execute("""
        SELECT title_name, won_date, lost_date, defenses_count
        FROM titles
        WHERE fighter_id = ?
        ORDER BY won_date DESC
    """, (fighter['id'],))
    titles = [dict(t) for t in cursor.fetchall()]
    
    # Get notable wins (wins against fighters with > 30 wins)
    cursor.execute("""
        SELECT f2.name as opponent, fi.date, fi.method, fi.round
        FROM fights fi
        JOIN fighters f2 ON (fi.fighter2_id = f2.id)
        WHERE fi.fighter1_id = ? AND fi.winner_id = ?
        AND f2.record_wins > 30
        ORDER BY fi.date DESC
        LIMIT 5
    """, (fighter['id'], fighter['id']))
    notable_wins = [dict(w) for w in cursor.fetchall()]
    
    # Get fight count
    cursor.execute("""
        SELECT COUNT(*) as fight_count
        FROM fights
        WHERE fighter1_id = ? OR fighter2_id = ?
    """, (fighter['id'], fighter['id']))
    total_fights = cursor.fetchone()['fight_count']
    
    conn.close()
    
    # Age
    age = None
    if fighter['birth_date']:
        try:
            birth = datetime.strptime(fighter['birth_date'], "%Y-%m-%d")
            age = (datetime.now() - birth).days // 365
        except:
            pass
    
    # Career length
    career_length = None
    if fighter['debut_date']:
        try:
            # Handle both "YYYY" and "YYYY-MM-DD" formats
            if len(fighter['debut_date']) == 4:  # Year only
                debut = datetime(int(fighter['debut_date']), 1, 1)
            else:
                debut = datetime.strptime(fighter['debut_date'], "%Y-%m-%d")
            career_length = (datetime.now() - debut).days // 365
        except:
            pass
    
    return {
        "name": fighter['name'],
        "nickname": fighter['nickname'],
        "nationality": fighter['nationality'],
        "weight_class": fighter['weight_class'],
        "record": format_record(fighter['record_wins'], fighter['record_losses'], fighter['record_draws']),
        "record_details": {
            "wins": fighter['record_wins'],
            "losses": fighter['record_losses'],
            "draws": fighter['record_draws'],
            "ko_percentage": round(fighter['ko_percentage'], 1)
        },
        "physical_stats": {
            "reach_cm": fighter['reach'],
            "height_cm": fighter['height'],
            "stance": fighter['stance']
        },
        "age": age,
        "active": bool(fighter['active']),
        "career_length_years": career_length,
        "total_fights": total_fights,
        "titles": titles,
        "notable_wins": notable_wins
    }


async def compare_fighters(fighter1: str, fighter2: str) -> Dict[str, Any]:
    """
    Compare two fighters statistically.
    
    Args:
        fighter1: First fighter's name
        fighter2: Second fighter's name
    
    Returns:
        Comparison analysis with advantages for each fighter
    """
    # Stats for both fighters
    stats1 = await get_fighter_stats(fighter1)
    stats2 = await get_fighter_stats(fighter2)
    
    if "error" in stats1:
        return stats1
    if "error" in stats2:
        return stats2
    
    advantages1 = []
    advantages2 = []
    
    # Compare KO percentage
    ko1 = stats1['record_details']['ko_percentage']
    ko2 = stats2['record_details']['ko_percentage']
    if ko1 > ko2 + 5:
        advantages1.append(f"Superior knockout power ({ko1}% vs {ko2}%)")
    elif ko2 > ko1 + 5:
        advantages2.append(f"Superior knockout power ({ko2}% vs {ko1}%)")
    
    # Compare records
    wins1 = stats1['record_details']['wins']
    wins2 = stats2['record_details']['wins']
    if wins1 > wins2 + 10:
        advantages1.append(f"More experienced ({wins1} wins vs {wins2} wins)")
    elif wins2 > wins1 + 10:
        advantages2.append(f"More experienced ({wins2} wins vs {wins1} wins)")
    
    # Compare losses
    losses1 = stats1['record_details']['losses']
    losses2 = stats2['record_details']['losses']
    if losses1 < losses2:
        advantages1.append(f"Better defensive record ({losses1} losses vs {losses2} losses)")
    elif losses2 < losses1:
        advantages2.append(f"Better defensive record ({losses2} losses vs {losses1} losses)")
    
    # Compare reach
    reach1 = stats1['physical_stats']['reach_cm']
    reach2 = stats2['physical_stats']['reach_cm']
    reach_diff = abs(reach1 - reach2)
    if reach_diff > 5:
        if reach1 > reach2:
            advantages1.append(f"Longer reach ({reach1}cm vs {reach2}cm, +{reach_diff}cm advantage)")
        else:
            advantages2.append(f"Longer reach ({reach2}cm vs {reach1}cm, +{reach_diff}cm advantage)")
    
    # Compare titles
    titles1 = len(stats1['titles'])
    titles2 = len(stats2['titles'])
    if titles1 > titles2:
        advantages1.append(f"More championship experience ({titles1} titles vs {titles2} titles)")
    elif titles2 > titles1:
        advantages2.append(f"More championship experience ({titles2} titles vs {titles1} titles)")
    
    # Determine statistical favorite
    score1 = len(advantages1)
    score2 = len(advantages2)
    
    if score1 > score2:
        favorite = stats1['name']
        confidence = min(0.7 + (score1 - score2) * 0.1, 0.95)
    elif score2 > score1:
        favorite = stats2['name']
        confidence = min(0.7 + (score2 - score1) * 0.1, 0.95)
    else:
        favorite = "Too close to call"
        confidence = 0.5
    
    return {
        "fighter1": stats1['name'],
        "fighter2": stats2['name'],
        "fighter1_record": stats1['record'],
        "fighter2_record": stats2['record'],
        "fighter1_advantages": advantages1,
        "fighter2_advantages": advantages2,
        "statistical_favorite": favorite,
        "confidence": round(confidence, 2),
        "analysis": f"Based on {score1 + score2} key factors analyzed"
    }


async def search_fighters(
    query: str = "",
    weight_class: Optional[str] = None,
    active_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Search for fighters by name or criteria.
    
    Args:
        query: Search query (name or partial name)
        weight_class: Filter by weight class (optional)
        active_only: Only return active fighters (optional)
    
    Returns:
        List of matching fighters
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "SELECT * FROM fighters WHERE 1=1"
    params = []
    
    if query:
        sql += " AND LOWER(name) LIKE LOWER(?)"
        params.append(f"%{query}%")
    
    if weight_class:
        sql += " AND LOWER(weight_class) = LOWER(?)"
        params.append(weight_class)
    
    if active_only:
        sql += " AND active = 1"
    
    sql += " ORDER BY record_wins DESC LIMIT 10"
    
    cursor.execute(sql, params)
    fighters = cursor.fetchall()
    conn.close()
    
    return [
        {
            "name": f['name'],
            "nickname": f['nickname'],
            "record": format_record(f['record_wins'], f['record_losses'], f['record_draws']),
            "weight_class": f['weight_class'],
            "nationality": f['nationality'],
            "active": bool(f['active']),
            "ko_percentage": round(f['ko_percentage'], 1)
        }
        for f in fighters
    ]


async def fighter_career_timeline(name: str) -> Dict[str, Any]:
    """
    Get career timeline and milestones for a fighter.
    
    Args:
        name: Fighter's name
    
    Returns:
        Career timeline with key moments
    """
    # Get fighter stats first
    stats = await get_fighter_stats(name)
    if "error" in stats:
        return stats
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get fighter ID
    cursor.execute("SELECT id, debut_date FROM fighters WHERE LOWER(name) LIKE LOWER(?)", (f"%{name}%",))
    fighter = cursor.fetchone()
    
    if not fighter:
        conn.close()
        return {"error": f"Fighter '{name}' not found"}
    
    fighter_id = fighter['id']
    debut_date = fighter['debut_date']
    
    # Get all fights chronologically
    cursor.execute("""
        SELECT 
            f.date,
            f.method,
            f.round,
            f.title_fight,
            CASE 
                WHEN f.fighter1_id = ? THEN f2.name 
                ELSE f1.name 
            END as opponent,
            CASE 
                WHEN f.winner_id = ? THEN 'Win'
                WHEN f.winner_id IS NULL THEN 'Draw'
                ELSE 'Loss'
            END as result
        FROM fights f
        LEFT JOIN fighters f1 ON f.fighter1_id = f1.id
        LEFT JOIN fighters f2 ON f.fighter2_id = f2.id
        WHERE f.fighter1_id = ? OR f.fighter2_id = ?
        ORDER BY f.date ASC
    """, (fighter_id, fighter_id, fighter_id, fighter_id))
    
    fights = [dict(f) for f in cursor.fetchall()]
    
    # Get title reigns
    cursor.execute("""
        SELECT title_name, won_date, lost_date, defenses_count
        FROM titles
        WHERE fighter_id = ?
        ORDER BY won_date ASC
    """, (fighter_id,))
    
    titles = [dict(t) for t in cursor.fetchall()]
    conn.close()
    
    # Build milestones
    milestones = []
    
    # Debut
    if debut_date:
        milestones.append({
            "date": debut_date,
            "event": "Professional Debut",
            "significance": "Start of professional career"
        })
    
    # First title win
    if titles:
        first_title = titles[0]
        milestones.append({
            "date": first_title['won_date'],
            "event": f"Won {first_title['title_name']}",
            "significance": "First world championship"
        })
    
    # Notable fights (title fights, KO wins)
    for fight in fights:
        if fight['title_fight'] and fight['result'] == 'Win':
            milestones.append({
                "date": fight['date'],
                "event": f"Defeated {fight['opponent']} for title",
                "significance": f"{fight['method']} victory in round {fight['round']}"
            })
    
    # Career span
    career_span = None
    if debut_date and fights:
        try:
            # Handle both "YYYY" and "YYYY-MM-DD" formats
            if len(debut_date) == 4:  # Year only
                start = datetime(int(debut_date), 1, 1)
            else:
                start = datetime.strptime(debut_date, "%Y-%m-%d")
            
            last_fight = datetime.strptime(fights[-1]['date'], "%Y-%m-%d")
            years = (last_fight - start).days / 365
            career_span = {
                "debut_date": debut_date,
                "last_fight": fights[-1]['date'],
                "years": round(years, 1)
            }
        except:
            pass
    
    # Year by year stats
    year_stats = {}
    for fight in fights:
        year = fight['date'][:4]
        if year not in year_stats:
            year_stats[year] = {"wins": 0, "losses": 0, "draws": 0}
        
        if fight['result'] == 'Win':
            year_stats[year]['wins'] += 1
        elif fight['result'] == 'Loss':
            year_stats[year]['losses'] += 1
        else:
            year_stats[year]['draws'] += 1
    
    return {
        "fighter": stats['name'],
        "career_span": career_span,
        "total_fights": len(fights),
        "milestones": sorted(milestones, key=lambda x: x['date'])[:10],  # Top 10 milestones
        "year_by_year": [
            {"year": year, **stats}
            for year, stats in sorted(year_stats.items())
        ],
        "championship_reigns": len(titles)
    }


async def upcoming_fights(
    date_range: str = "30d",
    weight_class: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get upcoming scheduled fights from the database.
    
    Args:
        date_range: Range like "7d", "30d", "3m"
        weight_class: Filter by weight class (optional)
    
    Returns:
        List of upcoming fights
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Parse date range
    days_map = {"7d": 7, "30d": 30, "60d": 60, "90d": 90, "3m": 90, "6m": 180}
    days = days_map.get(date_range, 30)
    cutoff_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Build query
    query = """
        SELECT 
            f.date,
            f1.name as fighter1,
            f2.name as fighter2,
            f.title_fight,
            f.weight_class,
            f.location,
            f.status
        FROM fights f
        JOIN fighters f1 ON f.fighter1_id = f1.id
        JOIN fighters f2 ON f.fighter2_id = f2.id
        WHERE f.status = 'NOT_STARTED'
        AND f.date <= ?
        AND f.date >= date('now')
    """
    
    params = [cutoff_date]
    
    if weight_class:
        query += " AND LOWER(f.weight_class) = LOWER(?)"
        params.append(weight_class)
    
    query += " ORDER BY f.date ASC"
    
    cursor.execute(query, params)
    fights = cursor.fetchall()
    
    conn.close()
    
    return [
        {
            "date": fight['date'],
            "fighter1": fight['fighter1'],
            "fighter2": fight['fighter2'],
            "title_fight": bool(fight['title_fight']),
            "weight_class": fight['weight_class'] or "Unknown",
            "location": fight['location'] or "TBA",
            "status": fight['status']
        }
        for fight in fights
    ]


# Create MCP server
app = Server("boxing-analytics")


@app.list_tools()
async def list_tools():
    print("STEP 14: list_tools called", file=sys.stderr, flush=True)
    return [
        Tool(
            name="test_tool",
            description="Test tool",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    print(f"STEP 15: call_tool called: {name}", file=sys.stderr, flush=True)
    return [TextContent(type="text", text='{"status": "ok"}')]

async def main():
    print("STEP 16: main() started", file=sys.stderr, flush=True)
    try:
        async with stdio_server() as (read_stream, write_stream):
            print("STEP 17: stdio_server created", file=sys.stderr, flush=True)
            await app.run(read_stream, write_stream, app.create_initialization_options())
            print("STEP 18: app.run completed", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"STEP 16-18 FAILED: {e}", file=sys.stderr, flush=True)
        import traceback
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        raise

if __name__ == "__main__":
    print("STEP 19: Entry point", file=sys.stderr, flush=True)
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"STEP 19 FAILED: {e}", file=sys.stderr, flush=True)
        import traceback
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        sys.exit(1)