import typer
from rich.console import Console
import sys
import os
import requests
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import sqlite3
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.append("..")
from db_apollo import init_apollo_db, insert_company
from db_apollo import count_companies
from apollo import APOLLO_API_KEY

app = typer.Typer()
console = Console()

# Fun icons (reduced)
ICON_COMPANY = "🏢"
ICON_BUYER = "🧑‍💼"
ICON_EXPORT = "📤"
ICON_WARN = "⚠️"
ICON_DONE = "✅"
ICON_LOADING = "⏳"

def apollo_company_extraction():
    """Standalone Apollo company extraction function with fun UI (reduced icons)."""
    init_apollo_db()  # Ensure Apollo.db is initialized
    console.rule(f"[bold blue]{ICON_COMPANY} Company Extraction: Glove-related companies via Apollo API")
    # Step 1: Country selection
    console.print(f"[bold]Select country search mode:[/bold]")
    console.print(f"[cyan]1.[/cyan] Choose from global country list")
    console.print(f"[cyan]2.[/cyan] Choose from Asia country list")
    console.print(f"[cyan]3.[/cyan] Enter custom country")
    console.print(f"[cyan]4.[/cyan] Back")
    country_mode = typer.prompt("Select option", type=int)
    country = None
    if country_mode == 1:
        country_list_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'global_countries.txt')
        with open(country_list_path, 'r', encoding='utf-8') as f:
            countries = [line.strip() for line in f if line.strip()]
        country_options = {str(idx+1): country for idx, country in enumerate([
            'United States', 'Germany', 'United Kingdom', 'France', 'Italy', 'Spain', 'Canada', 'Australia', 'Brazil', 'Mexico',
            'Russia', 'Turkey', 'Netherlands', 'Switzerland', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Poland', 'Austria',
            'Belgium', 'South Africa', 'Egypt', 'Saudi Arabia', 'United Arab Emirates', 'Argentina', 'Chile', 'New Zealand',
            'Ireland', 'Portugal', 'Greece', 'Czech Republic', 'Hungary', 'Romania', 'Israel', 'Ukraine'
        ])}
        for key, country_name in country_options.items():
            console.print(f"[cyan]{key}.[/cyan] {country_name}")
        choice = typer.prompt("Enter a number", type=str)
        selected_country = country_options.get(choice)
        if not selected_country:
            console.print("[yellow]Invalid choice. Defaulting to global search.[/yellow]")
            country = None
        else:
            country = selected_country
    elif country_mode == 2:
        country_list_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'asia_countries.txt')
        with open(country_list_path, 'r', encoding='utf-8') as f:
            countries = [line.strip() for line in f if line.strip()]
        asia_country_options = {
            "1": "Malaysia",
            "2": "Indonesia",
            "3": "Thailand",
            "4": "Vietnam",
            "5": "Singapore",
            "6": "Philippines",
            "7": "China",
            "8": "India",
            "9": "Japan",
            "10": "South Korea",
            "11": "Hong Kong",
            "12": "Taiwan",
            "13": "Bangladesh",
            "14": "Pakistan",
            "15": "Sri Lanka",
            "16": "Myanmar",
            "17": "Cambodia",
            "18": "Laos",
            "19": "Nepal",
            "20": "Mongolia",
            "21": "Brunei",
            "22": "Timor-Leste",
            "23": "Maldives",
            "24": "Bhutan"
        }
        for key, country_name in asia_country_options.items():
            console.print(f"[cyan]{key}.[/cyan] {country_name}")
        choice = typer.prompt("Enter a number", type=str)
        selected_country = asia_country_options.get(choice)
        if not selected_country:
            console.print("[yellow]Invalid choice. Defaulting to global search.[/yellow]")
            country = None
        else:
            country = selected_country
    elif country_mode == 3:
        country = Prompt.ask("Enter a country name (leave blank for global)", default="").strip()
        if not country:
            country = None
    elif country_mode == 4:
        return
    else:
        console.print("[red]Invalid option. Returning to menu.[/red]")
        return
    
    # Use Apollo's precise tag-based filtering for glove companies
    max_pages = typer.prompt("How many pages to fetch from Apollo? (up to 100 per page, 500 pages max)", type=int, default=500)
    api_key = APOLLO_API_KEY
    if not api_key:
        console.print("[red]APOLLO_API_KEY environment variable not set![/red]")
        return
    headers = {"Cache-Control": "no-cache", "Content-Type": "application/json", "x-api-key": api_key}
    initial_count = count_companies()
    console.print(f"[yellow]Initial companies in database: {initial_count}[/yellow]")
    total_saved = 0
    for page in range(1, max_pages + 1):
        body = {
            "page": page,
            "per_page": 100,
            "industry_tags": [
                "Pharmaceuticals",
                "Medical Devices",
                "Healthcare",
                "Manufacturing",
                "Medical Supplies"
            ],
            "q_organization_keyword_tags": [
                "latex gloves",
                "nitrile gloves",
                "medical gloves",
                "surgical gloves",
                "exam gloves",
                "biohazard protection"
            ]
        }
        if country:
            body["organization_locations"] = [country]
        try:
            with Progress(SpinnerColumn(), TextColumn(f"[progress.description]{ICON_LOADING} Fetching companies from Apollo (page {page})..."), transient=True) as progress:
                task = progress.add_task(f"[yellow]{ICON_LOADING} Fetching companies from Apollo (page {page})...", start=False)
                progress.start_task(task)
                resp = requests.post(
                    "https://api.apollo.io/v1/mixed_companies/search",
                    headers=headers,
                    json=body
                )
            if resp.status_code != 200:
                console.print(f"[red]Apollo API error (status {resp.status_code}): {resp.text}[/red]")
                break
            data = resp.json()
            companies = data.get("organizations", [])
            if not companies:
                console.print(f"[yellow]No companies found on page {page}.")
                break
            for comp in companies:
                company_name = comp.get("name", "")
                country_val = comp.get("location_country") or comp.get("country") or country
                domain = comp.get("primary_domain")
                industry = comp.get("industry", "")
                employee_count = comp.get("estimated_num_employees")
                # Optionally store Apollo's keyword tags
                keyword_tags = comp.get("keyword_tags", [])
                if not company_name or not domain:
                    continue  # skip incomplete
                # Optionally, you can extend insert_company to store keyword_tags if desired
                cid, is_new = insert_company(company_name, country_val, domain, industry, employee_count)
                if is_new:
                    total_saved += 1
                else:
                    pass # Company already exists, skipping count
            console.print(f"[green]{ICON_DONE} Page {page}: Processed {len(companies)} companies, saved {total_saved} new glove companies for {country or 'Global'}.")
        except Exception as e:
            console.print(f"[red]Error on page {page}: {e}[/red]")
            break
    final_count = count_companies()
    console.print(f"[bold green]{ICON_DONE} Extraction complete. New companies added: {total_saved} for {country or 'Global'}[/bold green]")
    console.print(f"[bold green]{ICON_DONE} Total companies in database: {final_count} (was {initial_count})[/bold green]")

