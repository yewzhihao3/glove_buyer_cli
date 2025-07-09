import os
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from db import (
    check_existing_buyer_leads, insert_results, insert_buyer_leads,
    get_all_asia_hs_codes, get_all_global_hs_codes, get_all_international_hs_codes,
    save_asia_hs_code, save_global_hs_code, fetch_all_results, update_result, delete_result
)
from deepseek_agent import query_deepseek, query_deepseek_for_hs_codes, query_deepseek_for_global_hs_codes, parse_hs_codes_from_deepseek
from db import parse_deepseek_output

console = Console()

def load_country_list(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def perform_buyer_search(scope, country, selected_code, selected_desc):
    # (Full perform_buyer_search logic from main.py goes here)
    keyword_file = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'keyword_options.txt')
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
    existing_buyers = check_existing_buyer_leads(scope, selected_code, keyword)
    if existing_buyers:
        console.print(f"[green]Found {len(existing_buyers)} existing buyer leads for HS Code {selected_code} ({selected_desc}) in {country} with keyword '{keyword}':[/green]")
        from rich.table import Table
        table = Table(title="Existing Buyer Leads", show_lines=True)
        table.add_column("No.", style="cyan", justify="right")
        table.add_column("Company Name", style="bold")
        table.add_column("Country", style="green")
        table.add_column("Website", style="blue")
        for idx, buyer in enumerate(existing_buyers, 1):
            table.add_row(
                str(idx),
                buyer.get('company_name', ''),
                buyer.get('company_country', ''),
                buyer.get('company_website_link', '')
            )
        console.print(table)
        console.print("\n[bold]Options:[/bold]")
        console.print("[cyan]1.[/cyan] Use existing results")
        console.print("[cyan]2.[/cyan] Query DeepSeek for new results")
        console.print("[cyan]3.[/cyan] Back to keyword selection")
        buyer_option = typer.prompt("Select option", type=int)
        if buyer_option == 1:
            console.print("[green]Using existing buyer leads.[/green]")
            return True
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
                insert_results(selected_code, keyword, country, companies)
                insert_buyer_leads(scope, selected_code, keyword, companies)
                console.print(f"[green]{len(companies)} companies saved to both results and {scope} buyer leads (duplicates skipped).[/green]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        elif buyer_option == 3:
            return False
        else:
            console.print("[red]Invalid option.[/red]")
            return False
    else:
        console.print(f"[yellow]Searching buyers for HS Code {selected_code} ({selected_desc}) in {country} with keyword '{keyword}'...[/yellow]")
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                task = progress.add_task("[yellow]Contacting DeepSeek...", start=False)
                progress.start_task(task)
                result = query_deepseek(selected_code, keyword, country, [])
            console.print("[bold green]DeepSeek Results:[/bold green]")
            console.print(result)
            companies = parse_deepseek_output(result)
            insert_results(selected_code, keyword, country, companies)
            insert_buyer_leads(scope, selected_code, keyword, companies)
            console.print(f"[green]{len(companies)} companies saved to both results and {scope} buyer leads (duplicates skipped).[/green]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return False
    return True

def select_country_and_scope():
    console.print("[bold]Choose search scope:[/bold]")
    console.print("[cyan]1.[/cyan] Asia")
    console.print("[cyan]2.[/cyan] Global")
    console.print("[cyan]3.[/cyan] Back to Main Menu")
    scope = typer.prompt("Enter number for scope", type=int)
    if scope == 3:
        return None, None
    if scope == 1:
        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'asia_countries.txt'))
        scope_name = "Asia"
    elif scope == 2:
        country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'global_countries.txt'))
        scope_name = "Global"
    else:
        console.print("[red]Invalid scope selection.[/red]")
        return None, None
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

def buyer_search_menu():
    buyer_search_active = True
    while buyer_search_active:
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
                country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'asia_countries.txt'))
                scope_name = "Asia"
            elif scope == 2:
                country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'global_countries.txt'))
                scope_name = "Global"
            else:
                console.print("[red]Invalid scope selection.[/red]")
                continue
            if not country_list:
                console.print(f"[yellow]No companies found in {scope_name} database.[/yellow]")
                continue
        if scope == 3:
            buyer_search_active = False
            break
        country_selection_active = True
        while country_selection_active and buyer_search_active:
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
            if scope_name == "Asia":
                existing_codes = [c for c in get_all_asia_hs_codes() if c['country'].lower() == country.lower()]
            else:
                existing_codes = [c for c in get_all_global_hs_codes() if c['country'].lower() == country.lower()]
            if not existing_codes:
                console.print(f"[yellow]No HS codes found for {country}.[/yellow]")
            hs_code_selection_active = True
            while hs_code_selection_active and country_selection_active and buyer_search_active:
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
                        perform_buyer_search(scope_name, country, selected_code, selected_desc)
                        console.print("[bold]What would you like to do next?[/bold]")
                        console.print("[cyan]1.[/cyan] Search again with the same country")
                        console.print("[cyan]2.[/cyan] Search in a different country")
                        console.print("[cyan]3.[/cyan] Change scope")
                        console.print("[cyan]4.[/cyan] Back to main menu")
                        next_action = typer.prompt("Select option", type=int)
                        if next_action == 1:
                            continue
                        elif next_action == 2:
                            break
                        elif next_action == 3:
                            break
                        elif next_action == 4:
                            buyer_search_active = False
                            country_selection_active = False
                            hs_code_selection_active = False
                            break
                        else:
                            console.print("[red]Invalid option.[/red]")
                            break
                    else:
                        console.print("[red]Invalid selection.[/red]")
                        continue
                else:
                    break 