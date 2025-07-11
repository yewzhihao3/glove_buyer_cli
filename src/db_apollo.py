import sqlite3
import os
from datetime import datetime

APOLLO_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'Apollo.db')

def init_apollo_db():
    conn = sqlite3.connect(APOLLO_DB_PATH)
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
    # Contacts table (now with company_name field)
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
    from datetime import datetime
    conn = sqlite3.connect(APOLLO_DB_PATH)
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
    conn = sqlite3.connect(APOLLO_DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM companies')
    rows = c.fetchall()
    conn.close()
    # Return as list of dicts
    columns = [desc[0] for desc in c.description]
    return [dict(zip(columns, row)) for row in rows]

def count_companies():
    """Count total companies in the database"""
    conn = sqlite3.connect(APOLLO_DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM companies')
    count = c.fetchone()[0]
    conn.close()
    return count

def insert_contact(company_id, company_name, name, title, email, linkedin, source="Apollo", created_at=None):
    """Insert a contact (buyer/decision maker) for a company. Returns contact id."""
    if created_at is None:
        created_at = datetime.utcnow().isoformat()
    conn = sqlite3.connect(APOLLO_DB_PATH)
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
    """Get all contacts for a given company_id."""
    conn = sqlite3.connect(APOLLO_DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM contacts WHERE company_id = ?', (company_id,))
    rows = c.fetchall()
    columns = [desc[0] for desc in c.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

def get_available_countries_asia():
    """Return sorted list of Asia countries present in the companies table."""
    asia_countries = set([
        'Malaysia','Indonesia','Thailand','Vietnam','Singapore','Philippines','China','India','Japan','South Korea','Hong Kong','Taiwan','Bangladesh','Pakistan','Sri Lanka','Myanmar','Cambodia','Laos','Nepal','Mongolia','Brunei','Timor-Leste','Maldives','Bhutan'
    ])
    conn = sqlite3.connect(APOLLO_DB_PATH)
    c = conn.cursor()
    c.execute('SELECT DISTINCT country FROM companies')
    db_countries = set(row[0].strip() for row in c.fetchall() if row[0])
    conn.close()
    return sorted(list(asia_countries & db_countries))

def get_available_countries_global():
    """Return sorted list of Global countries present in the companies table, always showing 'United States' instead of 'USA'."""
    global_countries = set([
        'United States','Germany','United Kingdom','France','Italy','Spain','Canada','Australia','Brazil','Mexico','Russia','Turkey','Netherlands','Switzerland','Sweden','Norway','Denmark','Finland','Poland','Austria','Belgium','South Africa','Egypt','Saudi Arabia','UAE','Argentina','Chile','New Zealand','Ireland','Portugal','Greece','Czech Republic','Hungary','Romania','Israel','Ukraine'
    ])
    conn = sqlite3.connect(APOLLO_DB_PATH)
    c = conn.cursor()
    c.execute('SELECT DISTINCT country FROM companies')
    db_countries = set(row[0].strip() for row in c.fetchall() if row[0])
    # Map all US variants to 'United States' for display and comparison
    us_aliases = {'USA', 'US', 'U.S.A.', 'U.S.A', 'U.S.', 'United States of America'}
    db_countries_mapped = set('United States' if c in us_aliases or c == 'United States' else c for c in db_countries)
    conn.close()
    return sorted(list(global_countries & db_countries_mapped)) 

def get_all_contacts():
    """Return all contacts (potential buyers) as a list of dicts."""
    conn = sqlite3.connect(APOLLO_DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM contacts')
    rows = c.fetchall()
    columns = [desc[0] for desc in c.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

def update_contact(contact_id, updated_fields):
    """Update a contact by id. updated_fields is a dict of column:value."""
    if not updated_fields:
        return False
    conn = sqlite3.connect(APOLLO_DB_PATH)
    c = conn.cursor()
    set_clause = ', '.join([f"{k} = ?" for k in updated_fields.keys()])
    values = list(updated_fields.values()) + [contact_id]
    c.execute(f'UPDATE contacts SET {set_clause} WHERE id = ?', values)
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0

def delete_contact(contact_id):
    """Delete a contact by id."""
    conn = sqlite3.connect(APOLLO_DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0

def find_duplicate_contacts():
    """Find duplicate contacts by email or (name+company_name). Returns a list of lists of duplicate contact dicts."""
    conn = sqlite3.connect(APOLLO_DB_PATH)
    c = conn.cursor()
    # By email
    c.execute('SELECT email FROM contacts WHERE email IS NOT NULL AND email != "" GROUP BY email HAVING COUNT(*) > 1')
    dup_emails = [row[0] for row in c.fetchall()]
    duplicates = []
    for email in dup_emails:
        c.execute('SELECT * FROM contacts WHERE email = ?', (email,))
        rows = c.fetchall()
        columns = [desc[0] for desc in c.description]
        duplicates.append([dict(zip(columns, row)) for row in rows])
    # By (name+company_name)
    c.execute('SELECT name, company_name FROM contacts WHERE name IS NOT NULL AND company_name IS NOT NULL GROUP BY name, company_name HAVING COUNT(*) > 1')
    for name, company_name in c.fetchall():
        c.execute('SELECT * FROM contacts WHERE name = ? AND company_name = ?', (name, company_name))
        rows = c.fetchall()
        columns = [desc[0] for desc in c.description]
        group = [dict(zip(columns, row)) for row in rows]
        if len(group) > 1 and group not in duplicates:
            duplicates.append(group)
    conn.close()
    return duplicates 