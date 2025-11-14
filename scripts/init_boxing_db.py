#!/usr/bin/env python3
"""
Boxing Data API - MAXIMUM REAL DATA EXTRACTION

Strategy: Aggressively query ALL available API endpoints to get maximum real data.
NO hardcoding, NO synthetic data - only real information from the API.

Approach:
1. Try multiple search variations to find more fighters
2. Use bulk queries extensively (they work better than per-fighter)
3. Try different pagination parameters
4. Explore all endpoint variations
5. Use aggressive caching to avoid rate limits
"""

import sqlite3
import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "boxing-data-api.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/v1"

RATE_LIMIT_DELAY = 1.0
CACHE_DIR = "data/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

api_calls_made = 0


def get_headers() -> Dict[str, str]:
    if not RAPIDAPI_KEY:
        raise ValueError("RAPIDAPI_KEY not found")
    return {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }


def rate_limited_request(url: str, cache_key: str = None, cache_ttl: int = 86400) -> Optional[Dict]:
    global api_calls_made
    
    if cache_key:
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        if os.path.exists(cache_file):
            cache_age = time.time() - os.path.getmtime(cache_file)
            if cache_age < cache_ttl:
                with open(cache_file, 'r') as f:
                    return json.load(f)
    
    try:
        time.sleep(RATE_LIMIT_DELAY)
        response = requests.get(url, headers=get_headers(), timeout=20)
        response.raise_for_status()
        data = response.json()
        api_calls_made += 1
        
        if cache_key:
            cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        
        return data
    except Exception as e:
        print(f"  ⚠️  {str(e)[:100]}")
        return None


def parse_height(height_str: str) -> Optional[int]:
    if not height_str:
        return None
    try:
        if 'cm' in height_str:
            cm_part = height_str.split('/')[-1].strip()
            return int(cm_part.replace('cm', '').strip())
    except:
        pass
    return None


