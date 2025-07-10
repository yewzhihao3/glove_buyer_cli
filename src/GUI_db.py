import os
import sqlite3
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'results.db')

def load_unified_countries() -> List[str]:
    """Load all countries from both asia_countries.txt and global_countries.txt"""
    countries = set()
    
    # Load Asia countries
    asia_file = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'asia_countries.txt')
    if os.path.exists(asia_file):
        with open(asia_file, encoding="utf-8") as f:
            for line in f:
                country = line.strip()
                if country:
                    countries.add(country)
    
    # Load Global countries
    global_file = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'global_countries.txt')
    if os.path.exists(global_file):
        with open(global_file, encoding="utf-8") as f:
            for line in f:
                country = line.strip()
                if country:
                    countries.add(country)
    
    return sorted(list(countries))

def get_all_available_countries() -> List[str]:
    """Get all countries from both file lists and existing database entries"""
    # Start with countries from files
    file_countries = set(load_unified_countries())
    
    # Add countries from existing database entries
    try:
        init_db()
        db_countries = get_all_hs_codes()
        for entry in db_countries:
            file_countries.add(entry['country'])
    except:
        pass  # If database doesn't exist yet, just use file countries
    
    return sorted(list(file_countries))

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Create a single hs_codes table for all countries
    c.execute('''
        CREATE TABLE IF NOT EXISTS hs_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT NOT NULL,
            description TEXT NOT NULL,
            country TEXT NOT NULL,
            source TEXT DEFAULT 'Manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(hs_code, country)
        )
    ''')
    conn.commit()
    conn.close()

def save_hs_code(hs_code: str, description: str, country: str, source: str = 'Manual') -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO hs_codes (hs_code, description, country, source) VALUES (?, ?, ?, ?)', (hs_code, description, country, source))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def update_hs_code(hs_code_id: int, new_hs_code: str, new_description: str, new_country: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE hs_codes SET hs_code = ?, description = ?, country = ? WHERE id = ?', (new_hs_code, new_description, new_country, hs_code_id))
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated

def delete_hs_code(hs_code_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM hs_codes WHERE id = ?', (hs_code_id,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted

def get_all_hs_codes() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, hs_code, description, country, source, created_at FROM hs_codes ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    columns = ['id', 'hs_code', 'description', 'country', 'source', 'created_at']
    return [dict(zip(columns, row)) for row in rows]

def get_hs_codes_by_country(country: str) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, hs_code, description, country, source, created_at FROM hs_codes WHERE country = ? ORDER BY created_at DESC', (country,))
    rows = c.fetchall()
    conn.close()
    columns = ['id', 'hs_code', 'description', 'country', 'source', 'created_at']
    return [dict(zip(columns, row)) for row in rows]

def get_hs_code_by_id(hs_code_id: int) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, hs_code, description, country, source, created_at FROM hs_codes WHERE id = ?', (hs_code_id,))
    row = c.fetchone()
    conn.close()
    if row:
        columns = ['id', 'hs_code', 'description', 'country', 'source', 'created_at']
        return dict(zip(columns, row))
    return None 