import typer
from rich.console import Console
import sys
import os
sys.path.append("..")  # Ensure parent dir is in path for imports
from hs_code_manager import load_hs_codes_xlsx, select_hs_code, add_hs_code, edit_hs_code, delete_hs_code
from rich.table import Table
from deepseek_agent import query_deepseek, query_deepseek_for_hs_codes, query_deepseek_for_global_hs_codes, parse_hs_codes_from_deepseek
from db import init_db, insert_results, parse_deepseek_output, fetch_all_results, update_result, delete_result, get_all_global_hs_codes, save_global_hs_code, update_global_hs_code, delete_global_hs_code, get_all_asia_hs_codes, save_asia_hs_code, update_asia_hs_code, delete_asia_hs_code, check_existing_buyer_results, find_and_remove_duplicates, get_duplicate_summary, init_international_hs_codes, get_all_international_hs_codes, check_existing_buyer_leads, insert_buyer_leads
import pandas as pd
import datetime
import csv
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer()
console = Console()

MENU_OPTIONS = [
    "Search Buyers with DeepSeek (Asia/Global/International)",
    "Manage HS Codes (CRUD)",
    "Manage Potential Buyer List",
    "Export Results (CSV)",
    "Exit"
]

def hs_code_crud_menu():
    crud_options = [
        "Add New HS Code",
        "Edit Existing HS Code",
        "Delete HS Code",
        "View All HS Codes",
        "Back to Main Menu"
    ]
    console.rule("[bold magenta]HS Code Management[/bold magenta]")
    for idx, option in enumerate(crud_options, 1):
        console.print(f"[cyan]{idx}.[/cyan] {option}")
    choice = typer.prompt("\nSelect an option", type=int)
    return choice

def country_hs_code_crud_menu():
    crud_options = [
        "View All Country-Specific HS Codes",
        "View HS Codes for Specific Country",
        "Add Country-Specific HS Code",
        "Edit Country-Specific HS Code",
        "Delete Country-Specific HS Code",
        "Query DeepSeek for Country-Specific HS Codes",
        "Back to Main Menu"
    ]
    console.rule("[bold magenta]Country-Specific HS Code Management[/bold magenta]")
    for idx, option in enumerate(crud_options, 1):
        console.print(f"[cyan]{idx}.[/cyan] {option}")
    choice = typer.prompt("\nSelect an option", type=int)
    return choice

def buyer_history_crud_menu():
    crud_options = [
        "View All Potential Buyers",
        "Edit Buyer Record",
        "Delete Buyer Record",
        "Check for Duplicates",
        "Back to Main Menu"
    ]
    console.rule("[bold magenta]Potential Buyer List Management[/bold magenta]")
    for idx, option in enumerate(crud_options, 1):
        console.print(f"[cyan]{idx}.[/cyan] {option}")
    choice = typer.prompt("\nSelect an option", type=int)
    return choice

def main_menu():
    console.rule("[bold blue]🧠 Glove Buyer Intel CLI 🧠")
    for idx, option in enumerate(MENU_OPTIONS, 1):
        console.print(f"[cyan]{idx}.[/cyan] {option}")
    choice = typer.prompt("\nSelect an option", type=int)
    return choice

def load_country_list(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def perform_buyer_search(scope, country, selected_code, selected_desc):
    """Helper function to perform the actual buyer search process (with country and scope)"""
    # Step 1: Keyword selection
    keyword_file = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'keyword_options.txt')
    with open(keyword_file, 'r', encoding='utf-8') as f:
        keyword_options = [line.strip() for line in f if line.strip()]
    console.print("[bold]Select product keyword:[/bold]")
    for kidx, keyword_option in enumerate(keyword_options, 1):
        console.print(f"[cyan]{kidx}.[/cyan] {keyword_option.title()}")
    console.print(f"[cyan]{len(keyword_options)+1}.[/cyan] [italic]Custom Keyword[/italic]")
    console.print(f"[cyan]{len(keyword_options)+2}.[/cyan] Back to HS Code Selection")
    keyword_choice = typer.prompt("Enter number to select keyword or custom", type=int)
    if keyword_choice == len(keyword_options)+2:
        return False  # Back to HS Code Selection
    if 1 <= keyword_choice <= len(keyword_options):
        keyword = keyword_options[keyword_choice-1]
    elif keyword_choice == len(keyword_options)+1:
        keyword = typer.prompt("Enter custom product keyword")
    else:
        console.print("[red]Invalid keyword selection.[/red]")
        return False
    # Step 2: Check for existing buyer leads first
    existing_buyers = check_existing_buyer_leads(scope, selected_code, keyword)
    if existing_buyers:
        console.print(f"[green]Found {len(existing_buyers)} existing buyer leads for HS Code {selected_code} ({selected_desc}) in {country} with keyword '{keyword}':[/green]")
        for idx, buyer in enumerate(existing_buyers, 1):
            console.print(f"[cyan]{idx}.[/cyan] {buyer['company_name']} - {buyer['company_country']}")
        console.print("\n[bold]Options:[/bold]")
        console.print("[cyan]1.[/cyan] Use existing results")
        console.print("[cyan]2.[/cyan] Query DeepSeek for new results")
        console.print("[cyan]3.[/cyan] Back to keyword selection")
        buyer_option = typer.prompt("Select option", type=int)
        if buyer_option == 1:
            console.print("[green]Using existing buyer leads.[/green]")
            return True  # Search completed successfully
        elif buyer_option == 2:
            existing_company_names = [buyer['company_name'] for buyer in existing_buyers]
            console.print(f"[yellow]Searching for NEW buyers (excluding {len(existing_company_names)} existing companies) for HS Code {selected_code} ({selected_desc}) in {country} with keyword '{keyword}'...[/yellow]")
            try:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                    task = progress.add_task("[yellow]Contacting DeepSeek...", start=False)
                    progress.start_task(task)
                    result = query_deepseek(selected_code, keyword, country, existing_company_names)
                console.print("[bold green]DeepSeek Results:[/bold green]")
                console.print(result)
                companies = parse_deepseek_output(result)
                console.print(f"[yellow]DEBUG: Parsed companies: {companies}[/yellow]")
                # Save to both old results table and new scope-specific table
                insert_results(selected_code, keyword, country, companies)
                insert_buyer_leads(scope, selected_code, keyword, companies)
                console.print(f"[green]{len(companies)} companies saved to both results and {scope} buyer leads (duplicates skipped).[/green]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        elif buyer_option == 3:
            return False  # Back to keyword selection
        else:
            console.print("[red]Invalid option.[/red]")
            return False
    else:
        # No existing results, query DeepSeek
        console.print(f"[yellow]Searching buyers for HS Code {selected_code} ({selected_desc}) in {country} with keyword '{keyword}'...[/yellow]")
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                task = progress.add_task("[yellow]Contacting DeepSeek...", start=False)
                progress.start_task(task)
                result = query_deepseek(selected_code, keyword, country, [])
            console.print("[bold green]DeepSeek Results:[/bold green]")
            console.print(result)
            companies = parse_deepseek_output(result)
            console.print(f"[yellow]DEBUG: Parsed companies: {companies}[/yellow]")
            # Save to both old results table and new scope-specific table
            insert_results(selected_code, keyword, country, companies)
            insert_buyer_leads(scope, selected_code, keyword, companies)
            console.print(f"[green]{len(companies)} companies saved to both results and {scope} buyer leads (duplicates skipped).[/green]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return False
    return True  # Search completed successfully

def select_country_and_scope():
    """Helper function to select country and scope"""
    # Step 1: Select scope (Asia/Global)
    console.print("[bold]Choose search scope:[/bold]")
    console.print("[cyan]1.[/cyan] Asia")
    console.print("[cyan]2.[/cyan] Global")
    console.print("[cyan]3.[/cyan] Back to Main Menu")
    scope = typer.prompt("Enter number for scope", type=int)
    
    if scope == 3:
        return None, None
    
    if scope == 1:
        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'asia_countries.txt'))
        scope_name = "Asia"
    elif scope == 2:
        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'global_countries.txt'))
        scope_name = "Global"
    else:
        console.print("[red]Invalid scope selection.[/red]")
        return None, None
    
    # Step 2: Country selection
    console.print(f"[bold]Select a country from {scope_name} or enter a custom country:[/bold]")
    for idx, country in enumerate(country_list, 1):
        console.print(f"[cyan]{idx}.[/cyan] {country}")
    console.print(f"[cyan]{len(country_list)+1}.[/cyan] [italic]Enter a custom country[/italic]")
    console.print(f"[cyan]{len(country_list)+2}.[/cyan] Back to Scope Selection")
    country_idx = typer.prompt("Enter number to select country or custom", type=int)
    
    if country_idx == len(country_list)+2:
        return None, None
    
    if 1 <= country_idx <= len(country_list):
        country = country_list[country_idx-1]
    elif country_idx == len(country_list)+1:
        country = typer.prompt("Enter custom country name")
    else:
        console.print("[red]Invalid country selection.[/red]")
        return None, None
    
    return country, scope_name