def create_schema(conn: sqlite3.Connection):
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fighters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            nickname TEXT,
            nationality TEXT,
            weight_class TEXT,
            record_wins INTEGER DEFAULT 0,
            record_losses INTEGER DEFAULT 0,
            record_draws INTEGER DEFAULT 0,
            ko_percentage REAL DEFAULT 0.0,
            reach INTEGER,
            height INTEGER,
            stance TEXT,
            birth_date TEXT,
            debut_date TEXT,
            active BOOLEAN DEFAULT 1,
            boxing_api_id TEXT UNIQUE,
            age INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            fighter1_id INTEGER NOT NULL,
            fighter2_id INTEGER NOT NULL,
            winner_id INTEGER,
            method TEXT,
            round INTEGER,
            time TEXT,
            title_fight BOOLEAN DEFAULT 0,
            weight_class TEXT,
            location TEXT,
            status TEXT,
            boxing_api_id TEXT UNIQUE,
            FOREIGN KEY (fighter1_id) REFERENCES fighters(id),
            FOREIGN KEY (fighter2_id) REFERENCES fighters(id),
            FOREIGN KEY (winner_id) REFERENCES fighters(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS titles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fighter_id INTEGER NOT NULL,
            title_name TEXT NOT NULL,
            won_date TEXT NOT NULL,
            lost_date TEXT,
            defenses_count INTEGER DEFAULT 0,
            FOREIGN KEY (fighter_id) REFERENCES fighters(id)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fighters_name ON fighters(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fighters_weight_class ON fighters(weight_class)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fights_date ON fights(date)")
    
    conn.commit()


def insert_fighter(conn: sqlite3.Connection, fighter_data: Dict) -> Optional[int]:
    cursor = conn.cursor()
    
    stats = fighter_data.get('stats') or {}
    division = fighter_data.get('division') or {}
    
    name = fighter_data.get('name') or fighter_data.get('full_name')
    if not name:
        return None
    
    fighter = {
        'name': name,
        'nickname': fighter_data.get('nickname'),
        'nationality': fighter_data.get('nationality'),
        'weight_class': division.get('name', 'Unknown') if division else 'Unknown',
        'record_wins': stats.get('wins', 0),
        'record_losses': stats.get('losses', 0),
        'record_draws': stats.get('draws', 0),
        'ko_percentage': float(stats.get('ko_percentage', 0.0)),
        'reach': parse_height(fighter_data.get('reach')),
        'height': parse_height(fighter_data.get('height')),
        'stance': fighter_data.get('stance'),
        'birth_date': None,
        'debut_date': fighter_data.get('debut'),
        'active': True,
        'boxing_api_id': fighter_data.get('id') or fighter_data.get('fighter_id'),
        'age': fighter_data.get('age'),
        'description': None
    }
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO fighters (
                name, nickname, nationality, weight_class,
                record_wins, record_losses, record_draws, ko_percentage,
                reach, height, stance, birth_date, debut_date, active,
                boxing_api_id, age, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fighter['name'], fighter['nickname'], fighter['nationality'],
            fighter['weight_class'], fighter['record_wins'], fighter['record_losses'],
            fighter['record_draws'], fighter['ko_percentage'], fighter['reach'],
            fighter['height'], fighter['stance'], fighter['birth_date'],
            fighter['debut_date'], fighter['active'], fighter['boxing_api_id'],
            fighter['age'], fighter['description']
        ))
        conn.commit()
        
        cursor.execute("SELECT id FROM fighters WHERE name = ?", (fighter['name'],))
        result = cursor.fetchone()
        return result[0] if result else None
        
    except:
        return None


def insert_fight(conn: sqlite3.Connection, fight_data: Dict) -> Optional[int]:
    cursor = conn.cursor()
    
    fighters = fight_data.get('fighters', {}) or {}
    fighter1 = fighters.get('fighter_1') or {}
    fighter2 = fighters.get('fighter_2') or {}
    
    if not fighter1 or not fighter2:
        return None
    
    def get_or_create_fighter(fighter_info):
        api_id = fighter_info.get('id') or fighter_info.get('fighter_id')
        name = fighter_info.get('name') or fighter_info.get('full_name')
        
        if api_id:
            cursor.execute("SELECT id FROM fighters WHERE boxing_api_id = ?", (api_id,))
            row = cursor.fetchone()
            if row:
                return row[0]
        
        if name:
            cursor.execute("SELECT id FROM fighters WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return insert_fighter(conn, fighter_info)
        
        return None
    
    fighter1_id = get_or_create_fighter(fighter1)
    fighter2_id = get_or_create_fighter(fighter2)
    
    if not fighter1_id or not fighter2_id:
        return None
    
    division = fight_data.get('division') or {}
    date_str = fight_data.get('date', '')
    
    date = None
    if date_str:
        try:
            date = date_str.split('T')[0]
        except:
            pass
    
    method = None
    round_num = None
    winner_id = None
    results = fight_data.get('results')
    if results:
        method = results.get('outcome')
        round_num = results.get('round')
        try:
            round_num = int(round_num) if round_num else None
        except:
            round_num = None
        
        winner = results.get('winner')
        if winner == 'fighter_1':
            winner_id = fighter1_id
        elif winner == 'fighter_2':
            winner_id = fighter2_id
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO fights (
                date, fighter1_id, fighter2_id, winner_id, method, round,
                title_fight, weight_class, location, status, boxing_api_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date, fighter1_id, fighter2_id, winner_id, method, round_num,
            len(fight_data.get('titles', [])) > 0,
            division.get('name') if division else None,
            fight_data.get('location'),
            fight_data.get('status'),
            fight_data.get('id')
        ))
        conn.commit()
        return cursor.lastrowid
    except:
        return None


def explore_fighters_endpoint(conn: sqlite3.Connection) -> int:
    """Try different approaches to get maximum fighters from API."""
    print(f"\n🔍 Exploring /fighters endpoint with multiple strategies...")
    
    fighters_found = 0
    
    # Strategy 1: Get fighters with pagination
    print(f"\n   Strategy 1: Paginated queries...")
    for page in range(1, 6):  # Try 5 pages
        url = f"{BASE_URL}/fighters/?page={page}&page_size=100"
        data = rate_limited_request(url, cache_key=f"fighters_page_{page}", cache_ttl=86400)
        
        if data and isinstance(data, list):
            print(f"   Page {page}: Found {len(data)} fighters")
            for fighter in data:
                if insert_fighter(conn, fighter):
                    fighters_found += 1
            
            if len(data) < 100:  # Last page
                break
        else:
            break
    
    # Strategy 2: Search by single letters to catch different fighters
    print(f"\n   Strategy 2: Alphabet search...")
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        url = f"{BASE_URL}/fighters/?name={letter}&page_size=50"
        data = rate_limited_request(url, cache_key=f"fighters_search_{letter}", cache_ttl=86400)
        
        if data and isinstance(data, list) and len(data) > 0:
            print(f"   Letter '{letter}': Found {len(data)} fighters")
            for fighter in data:
                if insert_fighter(conn, fighter):
                    fighters_found += 1
    
    # Strategy 3: Search by weight class
    print(f"\n   Strategy 3: Weight class queries...")
    weight_classes = [
        "heavyweight", "cruiserweight", "light-heavyweight", "super-middleweight",
        "middleweight", "welterweight", "lightweight", "featherweight", "bantamweight"
    ]
    
    for weight in weight_classes:
        url = f"{BASE_URL}/fighters/?division={weight}&page_size=50"
        data = rate_limited_request(url, cache_key=f"fighters_weight_{weight}", cache_ttl=86400)
        
        if data and isinstance(data, list) and len(data) > 0:
            print(f"   {weight.title()}: Found {len(data)} fighters")
            for fighter in data:
                if insert_fighter(conn, fighter):
                    fighters_found += 1
    
    return fighters_found


def explore_fights_endpoint(conn: sqlite3.Connection) -> int:
    """Try different approaches to get maximum fights from API."""
    print(f"\n🥊 Exploring /fights endpoint with multiple strategies...")
    
    fights_found = 0
    fights_seen = set()
    
    # Strategy 1: Finished fights with pagination
    print(f"\n   Strategy 1: Finished fights (paginated)...")
    for page in range(1, 11):  # Try 10 pages
        url = f"{BASE_URL}/fights/?status=FINISHED&page={page}&page_size=100&date_sort=DESC"
        data = rate_limited_request(url, cache_key=f"fights_finished_page_{page}", cache_ttl=3600)
        
        if data and isinstance(data, list):
            print(f"   Page {page}: Found {len(data)} fights")
            for fight in data:
                fight_id = fight.get('id')
                if fight_id and fight_id not in fights_seen:
                    fights_seen.add(fight_id)
                    if insert_fight(conn, fight):
                        fights_found += 1
            
            if len(data) < 100:
                break
        else:
            break
    
    # Strategy 2: Upcoming fights
    print(f"\n   Strategy 2: Upcoming fights...")
    for days in [30, 60, 90, 180, 365]:
        url = f"{BASE_URL}/fights/schedule?days={days}"
        data = rate_limited_request(url, cache_key=f"fights_upcoming_{days}d", cache_ttl=3600)
        
        if data and isinstance(data, list):
            print(f"   Next {days} days: Found {len(data)} fights")
            for fight in data:
                fight_id = fight.get('id')
                if fight_id and fight_id not in fights_seen:
                    fights_seen.add(fight_id)
                    if insert_fight(conn, fight):
                        fights_found += 1
    
    # Strategy 3: Query by year
    print(f"\n   Strategy 3: Fights by year...")
    for year in range(2024, 2019, -1):  # Last 5 years
        url = f"{BASE_URL}/fights/?year={year}&page_size=100"
        data = rate_limited_request(url, cache_key=f"fights_year_{year}", cache_ttl=86400)
        
        if data and isinstance(data, list):
            print(f"   Year {year}: Found {len(data)} fights")
            for fight in data:
                fight_id = fight.get('id')
                if fight_id and fight_id not in fights_seen:
                    fights_seen.add(fight_id)
                    if insert_fight(conn, fight):
                        fights_found += 1
    
    # Strategy 4: For each fighter we have, try to get their fights
    print(f"\n   Strategy 4: Per-fighter fight queries...")
    cursor = conn.cursor()
    cursor.execute("SELECT boxing_api_id, name FROM fighters WHERE boxing_api_id IS NOT NULL LIMIT 100")
    fighters = cursor.fetchall()
    
    per_fighter_added = 0
    for api_id, name in fighters:
        url = f"{BASE_URL}/fights/?fighter_id={api_id}&page_size=50"
        data = rate_limited_request(url, cache_key=f"fights_fighter_{api_id}", cache_ttl=3600)
        
        if data and isinstance(data, list):
            for fight in data:
                fight_id = fight.get('id')
                if fight_id and fight_id not in fights_seen:
                    fights_seen.add(fight_id)
                    if insert_fight(conn, fight):
                        per_fighter_added += 1
                        fights_found += 1
    
    if per_fighter_added > 0:
        print(f"   Per-fighter queries: Added {per_fighter_added} additional fights")
    
    return fights_found


def main():
    print("="*70)
    print("BOXING DATA API - MAXIMUM REAL DATA EXTRACTION")
    print("="*70)
    
    if not RAPIDAPI_KEY:
        print("\n❌ ERROR: RAPIDAPI_KEY not found")
        print("\nSetup:")
        print("  1. Get API key from: https://rapidapi.com/bellingcat/api/boxing-data-api")
        print("  2. Add to .env: RAPIDAPI_KEY=your_key")
        return
    
    print(f"\n✅ API Key found")
    print(f"🎯 Strategy: Aggressive multi-strategy queries")
    print(f"   • Multiple pagination approaches")
    print(f"   • Alphabet search")
    print(f"   • Weight class filters")
    print(f"   • Year-based queries")
    print(f"   • Per-fighter deep dives")
    print(f"\n⏱️  This may take 5-15 minutes depending on API responses...\n")
    
    os.makedirs("data", exist_ok=True)
    db_path = "data/boxing_data.db"
    
    # Remove old database
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Removed old database\n")
    
    conn = sqlite3.connect(db_path)
    
    try:
        print("📊 Creating database schema...")
        create_schema(conn)
        print("  ✅ Schema created")
        
        # Explore all fighter endpoints
        fighters_added = explore_fighters_endpoint(conn)
        print(f"\n✅ Fighter collection complete: Found {fighters_added} unique fighters")
        
        # Explore all fight endpoints
        fights_added = explore_fights_endpoint(conn)
        print(f"\n✅ Fight collection complete: Found {fights_added} unique fights")
        
        # Final statistics
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fighters")
        total_fighters = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fights")
        total_fights = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fights WHERE status = 'FINISHED'")
        finished_fights = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fights WHERE status = 'NOT_STARTED'")
        upcoming_fights = cursor.fetchone()[0]
        
        # Top fighters by fight count
        cursor.execute("""
            SELECT f.name, COUNT(DISTINCT fi.id) as fight_count
            FROM fighters f
            LEFT JOIN fights fi ON (f.id = fi.fighter1_id OR f.id = fi.fighter2_id)
            GROUP BY f.id
            HAVING fight_count > 0
            ORDER BY fight_count DESC
            LIMIT 10
        """)
        top_fighters = cursor.fetchall()
        
        # Weight class distribution
        cursor.execute("""
            SELECT weight_class, COUNT(*) as count
            FROM fighters
            WHERE weight_class != 'Unknown'
            GROUP BY weight_class
            ORDER BY count DESC
            LIMIT 10
        """)
        weight_dist = cursor.fetchall()
        
        print("\n" + "="*70)
        print("✅ MAXIMUM DATA EXTRACTION COMPLETE!")
        print("="*70)
        
        print(f"\n📊 Final Statistics:")
        print(f"   Total fighters: {total_fighters}")
        print(f"   Total fights: {total_fights}")
        print(f"   - Finished: {finished_fights}")
        print(f"   - Upcoming: {upcoming_fights}")
        
        print(f"\n📈 Top 10 Fighters by Fight Count:")
        for name, count in top_fighters:
            print(f"   {name}: {count} fights")
        
        print(f"\n🥊 Top 10 Weight Classes:")
        for weight, count in weight_dist:
            print(f"   {weight}: {count} fighters")
        
        print(f"\n🌐 API Usage:")
        print(f"   API calls made: {api_calls_made}")
        print(f"   Rate limit remaining: {100 - api_calls_made}/100")
        
        print(f"\n💾 Database: {db_path}")
        print(f"💾 Cache: {CACHE_DIR}")
        
        print("\n✨ Database populated with REAL API data only!")
        print("   Next: python scripts/test_mcp_adapters.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()