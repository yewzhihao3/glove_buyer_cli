import os
import sqlite3
from typing import List, Dict, Optional

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database.db'))

def init_db():
    # Ensure the database directory exists (project root)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:  # Only create directory if there is one
        os.makedirs(db_dir, exist_ok=True)
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
    
    # Create asia_hs_codes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS asia_hs_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT NOT NULL,
            description TEXT NOT NULL,
            country TEXT NOT NULL,
            source TEXT DEFAULT 'Manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(hs_code, country)
        )
    ''')
    
    # Create global_hs_codes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS global_hs_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT NOT NULL,
            description TEXT NOT NULL,
            country TEXT NOT NULL,
            source TEXT DEFAULT 'Manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(hs_code, country)
        )
    ''')
    
    # Create international_hs_codes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS international_hs_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        )
    ''')
    
    # Create asia_buyer_leads table
    c.execute('''
        CREATE TABLE IF NOT EXISTS asia_buyer_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT,
            keyword TEXT,
            company_name TEXT,
            company_country TEXT,
            company_website_link TEXT,
            description TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(hs_code, keyword, company_name)
        )
    ''')

    # Create global_buyer_leads table
    c.execute('''
        CREATE TABLE IF NOT EXISTS global_buyer_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT,
            keyword TEXT,
            company_name TEXT,
            company_country TEXT,
            company_website_link TEXT,
            description TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(hs_code, keyword, company_name)
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

def check_existing_buyer_results(hs_code: str, keyword: str, country: str) -> List[Dict]:
    """
    Check if we already have buyer results for the given HS code, keyword, and country combination.
    Returns a list of existing company results if found, empty list if none.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT company_name, company_country, company_website_link, description, source 
        FROM results 
        WHERE hs_code = ? AND keyword = ? AND country = ?
        ORDER BY id DESC
    ''', (hs_code, keyword, country))
    rows = c.fetchall()
    conn.close()
    columns = ['company_name', 'company_country', 'company_website_link', 'description', 'source']
    return [dict(zip(columns, row)) for row in rows]

def find_and_remove_duplicates() -> Dict:
    """
    Find and remove duplicate companies based on company_name and company_country.
    Returns a dict with counts of duplicates found and removed.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Find duplicates based on company_name and company_country
    c.execute('''
        SELECT company_name, company_country, COUNT(*) as count
        FROM results 
        GROUP BY company_name, company_country 
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    ''')
    duplicates = c.fetchall()
    
    total_duplicates_found = 0
    total_duplicates_removed = 0
    
    for company_name, company_country, count in duplicates:
        total_duplicates_found += count
        
        # Get all records for this company (ordered by id to keep the oldest)
        c.execute('''
            SELECT id, company_name, company_country, company_website_link, description, source
            FROM results 
            WHERE company_name = ? AND company_country = ?
            ORDER BY id ASC
        ''', (company_name, company_country))
        
        records = c.fetchall()
        
        # Keep the first record (oldest), delete the rest
        if len(records) > 1:
            # Delete all but the first record
            ids_to_delete = [str(record[0]) for record in records[1:]]
            placeholders = ','.join(['?' for _ in ids_to_delete])
            
            c.execute(f'''
                DELETE FROM results 
                WHERE id IN ({placeholders})
            ''', ids_to_delete)
            
            total_duplicates_removed += len(records) - 1
    
    conn.commit()
    conn.close()
    
    return {
        'duplicates_found': total_duplicates_found,
        'duplicates_removed': total_duplicates_removed,
        'duplicate_groups': len(duplicates)
    }

