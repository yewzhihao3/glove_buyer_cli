import re
from typing import Optional, List, Dict
import os
import requests
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv(dotenv_path)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
if APOLLO_API_KEY:
    pass

APOLLO_BASE_URL = "https://api.apollo.io/v1"

ROLE_KEYWORDS = [
    "procurement", "import", "supply chain", "purchasing",
    "buyer", "sourcing", "logistics", "operations",
    "manager", "director"
]

LEGAL_SUFFIXES = [
    r"sdn bhd", r"pte ltd", r"ltd", r"inc", r"llc", r"co\.?", r"corp\.?", r"plc", r"gmbh", r"sa",
    r"ag", r"bv", r"oy", r"sarl", r"sas", r"kg", r"kft", r"ab", r"as", r"nv", r"oyj", r"aps", r"a/s",
    r"sp z o\.o\.", r"spolka z ograniczona odpowiedzialnoscia"
]

def clean_company_name(company_name: str) -> str:
    pattern = re.compile(r"\b(?:" + "|".join(LEGAL_SUFFIXES) + r")\b", re.IGNORECASE)
    cleaned = pattern.sub("", company_name)
    return re.sub(r"\s+", " ", cleaned).strip()

def is_valid_domain(domain: str) -> bool:
    if not domain:
        return False
    domain = domain.strip().lower()
    if "@" in domain or " " in domain or "." not in domain:
        return False
    tlds = [".com", ".net", ".org", ".co", ".my", ".sg", ".id", ".cn", ".jp", ".us", ".uk"]
    return any(domain.endswith(tld) for tld in tlds)

def filter_people_by_role(people: List[Dict]) -> List[Dict]:
    filtered = []
    for person in people:
        title = (person.get("title") or "").lower()
        if any(role in title for role in ROLE_KEYWORDS):
            filtered.append(person)
    return filtered

def get_linkedin_url(person: Dict) -> str:
    if person.get("linkedin_url"):
        return person["linkedin_url"]
    if person.get("social_links"):
        for link in person["social_links"]:
            if "linkedin.com" in link:
                return link
    return ""

def reveal_email_apollo(person_id: str) -> str:
    """Reveal the email for a person using Apollo enrichment API (consumes credits)."""
    if not APOLLO_API_KEY:
        print("[red]Apollo.io API key not found in environment! Cannot reveal email.[/red]")
        return ""
    url = f"https://api.apollo.io/v1/people/match"
    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY
    }
    body = {
        "person_id": person_id,
        "reveal_personal_emails": True
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        # Try to get the most accurate email field
        person = data.get("person", {})
        email = person.get("email") or person.get("personal_email") or person.get("work_email")
        return email or ""
    except Exception as e:
        print(f"[red]Error revealing email for person_id {person_id}: {e}[/red]")
        return ""

def find_decision_makers_apollo(company_name: str, country: str, website: Optional[str] = None) -> List[Dict]:
    if not APOLLO_API_KEY:
        print("[red]Apollo.io API key not found in environment![/red]")
        return []

    cleaned_name = clean_company_name(company_name)
    valid_website = website if is_valid_domain(website or "") else None

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY
    }

    body = {
        "q_organization_name": cleaned_name,
        "organization_locations": country,
        "person_titles": ROLE_KEYWORDS,
        "page": 1,
        "per_page": 10
    }

    if valid_website:
        domain = valid_website.replace("https://", "").replace("http://", "").split("/")[0]
        body["organization_domains"] = domain

    try:
        resp = requests.post("https://api.apollo.io/api/v1/mixed_people/search", headers=headers, json=body, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        people = data.get("people", [])
        filtered = filter_people_by_role(people)

        if not filtered and not valid_website:
            # Fallback: try to get domain from /mixed_companies/search
            company_body = {
                "q_organization_name": cleaned_name,
                "organization_locations": country,
                "page": 1,
                "per_page": 1
            }
            c_resp = requests.post("https://api.apollo.io/api/v1/mixed_companies/search", headers=headers, json=company_body, timeout=20)
            c_resp.raise_for_status()
            c_data = c_resp.json()
            companies = c_data.get("organizations", [])
            if companies and companies[0].get("website_url"):
                domain = companies[0]["website_url"].replace("https://", "").replace("http://", "").split("/")[0]
                if is_valid_domain(domain):
                    body["organization_domains"] = domain
                    resp2 = requests.post("https://api.apollo.io/api/v1/mixed_people/search", headers=headers, json=body, timeout=20)
                    resp2.raise_for_status()
                    data2 = resp2.json()
                    people = data2.get("people", [])
                    filtered = filter_people_by_role(people)

        # Format results
        results = []
        for person in filtered:
            email = person.get("email", "")
            # Try to reveal email if not unlocked and id is present
            if email == "email_not_unlocked@domain.com" and person.get("id"):
                revealed_email = reveal_email_apollo(person["id"])
                if revealed_email:
                    email = revealed_email
            results.append({
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}",
                "title": person.get("title", ""),
                "email": email,
                "linkedin": get_linkedin_url(person)
            })
        return results

    except Exception as e:
        print(f"[red]Error contacting Apollo.io: {e}[/red]")
        return []