def buyer_extraction():
    """Interactive buyer extraction: select scope, country, company, then fetch/export contacts. Now with 'Back' options at each step and reduced icons."""
    from db_apollo import insert_contact, get_contacts_by_company, get_available_countries_asia, get_available_countries_global, get_all_companies
    from apollo import find_decision_makers_apollo
    import csv
    init_apollo_db()
    while True:
        console.rule(f"[bold blue]{ICON_BUYER} Buyer Extraction: Decision makers for glove companies via Apollo API")
        # Step 1: Scope selection
        console.print(f"[bold]Select search scope:[/bold]")
        console.print(f"[cyan]1.[/cyan] Asia")
        console.print(f"[cyan]2.[/cyan] Global")
        console.print(f"[cyan]3.[/cyan] Back")
        scope_choice = typer.prompt("Select option", type=int)
        if scope_choice == 3:
            return
        if scope_choice == 1:
            available_countries = get_available_countries_asia()
            scope_name = "Asia"
        elif scope_choice == 2:
            available_countries = get_available_countries_global()
            scope_name = "Global"
        else:
            console.print(f"[red]{ICON_WARN} Invalid scope selection.[/red]")
            continue
        if not available_countries:
            console.print(f"[yellow]{ICON_WARN} No countries with companies found for {scope_name} scope.[/yellow]")
            continue
        # Step 2: Country selection
        while True:
            console.print(f"[bold]Select a country from {scope_name} (only those with companies):[/bold]")
            for idx, country in enumerate(available_countries, 1):
                console.print(f"[cyan]{idx}.[/cyan] {country}")
            console.print(f"[cyan]{len(available_countries)+1}.[/cyan] Back")
            country_idx = typer.prompt("Enter number to select country", type=int)
            if country_idx == len(available_countries)+1:
                break  # Go back to scope selection
            if 1 <= country_idx <= len(available_countries):
                selected_country = available_countries[country_idx-1]
            else:
                console.print(f"[red]{ICON_WARN} Invalid country selection.[/red]")
                continue
            # Step 3: Show companies in this country
            all_companies = get_all_companies()
            companies = [c for c in all_companies if (c.get('country') or '').strip() == (selected_country if selected_country != 'USA' else 'United States')]
            if not companies:
                console.print(f"[yellow]{ICON_WARN} No companies found for {selected_country} in the database.[/yellow]")
                continue
            # Display table
            table = Table(title=f"Companies in {selected_country}", show_lines=True, title_style="bold magenta")
            table.add_column("Index", style="cyan", justify="right")
            table.add_column("Name", style="bold")
            table.add_column("Domain", style="green")
            table.add_column("Industry", style="yellow")
            table.add_column("Employees", style="magenta")
            table.add_column("Source", style="blue")
            for idx, comp in enumerate(companies, 1):
                table.add_row(str(idx), comp['company_name'], comp.get('domain',''), comp.get('industry',''), str(comp.get('employee_count','')), comp.get('source',''))
            console.print(table)
            # Step 4: Company selection (one or more)
            while True:
                console.print(f"[bold]Select companies to extract contacts for (comma-separated indices, e.g. 1,3,5):[/bold]")
                console.print(f"[cyan]0.[/cyan] Back")
                selection = typer.prompt("Enter indices or 0 to go back")
                if selection.strip() == '0':
                    break  # Go back to country selection
                try:
                    selected_indices = [int(x.strip())-1 for x in selection.split(',') if x.strip().isdigit()]
                except Exception:
                    console.print(f"[red]{ICON_WARN} Invalid input: please enter number(s) separated by commas (e.g. 1,2,3).[/red]")
                    continue
                selected_companies = [companies[i] for i in selected_indices if 0 <= i < len(companies)]
                if not selected_companies:
                    console.print(f"[red]{ICON_WARN} No valid companies selected.[/red]")
                    continue
                # Step 5: For each, fetch contacts, save, export
                for comp in selected_companies:
                    company_id = comp['id']
                    company_name = comp['company_name']
                    company_country = comp.get('country') or ''
                    company_domain = comp.get('domain')
                    console.print(f"[bold]Extracting contacts for: {company_name} ({company_country})")
                    try:
                        from rich.progress import Progress, SpinnerColumn, TextColumn
                        with Progress(SpinnerColumn(), TextColumn(f"[progress.description]{ICON_LOADING} Fetching contacts from Apollo..."), transient=True) as progress:
                            task = progress.add_task(f"[yellow]{ICON_LOADING} Fetching contacts from Apollo...", start=False)
                            progress.start_task(task)
                            contacts = find_decision_makers_apollo(company_name, company_country, company_domain)
                    except Exception as e:
                        console.print(f"[red]{ICON_WARN} Error querying Apollo for {company_name}: {e}[/red]")
                        continue
                    if not contacts:
                        console.print(f"[yellow]{ICON_WARN} No buyers/decision makers found for {company_name}.[/yellow]")
                        continue
                    for contact in contacts:
                        name = contact.get('name')
                        title = contact.get('title')
                        email = contact.get('email')
                        linkedin = contact.get('linkedin')
                        insert_contact(company_id, company_name, name, title, email, linkedin)
                    # Display contacts in a table
                    contact_table = Table(title=f"Contacts for {company_name}", show_lines=True, title_style="bold green")
                    contact_table.add_column("Name", style="bold")
                    contact_table.add_column("Title", style="green")
                    contact_table.add_column("Email", style="yellow")
                    contact_table.add_column("LinkedIn", style="blue")
                    for row in contacts:
                        contact_table.add_row(row.get('name',''), row.get('title',''), row.get('email',''), row.get('linkedin',''))
                    console.print(contact_table)
                    # Ask user if they want to export
                    export_choice = typer.confirm(f"Do you want to export these contacts for {company_name} to CSV?", default=True)
                    if export_choice:
                        export_dir = os.path.join(os.path.dirname(__file__), '..', 'EXPORT')
                        os.makedirs(export_dir, exist_ok=True)
                        safe_name = company_name.replace(' ', '_').replace('/', '_')
                        default_filename = f"apollo_{safe_name}_contacts.csv"
                        filename = typer.prompt(f"Enter filename for export", default=default_filename)
                        filepath = os.path.join(export_dir, filename)
                        with open(filepath, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=["name", "title", "email", "linkedin"])
                            writer.writeheader()
                            for row in contacts:
                                writer.writerow(row)
                        console.print(f"[green]{ICON_DONE} Exported contacts for {company_name} to {filepath}")
                    else:
                        console.print(f"[yellow]{ICON_WARN} Skipped export for {company_name}.[/yellow]")
                console.print(f"[bold green]{ICON_DONE} Extraction and export complete for {len(selected_companies)} companies.[/bold green]")
                break  # After extraction, go back to company selection