def get_duplicate_summary() -> List[Dict]:
    """
    Get a summary of duplicate companies without removing them.
    Returns a list of dicts with duplicate information.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT company_name, company_country, COUNT(*) as count
        FROM results 
        GROUP BY company_name, company_country 
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    ''')
    duplicates = c.fetchall()
    conn.close()
    
    return [
        {
            'company_name': row[0],
            'company_country': row[1],
            'duplicate_count': row[2]
        }
        for row in duplicates
    ]

# CRUD for asia_hs_codes
def get_all_asia_hs_codes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, hs_code, description, country, source, created_at FROM asia_hs_codes ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    columns = ['id', 'hs_code', 'description', 'country', 'source', 'created_at']
    return [dict(zip(columns, row)) for row in rows]

def save_asia_hs_code(hs_code: str, description: str, country: str, source: str = 'Manual') -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO asia_hs_codes (hs_code, description, country, source) VALUES (?, ?, ?, ?)', (hs_code, description, country, source))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def update_asia_hs_code(hs_code_id: int, new_hs_code: str, new_description: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE asia_hs_codes SET hs_code = ?, description = ? WHERE id = ?', (new_hs_code, new_description, hs_code_id))
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated

def delete_asia_hs_code(hs_code_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM asia_hs_codes WHERE id = ?', (hs_code_id,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted

# CRUD for global_hs_codes
def get_all_global_hs_codes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, hs_code, description, country, source, created_at FROM global_hs_codes ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    columns = ['id', 'hs_code', 'description', 'country', 'source', 'created_at']
    return [dict(zip(columns, row)) for row in rows]

def save_global_hs_code(hs_code: str, description: str, country: str, source: str = 'Manual') -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO global_hs_codes (hs_code, description, country, source) VALUES (?, ?, ?, ?)', (hs_code, description, country, source))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def update_global_hs_code(hs_code_id: int, new_hs_code: str, new_description: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE global_hs_codes SET hs_code = ?, description = ? WHERE id = ?', (new_hs_code, new_description, hs_code_id))
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated

def delete_global_hs_code(hs_code_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM global_hs_codes WHERE id = ?', (hs_code_id,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted

def init_international_hs_codes():
    """
    Create the international_hs_codes table and insert initial codes if not present.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS international_hs_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hs_code TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        )
    ''')
    # Check if table is empty
    c.execute('SELECT COUNT(*) FROM international_hs_codes')
    count = c.fetchone()[0]
    if count == 0:
        codes = [
            ("4015.12.1000", "Surgical Gloves"),
            ("4015.19.1000", "Industrial Gloves"),
            ("4015.12.9000", "Other Surgical"),
            ("4015.19.9000", "Other Industrial"),
            ("3926.20.1090", "Plastic Protective Gloves"),
            ("6116.10.0000", "Textile Gloves"),
            ("6216.00.4600", "Other Gloves (Fabric)")
        ]
        c.executemany('INSERT INTO international_hs_codes (hs_code, description) VALUES (?, ?)', codes)
        conn.commit()
    conn.close()

def get_all_international_hs_codes():
    """
    Fetch all international HS codes from the static table.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT hs_code, description FROM international_hs_codes ORDER BY id ASC')
    rows = c.fetchall()
    conn.close()
    return [{'hs_code': row[0], 'description': row[1]} for row in rows]

def check_existing_buyer_leads(scope: str, hs_code: str, keyword: str) -> List[Dict]:
    """
    Check if we already have buyer leads for the given scope, HS code, and keyword combination.
    Returns a list of existing company results if found, empty list if none.
    """
    table = {
        'Asia': 'asia_buyer_leads',
        'Global': 'global_buyer_leads',
        'International': 'results',  # Use the main results table for international
    }[scope]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if scope == 'International':
        # For international, we need to check the results table which has a country column
        c.execute(f'''
            SELECT company_name, company_country, company_website_link, description, source 
            FROM {table} 
            WHERE hs_code = ? AND keyword = ?
            ORDER BY id DESC
        ''', (hs_code, keyword))
    else:
        # For Asia and Global, use the buyer leads tables
        c.execute(f'''
            SELECT company_name, company_country, company_website_link, description, source 
            FROM {table} 
            WHERE hs_code = ? AND keyword = ?
            ORDER BY id DESC
        ''', (hs_code, keyword))
    
    rows = c.fetchall()
    conn.close()
    columns = ['company_name', 'company_country', 'company_website_link', 'description', 'source']
    return [dict(zip(columns, row)) for row in rows]

def insert_buyer_leads(scope: str, hs_code: str, keyword: str, companies: List[Dict]):
    """
    Insert a list of company dicts into the appropriate buyer leads table.
    Each dict should have: company_name, company_country, company_website_link, description
    """
    table = {
        'Asia': 'asia_buyer_leads',
        'Global': 'global_buyer_leads',
        'International': 'results',  # Use the main results table for international
    }[scope]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for company in companies:
        if scope == 'International':
            # For international, we need to include the country column
            c.execute(f'''
                INSERT OR IGNORE INTO {table}
                (hs_code, keyword, country, company_name, company_country, company_website_link, description, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hs_code,
                keyword,
                'International',  # Use 'International' as the country for international scope
                company.get('company_name', ''),
                company.get('company_country', ''),
                company.get('company_website_link', ''),
                company.get('description', ''),
                'DeepSeek R1'
            ))
        else:
            # For Asia and Global, use the buyer leads tables
            c.execute(f'''
                INSERT OR IGNORE INTO {table}
                (hs_code, keyword, company_name, company_country, company_website_link, description, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                hs_code,
                keyword,
                company.get('company_name', ''),
                company.get('company_country', ''),
                company.get('company_website_link', ''),
                company.get('description', ''),
                'DeepSeek R1'
            ))
    conn.commit()
    conn.close()

def fetch_all_buyer_leads(scope: str) -> List[Dict]:
    """
    Fetch all buyer leads from the specified scope table, ordered by most recent (id DESC).
    Returns a list of dicts with all columns.
    """
    table = {
        'Asia': 'asia_buyer_leads',
        'Global': 'global_buyer_leads',
        'International': 'results',  # Use the main results table for international
    }[scope]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if scope == 'International':
        # For international, we need to handle the results table which has a country column
        c.execute(f'SELECT id, hs_code, keyword, country, company_name, company_country, company_website_link, description, source FROM {table} ORDER BY id DESC')
        columns = ['id', 'hs_code', 'keyword', 'country', 'company_name', 'company_country', 'company_website_link', 'description', 'source']
    else:
        # For Asia and Global, use the buyer leads tables
        c.execute(f'SELECT id, hs_code, keyword, company_name, company_country, company_website_link, description, source, created_at FROM {table} ORDER BY id DESC')
        columns = ['id', 'hs_code', 'keyword', 'company_name', 'company_country', 'company_website_link', 'description', 'source', 'created_at']
    
    rows = c.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

def get_all_asia_buyer_leads() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, hs_code, keyword, company_name, company_country, company_website_link, description, source, created_at FROM asia_buyer_leads ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    columns = ['id', 'hs_code', 'keyword', 'company_name', 'company_country', 'company_website_link', 'description', 'source', 'created_at']
    return [dict(zip(columns, row)) for row in rows]

def get_all_global_buyer_leads() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, hs_code, keyword, company_name, company_country, company_website_link, description, source, created_at FROM global_buyer_leads ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    columns = ['id', 'hs_code', 'keyword', 'company_name', 'company_country', 'company_website_link', 'description', 'source', 'created_at']
    return [dict(zip(columns, row)) for row in rows]

def get_asia_buyer_leads_by_country(country: str) -> List[Dict]:
    """
    Get all Asia buyer leads for a specific country.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, hs_code, keyword, company_name, company_country, company_website_link, description, source, created_at 
        FROM asia_buyer_leads 
        WHERE company_country LIKE ? 
        ORDER BY id DESC
    ''', (f'%{country}%',))
    rows = c.fetchall()
    conn.close()
    columns = ['id', 'hs_code', 'keyword', 'company_name', 'company_country', 'company_website_link', 'description', 'source', 'created_at']
    return [dict(zip(columns, row)) for row in rows]

