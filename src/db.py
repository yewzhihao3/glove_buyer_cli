import os
import sqlite3
from typing import List, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'results.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create results table
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT,
            keyword TEXT,
            country TEXT,
            company_name TEXT,
            company_country TEXT,
            company_website_link TEXT,
            description TEXT,
            source TEXT,
            UNIQUE(hs_code, keyword, country, company_name)
        )
    ''')
    
    # Create country_hs_codes table for country-specific HS codes
    c.execute('''
        CREATE TABLE IF NOT EXISTS country_hs_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            hs_code TEXT NOT NULL,
            description TEXT NOT NULL,
            source TEXT DEFAULT 'DeepSeek',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country, hs_code)
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_results(hs_code: str, keyword: str, country: str, companies: List[Dict]):
    """
    Insert a list of company dicts into the database. Each dict should have:
    company_name, company_country, company_website_link, description
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for company in companies:
        c.execute('''
            INSERT OR IGNORE INTO results
            (hs_code, keyword, country, company_name, company_country, company_website_link, description, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            hs_code,
            keyword,
            country,
            company.get('company_name', ''),
            company.get('company_country', ''),
            company.get('company_website_link', ''),
            company.get('description', ''),
            'DeepSeek R1'
        ))
    conn.commit()
    conn.close()

def parse_deepseek_output(output: str) -> List[Dict]:
    """
    Parse DeepSeek output into a list of company dicts.
    Handles:
    - Markdown-style output with numbered company blocks and fields, with colon inside or outside bold.
    - Company name as bolded header (e.g., 1. **PT Medisafe Technologies**)
    - Fields like '**Company Name**: Value' (extracts value after colon)
    Captures multi-line descriptions and brief descriptions. Cleans website/email fields.
    """
    import re
    # Remove all Markdown bold formatting
    output = output.replace('**', '')
    companies = []
    # Split into blocks by numbered list (e.g., 1. **Company Name**...)
    blocks = re.split(r'\n\d+\. ', '\n' + output)
    for block in blocks:
        if not block.strip():
            continue
        company = {}
        # Company Name: match 'Company Name: Value' or header
        m = re.search(r'Company Name:?.*?([\w\W]*?)(?:\n|$)', block)
        if m and m.group(1).strip():
            company['company_name'] = m.group(1).strip().replace('\n', ' ')
        else:
            m = re.match(r'(.+)', block)
            if m:
                company['company_name'] = m.group(1).strip().replace('\n', ' ')
        # Country
        m = re.search(r'Country:?.*?([\w\W]*?)(?:\n|$)', block)
        if m and m.group(1).strip():
            company['company_country'] = m.group(1).strip()
        # Website: extract only the first valid URL after 'Website:'
        m = re.search(r'Website:?.*?([\w\W]*?)(?:\n|$)', block)
        if m and m.group(1).strip():
            url_match = re.search(r'(https?://[\w\.-]+[\w\d/#?&=\.-]*)', m.group(1))
            if url_match:
                company['company_website_link'] = url_match.group(1).strip()
        # Multi-line Description or Brief Description (prefer Description, fallback to Brief Description)
        desc_match = re.search(r'Description:?.*?([\w\W]*?)(?=\n- |$)', block, re.DOTALL)
        if desc_match and desc_match.group(1).strip():
            description = desc_match.group(1).strip()
            description = '\n'.join(line.lstrip('-').strip() for line in description.splitlines() if line.strip())
            company['description'] = description
        else:
            desc_match = re.search(r'Brief Description:?.*?([\w\W]*?)(?=\n- |$)', block, re.DOTALL)
            if desc_match and desc_match.group(1).strip():
                description = desc_match.group(1).strip()
                description = '\n'.join(line.lstrip('-').strip() for line in description.splitlines() if line.strip())
                company['description'] = description
        if company.get('company_name'):
            companies.append(company)
    print("DEBUG: Parsed company names:", [c['company_name'] for c in companies])
    return companies

def fetch_all_results():
    """
    Fetch all past results from the database, ordered by most recent (id DESC).
    Returns a list of dicts with all columns.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, hs_code, keyword, country, company_name, company_country, company_website_link, description, source FROM results ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    columns = [
        'id', 'hs_code', 'keyword', 'country', 'company_name', 'company_country', 'company_website_link', 'description', 'source'
    ]
    return [dict(zip(columns, row)) for row in rows]

def update_result(record_id: int, updated_fields: dict) -> bool:
    """
    Update a buyer search history record by its ID. updated_fields is a dict of column:value pairs to update.
    Returns True if a record was updated, False otherwise.
    """
    allowed_fields = {'hs_code', 'keyword', 'country', 'company_name', 'company_country', 'company_website_link', 'description', 'source'}
    set_clause = ', '.join([f"{k} = ?" for k in updated_fields if k in allowed_fields])
    values = [updated_fields[k] for k in updated_fields if k in allowed_fields]
    if not set_clause:
        return False
    values.append(record_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f'UPDATE results SET {set_clause} WHERE id = ?', values)
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated

def delete_result(record_id: int) -> bool:
    """
    Delete a buyer search history record by its ID.
    Returns True if a record was deleted, False otherwise.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM results WHERE id = ?', (record_id,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted

def get_country_hs_codes(country: str) -> List[Dict]:
    """
    Get HS codes for a specific country from the database.
    Returns a list of dicts with 'hs_code' and 'description' keys.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT hs_code, description FROM country_hs_codes WHERE country = ? ORDER BY created_at DESC', (country,))
    rows = c.fetchall()
    conn.close()
    return [{'hs_code': row[0], 'description': row[1]} for row in rows]

def save_country_hs_code(country: str, hs_code: str, description: str, source: str = 'DeepSeek') -> bool:
    """
    Save a country-specific HS code to the database.
    Returns True if successful, False if duplicate.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO country_hs_codes (country, hs_code, description, source)
            VALUES (?, ?, ?, ?)
        ''', (country, hs_code, description, source))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Duplicate entry
        success = False
    conn.close()
    return success

def update_country_hs_code(country: str, old_hs_code: str, new_hs_code: str, new_description: str) -> bool:
    """
    Update an existing country-specific HS code.
    Returns True if successful, False if not found.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE country_hs_codes 
        SET hs_code = ?, description = ?
        WHERE country = ? AND hs_code = ?
    ''', (new_hs_code, new_description, country, old_hs_code))
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated

def delete_country_hs_code(country: str, hs_code: str) -> bool:
    """
    Delete a country-specific HS code.
    Returns True if successful, False if not found.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM country_hs_codes WHERE country = ? AND hs_code = ?', (country, hs_code))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted

def get_all_country_hs_codes() -> List[Dict]:
    """
    Get all country-specific HS codes from the database.
    Returns a list of dicts with all columns.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, country, hs_code, description, source, created_at 
        FROM country_hs_codes 
        ORDER BY country, created_at DESC
    ''')
    rows = c.fetchall()
    conn.close()
    columns = ['id', 'country', 'hs_code', 'description', 'source', 'created_at']
    return [dict(zip(columns, row)) for row in rows] 