@app.command()
def run():
    """Main entry point for Apollo extraction"""
    while True:
        console.rule(f"[bold blue]{ICON_COMPANY} Apollo Company Extraction Tool {ICON_COMPANY}")
        console.print(f"[bold]Select option:[/bold]")
        console.print(f"[cyan]1.[/cyan] Company Extraction")
        console.print(f"[cyan]2.[/cyan] Buyer Extraction")
        console.print(f"[cyan]3.[/cyan] Remove Duplicate Companies {ICON_WARN}")
        console.print(f"[cyan]4.[/cyan] Exit")
        choice = typer.prompt("Select an option", type=int)
        if choice == 1:
            apollo_company_extraction()
        elif choice == 2:
            buyer_extraction()
        elif choice == 3:
            remove_duplicate_companies()
        elif choice == 4:
            console.print(f"[green]{ICON_DONE} Goodbye!")
            break
        else:
            console.print(f"[red]{ICON_WARN} Invalid option. Please try again.[/red]")

# --- Duplicate removal logic ---
def remove_duplicate_companies():
    """Scan for duplicate companies and remove them, keeping the oldest."""
    from db_apollo import get_all_companies
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), '..', 'Apollo.db')
    companies = get_all_companies()
    # Find duplicates by (domain) or (company_name+country)
    seen_domains = {}
    seen_name_country = {}
    duplicates = []
    for comp in companies:
        key_domain = comp['domain'].lower().strip() if comp['domain'] else None
        key_name_country = (comp['company_name'].lower().strip(), (comp['country'] or '').lower().strip())
        if key_domain and key_domain in seen_domains:
            duplicates.append(comp['id'])
        elif key_domain:
            seen_domains[key_domain] = comp['id']
        elif key_name_country in seen_name_country:
            duplicates.append(comp['id'])
        else:
            seen_name_country[key_name_country] = comp['id']
    if not duplicates:
        console.print(f"[green]{ICON_DONE} No duplicate companies found in the database![/green]")
        return
    # Remove duplicates
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executemany('DELETE FROM companies WHERE id = ?', [(dup_id,) for dup_id in duplicates])
    conn.commit()
    conn.close()
    console.print(f"[yellow]{ICON_WARN} Removed {len(duplicates)} duplicate companies from the database.[/yellow]")

if __name__ == "__main__":
    app() 