def get_global_buyer_leads_by_country(country: str) -> List[Dict]:
    """
    Get all Global buyer leads for a specific country.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, hs_code, keyword, company_name, company_country, company_website_link, description, source, created_at 
        FROM global_buyer_leads 
        WHERE company_country LIKE ? 
        ORDER BY id DESC
    ''', (f'%{country}%',))
    rows = c.fetchall()
    conn.close()
    columns = ['id', 'hs_code', 'keyword', 'company_name', 'company_country', 'company_website_link', 'description', 'source', 'created_at']
    return [dict(zip(columns, row)) for row in rows]

def get_buyer_lead_by_id(scope: str, record_id: int) -> Optional[Dict]:
    """
    Get a specific buyer lead by ID from the specified scope.
    """
    table = {
        'Asia': 'asia_buyer_leads',
        'Global': 'global_buyer_leads',
    }[scope]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f'''
        SELECT id, hs_code, keyword, company_name, company_country, company_website_link, description, source, created_at 
        FROM {table} 
        WHERE id = ?
    ''', (record_id,))
    row = c.fetchone()
    conn.close()
    if row:
        columns = ['id', 'hs_code', 'keyword', 'company_name', 'company_country', 'company_website_link', 'description', 'source', 'created_at']
        return dict(zip(columns, row))
    return None

def get_available_countries_asia() -> List[str]:
    """
    Get list of countries that have companies in the Asia buyer leads table.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT company_country 
        FROM asia_buyer_leads 
        WHERE company_country IS NOT NULL AND company_country != ''
        ORDER BY company_country
    ''')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_available_countries_global() -> List[str]:
    """
    Get list of countries that have companies in the Global buyer leads table.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT company_country 
        FROM global_buyer_leads 
        WHERE company_country IS NOT NULL AND company_country != ''
        ORDER BY company_country
    ''')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]