@app.command()
def run():
    init_db()
    init_international_hs_codes()
    while True:
        choice = main_menu()
        if choice == 1:
            # Buyer search state machine
            while True:
                # 1. Scope selection
                scope, scope_name = None, None
                while scope_name is None:
                    console.print("[bold]Choose search scope:[/bold]")
                    console.print("[cyan]1.[/cyan] Asia")
                    console.print("[cyan]2.[/cyan] Global")
                    console.print("[cyan]3.[/cyan] Back to Main Menu")
                    scope = typer.prompt("Enter number for scope", type=int)
                    if scope == 3:
                        break
                    if scope == 1:
                        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'asia_countries.txt'))
                        scope_name = "Asia"
                    elif scope == 2:
                        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'global_countries.txt'))
                        scope_name = "Global"
                    else:
                        console.print("[red]Invalid scope selection.[/red]")
                        continue
                if scope == 3:
                    break
                # 2. Country selection
                while True:
                    console.print(f"[bold]Select a country from {scope_name} or enter a custom country:[/bold]")
                    for idx, ctry in enumerate(country_list, 1):
                        console.print(f"[cyan]{idx}.[/cyan] {ctry}")
                    console.print(f"[cyan]{len(country_list)+1}.[/cyan] [italic]Enter a custom country[/italic]")
                    console.print(f"[cyan]{len(country_list)+2}.[/cyan] Back to Scope Selection")
                    country_idx = typer.prompt("Enter number to select country or custom", type=int)
                    if country_idx == len(country_list)+2:
                        break
                    if 1 <= country_idx <= len(country_list):
                        country = country_list[country_idx-1]
                    elif country_idx == len(country_list)+1:
                        country = typer.prompt("Enter custom country name")
                    else:
                        console.print("[red]Invalid country selection.[/red]")
                        continue
                    # Check for existing HS codes for the selected country
                    if scope_name == "Asia":
                        existing_codes = [c for c in get_all_asia_hs_codes() if c['country'].lower() == country.lower()]
                    else:
                        existing_codes = [c for c in get_all_global_hs_codes() if c['country'].lower() == country.lower()]
                    if existing_codes:
                        console.print(f"[green]Existing HS codes for {country}:[/green]")
                        for idx, code_info in enumerate(existing_codes, 1):
                            console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                    else:
                        console.print(f"[yellow]No HS codes found for {country}.[/yellow]")
                    # 3. HS code and buyer search loop for this country
                    while True:
                        if scope_name == "Asia":
                            codes = [c for c in get_all_asia_hs_codes() if c['country'].lower() == country.lower()]
                        else:
                            codes = [c for c in get_all_global_hs_codes() if c['country'].lower() == country.lower()]
                        if not codes:
                            console.print(f"[red]No {scope_name} HS codes available for {country}.")
                            console.print("[bold]Options:[/bold]")
                            console.print("[cyan]1.[/cyan] Query DeepSeek for new HS codes")
                            console.print("[cyan]2.[/cyan] Use international HS codes")
                            console.print("[cyan]3.[/cyan] Back to Country Selection")
                            fallback_choice = typer.prompt("Select option", type=int)
                            if fallback_choice == 3:
                                break
                            if fallback_choice == 1:
                                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                                    task = progress.add_task("[yellow]Contacting DeepSeek...", start=False)
                                    progress.start_task(task)
                                    if scope_name == "Asia":
                                        deepseek_response = query_deepseek_for_hs_codes(country)
                                    else:
                                        deepseek_response = query_deepseek_for_global_hs_codes()
                                new_codes = parse_hs_codes_from_deepseek(deepseek_response)
                                if new_codes:
                                    console.print(f"[green]Found {len(new_codes)} new HS codes:")
                                    for idx, code_info in enumerate(new_codes, 1):
                                        console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                                    console.print("[bold]What would you like to do with these codes?[/bold]")
                                    console.print("[cyan]1.[/cyan] Add all new codes")
                                    console.print("[cyan]2.[/cyan] Select specific codes to add")
                                    console.print("[cyan]3.[/cyan] Skip saving")
                                    save_option = typer.prompt("Select option", type=int)
                                    if save_option == 1:
                                        added_count = 0
                                        for code_info in new_codes:
                                            if scope_name == "Asia":
                                                if save_asia_hs_code(code_info['hs_code'], code_info['description'], country, source="DeepSeek"):
                                                    added_count += 1
                                            else:
                                                if save_global_hs_code(code_info['hs_code'], code_info['description'], country, source="DeepSeek"):
                                                    added_count += 1
                                        console.print(f"[green]{added_count} HS codes have been saved to the database.[/green]")
                                        codes = [c for c in get_all_asia_hs_codes() if c['country'].lower() == country.lower()] if scope_name == "Asia" else [c for c in get_all_global_hs_codes() if c['country'].lower() == country.lower()]
                                    elif save_option == 2:
                                        console.print("[bold]Select codes to add (comma-separated numbers):[/bold]")
                                        for idx, code_info in enumerate(new_codes, 1):
                                            console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                                        selection = typer.prompt("Enter numbers (e.g., 1,3,5)")
                                        try:
                                            selected_indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip().isdigit()]
                                            added_count = 0
                                            for idx in selected_indices:
                                                if 0 <= idx < len(new_codes):
                                                    code_info = new_codes[idx]
                                                    if scope_name == "Asia":
                                                        if save_asia_hs_code(code_info['hs_code'], code_info['description'], country, source="DeepSeek"):
                                                            added_count += 1
                                                    else:
                                                        if save_global_hs_code(code_info['hs_code'], code_info['description'], country, source="DeepSeek"):
                                                            added_count += 1
                                            console.print(f"[green]{added_count} HS codes have been saved to the database.[/green]")
                                            codes = [c for c in get_all_asia_hs_codes() if c['country'].lower() == country.lower()] if scope_name == "Asia" else [c for c in get_all_global_hs_codes() if c['country'].lower() == country.lower()]
                                        except Exception:
                                            console.print("[red]Invalid selection format.[/red]")
                                            continue
                                    elif save_option == 3:
                                        console.print("[yellow]Skipped saving new codes.[/yellow]")
                                        continue
                                    else:
                                        console.print("[red]Invalid option.[/red]")
                                        continue
                                else:
                                    console.print("[red]No HS codes found in DeepSeek response.[/red]")
                                    continue
                            elif fallback_choice == 2:
                                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                                    task = progress.add_task("[yellow]Loading international HS codes...", start=False)
                                    progress.start_task(task)
                                    codes = get_all_international_hs_codes()
                                if not codes:
                                    console.print("[red]No international HS codes available.[/red]")
                                    continue
                                scope_name = "International"
                            else:
                                console.print("[red]Invalid option.[/red]")
                                continue
                        # Step 3: HS code selection
                        if codes:
                            console.print(f"[bold]Select HS code to use for {country}:[/bold]")
                            for idx, code_info in enumerate(codes, 1):
                                console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                            console.print(f"[cyan]{len(codes)+1}.[/cyan] Back to Country Selection")
                            idx = typer.prompt("Enter number to select", type=int)
                            if idx == len(codes)+1:
                                break
                            if 1 <= idx <= len(codes):
                                selected_code = codes[idx-1]['hs_code']
                                selected_desc = codes[idx-1]['description']
                                console.print(f"[green]Selected HS Code:[/green] [bold]{selected_code}[/bold] - {selected_desc}")
                                # Step 4: Keyword selection and search
                                perform_buyer_search(scope_name, country, selected_code, selected_desc)
                                # Step 5: After search, ask what to do next
                                console.print("[bold]What would you like to do next?[/bold]")
                                console.print("[cyan]1.[/cyan] Search again with the same country")
                                console.print("[cyan]2.[/cyan] Search in a different country")
                                console.print("[cyan]3.[/cyan] Change scope")
                                console.print("[cyan]4.[/cyan] Back to main menu")
                                next_action = typer.prompt("Select option", type=int)
                                if next_action == 1:
                                    continue  # Go back to HS code selection for same country
                                elif next_action == 2:
                                    break    # Go back to country selection
                                elif next_action == 3:
                                    break    # Go back to scope selection (outer loop)
                                elif next_action == 4:
                                    return   # Exit to main menu
                                else:
                                    console.print("[red]Invalid option.[/red]")
                                    break
                            else:
                                console.print("[red]Invalid selection.[/red]")
                                continue
                        else:
                            break
                    # End of HS code and buyer search loop for this country
                # End of country selection loop
        elif choice == 2:
            while True:
                crud_choice = hs_code_crud_menu()
                if crud_choice == 1:
                    # Add New HS Code - Scope/Country flow
                    console.print("[bold]Select scope for HS code:[/bold]")
                    console.print("[cyan]1.[/cyan] Asia")
                    console.print("[cyan]2.[/cyan] Global")
                    console.print("[cyan]3.[/cyan] Back to HS Code Management")
                    scope_choice = typer.prompt("Select scope", type=int)
                    if scope_choice == 3:
                        continue
                    if scope_choice == 1:
                        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'asia_countries.txt'))
                        current_scope = "Asia"
                    elif scope_choice == 2:
                        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'global_countries.txt'))
                        current_scope = "Global"
                    else:
                        console.print("[red]Invalid scope selection.[/red]")
                        continue
                    # Country selection
                    console.print(f"[bold]Select a country from {current_scope} or choose Global:[/bold]")
                    for idx, country in enumerate(country_list, 1):
                        console.print(f"[cyan]{idx}.[/cyan] {country}")
                    console.print(f"[cyan]{len(country_list)+1}.[/cyan] [italic]Global (for global HS codes)[/italic]")
                    console.print(f"[cyan]{len(country_list)+2}.[/cyan] Back to Scope Selection")
                    country_idx = typer.prompt("Enter number to select country or global", type=int)
                    if country_idx == len(country_list)+2:
                        continue
                    if 1 <= country_idx <= len(country_list):
                        country = country_list[country_idx-1]
                    elif country_idx == len(country_list)+1:
                        country = "Global"
                    else:
                        console.print("[red]Invalid country selection.[/red]")
                        continue
                    # Check for existing HS codes for the selected country
                    if scope_choice == 1:
                        existing_codes = [c for c in get_all_asia_hs_codes() if c['country'].lower() == country.lower()]
                    elif scope_choice == 2:
                        existing_codes = [c for c in get_all_global_hs_codes() if c['country'].lower() == country.lower()]
                    else:
                        existing_codes = []
                    if existing_codes:
                        console.print(f"[green]Existing HS codes for {country}:[/green]")
                        for idx, code_info in enumerate(existing_codes, 1):
                            console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                        console.print(f"\n[bold yellow]HS codes already exist for {country}. What would you like to do?[/bold yellow]")
                        console.print("[cyan]1.[/cyan] Add another HS code")
                        console.print("[cyan]2.[/cyan] Return to HS Code Management menu")
                        reuse_choice = typer.prompt("Select option", type=int)
                        if reuse_choice == 2:
                            continue
                        elif reuse_choice != 1:
                            console.print("[red]Invalid option. Returning to menu.[/red]")
                            continue
                    else:
                        console.print(f"[yellow]No HS codes found for {country}.[/yellow]")
                    # Ask for DeepSeek or manual
                    console.print("[bold]How would you like to add HS codes for this selection?[/bold]")
                    console.print("[cyan]1.[/cyan] Query DeepSeek for HS codes")
                    console.print("[cyan]2.[/cyan] Manually add HS code")
                    console.print("[cyan]3.[/cyan] Back to previous menu")
                    add_method = typer.prompt("Select method", type=int)
                    if add_method == 3:
                        continue
                    if add_method == 1:
                        # Query DeepSeek for HS codes
                        if country == "Global":
                            console.print("[yellow]Querying DeepSeek for global HS codes...[/yellow]")
                            try:
                                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                                    task = progress.add_task("[yellow]Contacting DeepSeek...", start=False)
                                    progress.start_task(task)
                                    deepseek_response = query_deepseek_for_global_hs_codes()
                                console.print("[bold green]DeepSeek Results:[/bold green]")
                                console.print(deepseek_response)
                                new_codes = parse_hs_codes_from_deepseek(deepseek_response)
                                if new_codes:
                                    console.print(f"\n[green]Found {len(new_codes)} new HS codes:[/green]")
                                    for idx, code_info in enumerate(new_codes, 1):
                                        console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                                    console.print("\n[bold]What would you like to do with these codes?[/bold]")
                                    console.print("[cyan]1.[/cyan] Add all new codes")
                                    console.print("[cyan]2.[/cyan] Select specific codes to add")
                                    console.print("[cyan]3.[/cyan] Skip saving")
                                    save_option = typer.prompt("Select option", type=int)
                                    if save_option == 1:
                                        added_count = 0
                                        for code_info in new_codes:
                                            if save_global_hs_code(code_info['hs_code'], code_info['description'], country, source="DeepSeek"):
                                                added_count += 1
                                        console.print(f"[green]Added {added_count} new HS codes to database.[/green]")
                                    elif save_option == 2:
                                        console.print("[bold]Select codes to add (comma-separated numbers):[/bold]")
                                        for idx, code_info in enumerate(new_codes, 1):
                                            console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                                        selection = typer.prompt("Enter numbers (e.g., 1,3,5)")
                                        try:
                                            selected_indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip().isdigit()]
                                            added_count = 0
                                            for idx in selected_indices:
                                                if 0 <= idx < len(new_codes):
                                                    code_info = new_codes[idx]
                                                    if save_global_hs_code(code_info['hs_code'], code_info['description'], country, source="DeepSeek"):
                                                        added_count += 1
                                            console.print(f"[green]Added {added_count} selected HS codes to database.[/green]")
                                        except Exception:
                                            console.print("[red]Invalid selection format.[/red]")
                                    elif save_option == 3:
                                        console.print("[yellow]Skipped saving new codes.[/yellow]")
                                    else:
                                        console.print("[red]Invalid option.[/red]")
                                else:
                                    console.print("[red]No HS codes found in DeepSeek response.[/red]")
                            except Exception as e:
                                console.print(f"[red]Error querying DeepSeek: {e}[/red]")
                        else:
                            console.print(f"[yellow]Querying DeepSeek for {country}-specific HS codes...[/yellow]")
                            try:
                                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                                    task = progress.add_task("[yellow]Contacting DeepSeek...", start=False)
                                    progress.start_task(task)
                                    deepseek_response = query_deepseek_for_hs_codes(country)
                                console.print("[bold green]DeepSeek Results:[/bold green]")
                                console.print(deepseek_response)
                                new_codes = parse_hs_codes_from_deepseek(deepseek_response)
                                if new_codes:
                                    console.print(f"\n[green]Found {len(new_codes)} new HS codes for {country}:[/green]")
                                    for idx, code_info in enumerate(new_codes, 1):
                                        console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                                    console.print("\n[bold]What would you like to do with these codes?[/bold]")
                                    console.print("[cyan]1.[/cyan] Add all new codes")
                                    console.print("[cyan]2.[/cyan] Select specific codes to add")
                                    console.print("[cyan]3.[/cyan] Skip saving")
                                    save_option = typer.prompt("Select option", type=int)
                                    if save_option == 1:
                                        added_count = 0
                                        for code_info in new_codes:
                                            if save_asia_hs_code(code_info['hs_code'], code_info['description'], country, source="DeepSeek"):
                                                added_count += 1
                                        console.print(f"[green]Added {added_count} new HS codes for {country} to database.[/green]")
                                    elif save_option == 2:
                                        console.print("[bold]Select codes to add (comma-separated numbers):[/bold]")
                                        for idx, code_info in enumerate(new_codes, 1):
                                            console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                                        selection = typer.prompt("Enter numbers (e.g., 1,3,5)")
                                        try:
                                            selected_indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip().isdigit()]
                                            added_count = 0
                                            for idx in selected_indices:
                                                if 0 <= idx < len(new_codes):
                                                    code_info = new_codes[idx]
                                                    if save_asia_hs_code(code_info['hs_code'], code_info['description'], country, source="DeepSeek"):
                                                        added_count += 1
                                            console.print(f"[green]Added {added_count} selected HS codes for {country} to database.[/green]")
                                        except Exception:
                                            console.print("[red]Invalid selection format.[/red]")
                                    elif save_option == 3:
                                        console.print("[yellow]Skipped saving new codes.[/yellow]")
                                    else:
                                        console.print("[red]Invalid option.[/red]")
                                else:
                                    console.print("[red]No HS codes found in DeepSeek response.[/red]")
                            except Exception as e:
                                console.print(f"[red]Error querying DeepSeek: {e}[/red]")
                    elif add_method == 2:
                        # Manually add HS code
                        hs_code = typer.prompt("Enter HS Code")
                        description = typer.prompt("Enter description")
                        source = typer.prompt("Enter source (optional)", default="Manual")
                        if scope_choice == 1:
                            success = save_asia_hs_code(hs_code, description, country)
                            if success:
                                console.print(f"[green]HS Code {hs_code} - {description} added to Asia codes for {country}.[/green]")
                            else:
                                console.print(f"[red]HS Code {hs_code} already exists in Asia codes for {country}.[/red]")
                        elif scope_choice == 2:
                            success = save_global_hs_code(hs_code, description, country)
                            if success:
                                console.print(f"[green]HS Code {hs_code} - {description} added to Global codes for {country}.[/green]")
                            else:
                                console.print(f"[red]HS Code {hs_code} already exists in Global codes for {country}.[/red]")
                        else:
                            console.print("[red]Invalid scope selection.[/red]")
                    else:
                        console.print("[red]Invalid option.[/red]")
                elif crud_choice == 2:
                    # Edit Existing HS Code (country-specific only)
                    console.print("[bold]Edit Country-Specific HS Code[/bold]")
                    console.print("[bold]Select scope for country:[/bold]")
                    console.print("[cyan]1.[/cyan] Asia")
                    console.print("[cyan]2.[/cyan] Global")
                    console.print("[cyan]3.[/cyan] Back to HS Code Management")
                    region_choice = typer.prompt("Select region", type=int)
                    if region_choice == 3:
                        continue
                    if region_choice == 1:
                        current_scope = "Asia"
                        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'asia_countries.txt'))
                    elif region_choice == 2:
                        current_scope = "Global"
                        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'global_countries.txt'))
                    else:
                        console.print("[red]Invalid region selection.[/red]")
                        continue
                    console.print("[bold]Select country:[/bold]")
                    for idx, country in enumerate(country_list, 1):
                        console.print(f"[cyan]{idx}.[/cyan] {country}")
                    console.print(f"[cyan]{len(country_list)+1}.[/cyan] Back to previous menu")
                    country_idx = typer.prompt("Enter number to select country", type=int)
                    if country_idx == len(country_list)+1:
                        continue
                    if 1 <= country_idx <= len(country_list):
                        country = country_list[country_idx-1]
                    else:
                        console.print("[red]Invalid country selection.[/red]")
                        continue
                    codes = [c for c in get_all_asia_hs_codes() if c['country'].lower() == country.lower()]
                    if not codes:
                        console.print(f"[red]No HS codes to edit for {country}.[/red]")
                        continue
                    console.print(f"[bold]Select HS code to edit for {country}:[/bold]")
                    for idx, code_info in enumerate(codes, 1):
                        console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                    idx = typer.prompt("Enter number to edit", type=int)
                    if 1 <= idx <= len(codes):
                        old_code_info = codes[idx-1]
                        # Field selection
                        fields = ['hs_code', 'description']
                        field_names = ['HS Code', 'Description']
                        console.print("[bold]Do you want to edit a single field or multiple fields?[/bold]")
                        console.print("[cyan]1.[/cyan] Single Field")
                        console.print("[cyan]2.[/cyan] Multiple Fields")
                        mode = typer.prompt("Enter 1 or 2", type=int)
                        updated_fields = {}
                        if mode == 1:
                            for i, name in enumerate(field_names, 1):
                                console.print(f"[cyan]{i}.[/cyan] {name}")
                            field_idx = typer.prompt("Select field number to edit", type=int)
                            if 1 <= field_idx <= len(fields):
                                field = fields[field_idx-1]
                                new_val = typer.prompt(f"Enter new {field_names[field_idx-1]}", default=old_code_info.get(field, ''))
                                if new_val != old_code_info.get(field, ''):
                                    updated_fields[field] = new_val
                            else:
                                console.print("[red]Invalid field selection.[/red]")
                        elif mode == 2:
                            for i, name in enumerate(field_names, 1):
                                console.print(f"[cyan]{i}.[/cyan] {name}")
                            field_idxs = typer.prompt("Enter field numbers to edit (comma-separated, e.g. 1,2)")
                            try:
                                selected = [int(x.strip()) for x in field_idxs.split(',') if x.strip().isdigit()]
                                for field_idx in selected:
                                    if 1 <= field_idx <= len(fields):
                                        field = fields[field_idx-1]
                                        new_val = typer.prompt(f"Enter new {field_names[field_idx-1]}", default=old_code_info.get(field, ''))
                                        if new_val != old_code_info.get(field, ''):
                                            updated_fields[field] = new_val
                                    else:
                                        console.print(f"[red]Invalid field number: {field_idx}")
                            except Exception:
                                console.print("[red]Invalid input format.[/red]")
                        else:
                            console.print("[red]Invalid selection.[/red]")
                        # Save changes
                        if updated_fields:
                            # Always require hs_code and description for update_asia_hs_code
                            new_hs_code = updated_fields.get('hs_code', old_code_info['hs_code'])
                            new_description = updated_fields.get('description', old_code_info['description'])
                            # If source is updated, update it separately
                            update_success = update_asia_hs_code(old_code_info['id'], new_hs_code, new_description)
                            if update_success:
                                from db import DB_PATH
                                import sqlite3
                                conn = sqlite3.connect(DB_PATH)
                                c = conn.cursor()
                                if current_scope == "Asia":
                                    c.execute('UPDATE asia_hs_codes SET source = ? WHERE id = ?', ("custom", old_code_info['id']))
                                elif current_scope == "Global":
                                    c.execute('UPDATE global_hs_codes SET source = ? WHERE id = ?', ("custom", old_code_info['id']))
                                conn.commit()
                                conn.close()
                            if update_success:
                                console.print("[green]HS code updated successfully![/green]")
                            else:
                                console.print("[red]Failed to update HS code.[/red]")
                        else:
                            console.print("[yellow]No changes made.[/yellow]")
                    else:
                        console.print("[red]Invalid selection.[/red]")
                elif crud_choice == 3:
                    # Delete Country-Specific HS Code (no global option)
                    console.print("[bold]Delete Country-Specific HS Code[/bold]")
                    console.print("[bold]Select scope for country:[/bold]")
                    console.print("[cyan]1.[/cyan] Asia")
                    console.print("[cyan]2.[/cyan] Global")
                    console.print("[cyan]3.[/cyan] Back to HS Code Management")
                    region_choice = typer.prompt("Select region", type=int)
                    if region_choice == 3:
                        continue
                    if region_choice == 1:
                        current_scope = "Asia"
                        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'asia_countries.txt'))
                    elif region_choice == 2:
                        current_scope = "Global"
                        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'global_countries.txt'))
                    else:
                        console.print("[red]Invalid region selection.[/red]")
                        continue
                    console.print("[bold]Select country:[/bold]")
                    for idx, country in enumerate(country_list, 1):
                        console.print(f"[cyan]{idx}.[/cyan] {country}")
                    console.print(f"[cyan]{len(country_list)+1}.[/cyan] Back to previous menu")
                    country_idx = typer.prompt("Enter number to select country", type=int)
                    if country_idx == len(country_list)+1:
                        continue
                    if 1 <= country_idx <= len(country_list):
                        country = country_list[country_idx-1]
                    else:
                        console.print("[red]Invalid country selection.[/red]")
                        continue
                    codes = [c for c in get_all_asia_hs_codes() if c['country'].lower() == country.lower()]
                    if not codes:
                        console.print(f"[red]No HS codes to delete for {country}.[/red]")
                        continue
                    console.print(f"[bold]Select HS code(s) to delete for {country} (comma-separated numbers, e.g. 1,3,5):[/bold]")
                    for idx, code_info in enumerate(codes, 1):
                        console.print(f"[cyan]{idx}.[/cyan] {code_info['hs_code']} - {code_info['description']}")
                    selection = typer.prompt("Enter number(s) to delete (comma-separated)")
                    try:
                        selected_indices = [int(x.strip())-1 for x in selection.split(',') if x.strip().isdigit()]
                    except Exception:
                        console.print("[red]Invalid input: please enter number(s) separated by commas (e.g. 1,2,3).[/red]")
                        continue

                    to_delete = [codes[idx] for idx in selected_indices if 0 <= idx < len(codes)]
                    if not to_delete:
                        console.print("[red]No valid codes selected for deletion.[/red]")
                        continue

                    confirm = typer.confirm(f"Are you sure you want to delete {len(to_delete)} HS code(s) for {country}?", default=False)
                    if confirm:
                        deleted_count = 0
                        for code_info in to_delete:
                            success = delete_asia_hs_code(code_info['id'])
                            if success:
                                deleted_count += 1
                        console.print(f"[green]{deleted_count} HS code(s) deleted for {country}.[/green]")
                    else:
                        console.print("[yellow]Delete cancelled.[/yellow]")
                elif crud_choice == 4:
                    while True:
                        console.print("[bold]View HS Codes Menu[/bold]")
                        console.print("[cyan]1.[/cyan] View All HS Codes (all scopes)")
                        console.print("[cyan]2.[/cyan] View Asia HS Codes")
                        console.print("[cyan]3.[/cyan] View Global HS Codes")
                        console.print("[cyan]4.[/cyan] View International HS Codes")
                        console.print("[cyan]5.[/cyan] Back to previous menu")
                        view_choice = typer.prompt("Select an option", type=int)
                        if view_choice == 1:
                            global_codes = get_all_global_hs_codes()
                            asia_codes = get_all_asia_hs_codes()
                            intl_codes = get_all_international_hs_codes()
                            table = Table(title="All HS Codes (Asia, Global, International)", show_lines=True)
                            table.add_column("No.", style="cyan", justify="right")
                            table.add_column("Scope", style="green")
                            table.add_column("Country", style="green")
                            table.add_column("HS Code", style="magenta")
                            table.add_column("Description", style="yellow")
                            table.add_column("Source", style="blue")
                            table.add_column("Created", style="dim")
                            idx = 1
                            for code_info in asia_codes:
                                table.add_row(str(idx), "Asia", code_info['country'], code_info['hs_code'], code_info['description'], code_info.get('source', '-'), code_info.get('created_at', '-'))
                                idx += 1
                            for code_info in global_codes:
                                table.add_row(str(idx), "Global", code_info['country'], code_info['hs_code'], code_info['description'], code_info.get('source', '-'), code_info.get('created_at', '-'))
                                idx += 1
                            for code_info in intl_codes:
                                table.add_row(str(idx), "International", code_info.get('country', '-'), code_info['hs_code'], code_info['description'], code_info.get('source', '-'), code_info.get('created_at', '-'))
                                idx += 1
                            console.print(table)
                        elif view_choice == 2:
                            # Asia HS Codes
                            while True:
                                console.print("[bold]View Asia HS Codes[/bold]")
                                console.print("[cyan]1.[/cyan] View all Asia HS codes")
                                console.print("[cyan]2.[/cyan] View HS codes for a specific country")
                                console.print("[cyan]3.[/cyan] Back")
                                asia_view_choice = typer.prompt("Select an option", type=int)
                                asia_codes = get_all_asia_hs_codes()
                                if asia_view_choice == 1:
                                    table = Table(title="Asia HS Codes", show_lines=True)
                                    table.add_column("No.", style="cyan", justify="right")
                                    table.add_column("Country", style="green")
                                    table.add_column("HS Code", style="magenta")
                                    table.add_column("Description", style="yellow")
                                    table.add_column("Source", style="blue")
                                    table.add_column("Created", style="dim")
                                    for idx, row in enumerate(asia_codes, 1):
                                        table.add_row(str(idx), row['country'], row['hs_code'], row['description'], row.get('source', '-'), row.get('created_at', '-'))
                                    console.print(table)
                                elif asia_view_choice == 2:
                                    # Get unique countries from asia_codes
                                    countries = sorted(set(row['country'] for row in asia_codes))
                                    if not countries:
                                        console.print("[red]No Asia HS codes available.[/red]")
                                        continue
                                    for idx, country in enumerate(countries, 1):
                                        console.print(f"[cyan]{idx}.[/cyan] {country}")
                                    console.print(f"[cyan]{len(countries)+1}.[/cyan] Back")
                                    cidx = typer.prompt("Select a country", type=int)
                                    if cidx == len(countries)+1:
                                        continue
                                    if 1 <= cidx <= len(countries):
                                        country = countries[cidx-1]
                                        filtered = [row for row in asia_codes if row['country'] == country]
                                        table = Table(title=f"Asia HS Codes for {country}", show_lines=True)
                                        table.add_column("No.", style="cyan", justify="right")
                                        table.add_column("HS Code", style="magenta")
                                        table.add_column("Description", style="yellow")
                                        table.add_column("Source", style="blue")
                                        table.add_column("Created", style="dim")
                                        for idx, row in enumerate(filtered, 1):
                                            table.add_row(str(idx), row['hs_code'], row['description'], row.get('source', '-'), row.get('created_at', '-'))
                                        console.print(table)
                                    else:
                                        console.print("[red]Invalid selection.[/red]")
                                elif asia_view_choice == 3:
                                    break
                                else:
                                    console.print("[red]Invalid option.[/red]")
                        elif view_choice == 3:
                            # Global HS Codes
                            while True:
                                console.print("[bold]View Global HS Codes[/bold]")
                                console.print("[cyan]1.[/cyan] View all Global HS codes")
                                console.print("[cyan]2.[/cyan] View HS codes for a specific country")
                                console.print("[cyan]3.[/cyan] Back")
                                global_view_choice = typer.prompt("Select an option", type=int)
                                global_codes = get_all_global_hs_codes()
                                if global_view_choice == 1:
                                    table = Table(title="Global HS Codes", show_lines=True)
                                    table.add_column("No.", style="cyan", justify="right")
                                    table.add_column("Country", style="green")
                                    table.add_column("HS Code", style="magenta")
                                    table.add_column("Description", style="yellow")
                                    table.add_column("Source", style="blue")
                                    table.add_column("Created", style="dim")
                                    for idx, row in enumerate(global_codes, 1):
                                        table.add_row(str(idx), row['country'], row['hs_code'], row['description'], row.get('source', '-'), row.get('created_at', '-'))
                                    console.print(table)
                                elif global_view_choice == 2:
                                    countries = sorted(set(row['country'] for row in global_codes))
                                    if not countries:
                                        console.print("[red]No Global HS codes available.[/red]")
                                        continue
                                    for idx, country in enumerate(countries, 1):
                                        console.print(f"[cyan]{idx}.[/cyan] {country}")
                                    console.print(f"[cyan]{len(countries)+1}.[/cyan] Back")
                                    cidx = typer.prompt("Select a country", type=int)
                                    if cidx == len(countries)+1:
                                        continue
                                    if 1 <= cidx <= len(countries):
                                        country = countries[cidx-1]
                                        filtered = [row for row in global_codes if row['country'] == country]
                                        table = Table(title=f"Global HS Codes for {country}", show_lines=True)
                                        table.add_column("No.", style="cyan", justify="right")
                                        table.add_column("HS Code", style="magenta")
                                        table.add_column("Description", style="yellow")
                                        table.add_column("Source", style="blue")
                                        table.add_column("Created", style="dim")
                                        for idx, row in enumerate(filtered, 1):
                                            table.add_row(str(idx), row['hs_code'], row['description'], row.get('source', '-'), row.get('created_at', '-'))
                                        console.print(table)
                                    else:
                                        console.print("[red]Invalid selection.[/red]")
                                elif global_view_choice == 3:
                                    break
                                else:
                                    console.print("[red]Invalid option.[/red]")
                        elif view_choice == 4:
                            # International HS Codes
                            intl_codes = get_all_international_hs_codes()
                            table = Table(title="International HS Codes", show_lines=True)
                            table.add_column("No.", style="cyan", justify="right")
                            table.add_column("HS Code", style="magenta")
                            table.add_column("Description", style="yellow")
                            table.add_column("Source", style="blue")
                            table.add_column("Created", style="dim")
                            for idx, row in enumerate(intl_codes, 1):
                                table.add_row(str(idx), row['hs_code'], row['description'], row.get('source', '-'), row.get('created_at', '-'))
                            console.print(table)
                        elif view_choice == 5:
                            break
                        else:
                            console.print("[red]Invalid option.[/red]")
                elif crud_choice == 5:
                    break
                else:
                    console.print("[red]Invalid option. Please try again.[/red]")
        elif choice == 3:
            # Manage Potential Buyer List
            while True:
                crud_choice = buyer_history_crud_menu()
                if crud_choice == 1:
                    results = fetch_all_results()
                    if not results:
                        console.print("[red]No past buyer search results found.[/red]")
                    else:
                        table = Table(title="Buyer Search History", show_lines=True)
                        table.add_column("No.", style="cyan", justify="right")
                        table.add_column("HS Code", style="magenta")
                        table.add_column("Keyword", style="yellow")
                        table.add_column("Country", style="green")
                        table.add_column("Company Name", style="bold")
                        table.add_column("Company Country", style="blue")
                        table.add_column("Website", style="underline")
                        table.add_column("Description", style="dim", overflow="fold")
                        for idx, row in enumerate(results, 1):
                            table.add_row(
                                str(idx),
                                row['hs_code'],
                                row['keyword'],
                                row['country'],
                                row['company_name'],
                                row['company_country'],
                                row['company_website_link'],
                                (row['description'][:60] + '...') if row['description'] and len(row['description']) > 60 else (row['description'] or "")
                            )
                        console.print(table)
                elif crud_choice == 2:
                    results = fetch_all_results()
                    if not results:
                        console.print("[red]No records to edit.[/red]")
                        continue
                    for idx, row in enumerate(results, 1):
                        console.print(f"[cyan]{idx}.[/cyan] {row['company_name']} ({row['hs_code']}, {row['keyword']}, {row['country']})")
                    idx = typer.prompt("Enter number to edit", type=int)
                    if 1 <= idx <= len(results):
                        record = results[idx-1]
                        fields = ['hs_code', 'keyword', 'country', 'company_name', 'company_country', 'company_website_link', 'description']
                        field_names = [f.replace('_', ' ').title() for f in fields]
                        console.print("[bold]Do you want to edit a single field or multiple fields?[/bold]")
                        console.print("[cyan]1.[/cyan] Single Field")
                        console.print("[cyan]2.[/cyan] Multiple Fields")
                        mode = typer.prompt("Enter 1 or 2", type=int)
                        updated_fields = {}
                        if mode == 1:
                            for i, name in enumerate(field_names, 1):
                                console.print(f"[cyan]{i}.[/cyan] {name}")
                            field_idx = typer.prompt("Select field number to edit", type=int)
                            if 1 <= field_idx <= len(fields):
                                field = fields[field_idx-1]
                                new_val = typer.prompt(f"Enter new {field_names[field_idx-1]}", default=record[field])
                                if new_val != record[field]:
                                    updated_fields[field] = new_val
                            else:
                                console.print("[red]Invalid field selection.[/red]")
                        elif mode == 2:
                            for i, name in enumerate(field_names, 1):
                                console.print(f"[cyan]{i}.[/cyan] {name}")
                            field_idxs = typer.prompt("Enter field numbers to edit (comma-separated, e.g. 1,3,5)")
                            try:
                                selected = [int(x.strip()) for x in field_idxs.split(',') if x.strip().isdigit()]
                                for field_idx in selected:
                                    if 1 <= field_idx <= len(fields):
                                        field = fields[field_idx-1]
                                        new_val = typer.prompt(f"Enter new {field_names[field_idx-1]}", default=record[field])
                                        if new_val != record[field]:
                                            updated_fields[field] = new_val
                                    else:
                                        console.print(f"[red]Invalid field number: {field_idx}[/red]")
                            except Exception:
                                console.print("[red]Invalid input format.[/red]")
                        else:
                            console.print("[red]Invalid selection.[/red]")
                        if updated_fields:
                            success = update_result(record['id'], updated_fields)
                            if success:
                                console.print("[green]Record updated successfully![/green]")
                            else:
                                console.print("[red]Failed to update record.[/red]")
                        else:
                            console.print("[yellow]No changes made.[/yellow]")
                    else:
                        console.print("[red]Invalid selection.[/red]")
                elif crud_choice == 3:
                    results = fetch_all_results()
                    if not results:
                        console.print("[red]No records to delete.[/red]")
                        continue
                    for idx, row in enumerate(results, 1):
                        console.print(f"[cyan]{idx}.[/cyan] {row['company_name']} ({row['hs_code']}, {row['keyword']}, {row['country']})")
                    idx = typer.prompt("Enter number to delete", type=int)
                    if 1 <= idx <= len(results):
                        record = results[idx-1]
                        confirm = typer.confirm(f"Are you sure you want to delete {record['company_name']} ({record['hs_code']}, {record['keyword']}, {record['country']})?", default=False)
                        if confirm:
                            success = delete_result(record['id'])
                            if success:
                                console.print("[green]Record deleted successfully![/green]")
                            else:
                                console.print("[red]Failed to delete record.[/red]")
                        else:
                            console.print("[yellow]Delete cancelled.[/yellow]")
                    else:
                        console.print("[red]Invalid selection.[/red]")
                elif crud_choice == 4:
                    # Check for duplicates
                    duplicates = get_duplicate_summary()
                    if not duplicates:
                        console.print("[green]No duplicate companies found in the database.[/green]")
                    else:
                        console.print(f"[yellow]Found {len(duplicates)} groups of duplicate companies:[/yellow]")
                        table = Table(title="Duplicate Companies Summary", show_lines=True)
                        table.add_column("No.", style="cyan", justify="right")
                        table.add_column("Company Name", style="bold")
                        table.add_column("Company Country", style="blue")
                        table.add_column("Duplicate Count", style="red")
                        for idx, duplicate in enumerate(duplicates, 1):
                            table.add_row(
                                str(idx),
                                duplicate['company_name'],
                                duplicate['company_country'],
                                str(duplicate['duplicate_count'])
                            )
                        console.print(table)
                        
                        total_duplicates = sum(dup['duplicate_count'] for dup in duplicates)
                        total_to_remove = total_duplicates - len(duplicates)  # Keep one from each group
                        console.print(f"[yellow]Total duplicate records: {total_duplicates}[/yellow]")
                        console.print(f"[yellow]Records to be removed: {total_to_remove}[/yellow]")
                        
                        # Ask user if they want to remove duplicates
                        console.print("\n[bold]Do you want to remove these duplicates?[/bold]")
                        console.print("[cyan]1.[/cyan] Yes, remove all duplicates (keep oldest record from each group)")
                        console.print("[cyan]2.[/cyan] No, keep all records")
                        
                        remove_choice = typer.prompt("Select option", type=int)
                        
                        if remove_choice == 1:
                            confirm = typer.confirm("Are you sure you want to remove all duplicates? (This will keep the oldest record from each duplicate group)", default=False)
                            if confirm:
                                result = find_and_remove_duplicates()
                                console.print(f"[green]Duplicate removal completed![/green]")
                                console.print(f"[green]Duplicate groups found: {result['duplicate_groups']}[/green]")
                                console.print(f"[green]Total duplicates found: {result['duplicates_found']}[/green]")
                                console.print(f"[green]Duplicates removed: {result['duplicates_removed']}[/green]")
                            else:
                                console.print("[yellow]Duplicate removal cancelled.[/yellow]")
                        elif remove_choice == 2:
                            console.print("[yellow]Duplicate removal skipped. All records kept.[/yellow]")
                        else:
                            console.print("[red]Invalid option.[/red]")
                elif crud_choice == 5:
                    break
                else:
                    console.print("[red]Invalid option. Please try again.[/red]")
        elif choice == 4:
            # Export Results (CSV)
            results = fetch_all_results()
            if not results:
                console.print("[red]No results to export.[/red]")
            else:
                export_dir = os.path.join(os.path.dirname(__file__), '..', 'EXPORT')
                os.makedirs(export_dir, exist_ok=True)
                default_filename = 'buyer_search_results.csv'
                export_path = os.path.join(export_dir, default_filename)
                if os.path.exists(export_path):
                    console.print(f"[yellow]A file named {default_filename} already exists in EXPORT.[/yellow]")
                    replace = typer.confirm("Do you want to replace the existing file? (No will create a new file with timestamp)", default=False)
                    if not replace:
                        import datetime
                        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        export_path = os.path.join(export_dir, f'buyer_search_results_{timestamp}.csv')
                with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                    if results:
                        writer = csv.DictWriter(csvfile, fieldnames=results[0].keys())
                        writer.writeheader()
                        writer.writerows(results)
                console.print(f"[green]Results exported to:[/green] [bold]{export_path}[/bold]")
        elif choice == 5:
            console.print("[green]Goodbye!")
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]")

if __name__ == "__main__":
    app() 