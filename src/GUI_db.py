import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

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

# Potential Buyer database functions
def init_apollo_db():
    """Initialize Potential Buyer database tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Companies table
    c.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            country TEXT,
            domain TEXT,
            industry TEXT,
            employee_count INTEGER,
            source TEXT,
            created_at TEXT
        )
    ''')
    # Contacts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            company_name TEXT,
            name TEXT,
            title TEXT,
            email TEXT,
            linkedin TEXT,
            source TEXT,
            created_at TEXT,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
    ''')
    conn.commit()
    conn.close()

def insert_company(company_name, country, domain, industry, employee_count, source="Apollo"):
    """Insert a company into database"""
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    # Check for existing by domain or (name+country)
    c.execute("SELECT id FROM companies WHERE domain = ? OR (company_name = ? AND country = ?)", (domain, company_name, country))
    row = c.fetchone()
    if row:
        conn.close()
        return row[0], False  # Return existing company id, not new
    c.execute('''
        INSERT INTO companies (company_name, country, domain, industry, employee_count, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (company_name, country, domain, industry, employee_count, source, created_at))
    company_id = c.lastrowid
    conn.commit()
    conn.close()
    return company_id, True  # Return new company id, is new

def get_all_companies():
    """Get all companies from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM companies')
    rows = c.fetchall()
    conn.close()
    # Return as list of dicts
    columns = [desc[0] for desc in c.description]
    return [dict(zip(columns, row)) for row in rows]

def count_companies():
    """Count total companies in database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM companies')
    count = c.fetchone()[0]
    conn.close()
    return count

def insert_contact(company_id, company_name, name, title, email, linkedin, source="Apollo", created_at=None):
    """Insert a contact (buyer/decision maker) for a company"""
    if created_at is None:
        created_at = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO contacts (company_id, company_name, name, title, email, linkedin, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (company_id, company_name, name, title, email, linkedin, source, created_at))
    contact_id = c.lastrowid
    conn.commit()
    conn.close()
    return contact_id

def get_contacts_by_company(company_id):
    """Get all contacts for a given company_id"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM contacts WHERE company_id = ?', (company_id,))
    rows = c.fetchall()
    columns = [desc[0] for desc in c.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

def get_available_countries():
    """Return sorted list of all countries present in the companies table"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT DISTINCT country FROM companies WHERE country IS NOT NULL AND country != ""')
    countries = [row[0].strip() for row in c.fetchall() if row[0]]
    conn.close()
    return sorted(list(set(countries)))

def get_all_contacts():
    """Return all contacts (potential buyers) as a list of dicts"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM contacts')
    rows = c.fetchall()
    columns = [desc[0] for desc in c.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows] 