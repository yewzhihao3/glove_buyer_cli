import typer
from rich.console import Console
import sys
import os
sys.path.append("..")  # Ensure parent dir is in path for imports
from hs_code_manager import load_hs_codes_xlsx, select_hs_code, add_hs_code, edit_hs_code, delete_hs_code
from rich.table import Table
from deepseek_agent import query_deepseek
from db import init_db, insert_results, parse_deepseek_output, fetch_all_results, update_result, delete_result
import pandas as pd
import datetime
import csv

app = typer.Typer()
console = Console()

MENU_OPTIONS = [
    "Select HS Code to Search",
    "Search Buyers with DeepSeek",
    "Manage HS Codes (CRUD)",
    "Manage Buyer Search History",
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

def buyer_history_crud_menu():
    crud_options = [
        "View All Buyer Search History",
        "Edit Buyer Search Record",
        "Delete Buyer Search Record",
        "Back to Main Menu"
    ]
    console.rule("[bold magenta]Buyer Search History Management[/bold magenta]")
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

@app.command()
def run():
    init_db()
    while True:
        choice = main_menu()
        if choice == 1:
            codes = load_hs_codes_xlsx()
            selected = select_hs_code(codes)
            if selected:
                code, desc = selected
                console.print(f"[green]Selected HS Code:[/green] [bold]{code}[/bold] - {desc}")
            else:
                console.print("[red]No HS code selected.[/red]")
        elif choice == 2:
            # Scope selection
            console.print("[bold]Choose search scope:[/bold]")
            console.print("[cyan]1.[/cyan] Asia")
            console.print("[cyan]2.[/cyan] Global")
            scope = typer.prompt("Enter number for scope", type=int)
            if scope == 1:
                country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'asia_countries.txt'))
                scope_name = "Asia"
            elif scope == 2:
                country_list = load_country_list(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'global_countries.txt'))
                scope_name = "Global"
            else:
                console.print("[red]Invalid scope selection.[/red]")
                continue
            # Country selection
            console.print(f"[bold]Select a country from {scope_name} or enter a custom country:[/bold]")
            for idx, country in enumerate(country_list, 1):
                console.print(f"[cyan]{idx}.[/cyan] {country}")
            console.print(f"[cyan]{len(country_list)+1}.[/cyan] [italic]Enter a custom country[/italic]")
            country_idx = typer.prompt("Enter number to select country or custom", type=int)
            if 1 <= country_idx <= len(country_list):
                country = country_list[country_idx-1]
            elif country_idx == len(country_list)+1:
                country = typer.prompt("Enter custom country name")
            else:
                console.print("[red]Invalid country selection.[/red]")
                continue
            # HS code selection
            codes = load_hs_codes_xlsx()
            if not codes:
                console.print("[red]No HS codes available.")
                continue
            console.print("[bold]Select HS code to search for buyers:[/bold]")
            for idx, (code, desc) in enumerate(codes, 1):
                console.print(f"[cyan]{idx}.[/cyan] {code} - {desc}")
            idx = typer.prompt("Enter number to search", type=int)
            if 1 <= idx <= len(codes):
                hs_code, desc = codes[idx-1]
                # Load keyword options from file
                keyword_file = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'keyword_options.txt')
                with open(keyword_file, 'r', encoding='utf-8') as f:
                    keyword_options = [line.strip() for line in f if line.strip()]
                console.print("[bold]Select product keyword:[/bold]")
                for kidx, keyword_option in enumerate(keyword_options, 1):
                    console.print(f"[cyan]{kidx}.[/cyan] {keyword_option.title()}")
                console.print(f"[cyan]{len(keyword_options)+1}.[/cyan] [italic]Custom Keyword[/italic]")
                keyword_choice = typer.prompt("Enter number to select keyword or custom", type=int)
                if 1 <= keyword_choice <= len(keyword_options):
                    keyword = keyword_options[keyword_choice-1]
                elif keyword_choice == len(keyword_options)+1:
                    keyword = typer.prompt("Enter custom product keyword")
                else:
                    console.print("[red]Invalid keyword selection.[/red]")
                    continue
                console.print(f"[yellow]Searching buyers for HS Code {hs_code} ({desc}) in {country} with keyword '{keyword}'...[/yellow]")
                try:
                    result = query_deepseek(hs_code, keyword, country)
                    console.print("[bold green]DeepSeek Results:[/bold green]")
                    console.print(result)
                    # Save to DB
                    companies = parse_deepseek_output(result)
                    console.print(f"[yellow]DEBUG: Parsed companies: {companies}[/yellow]")
                    insert_results(hs_code, keyword, country, companies)
                    console.print(f"[green]{len(companies)} companies saved to database (duplicates skipped).[/green]")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
            else:
                console.print("[red]Invalid selection.[/red]")
        elif choice == 3:
            while True:
                crud_choice = hs_code_crud_menu()
                if crud_choice == 1:
                    code = typer.prompt("Enter new HS Code")
                    desc = typer.prompt("Enter description")
                    success = add_hs_code(code, desc)
                    if success:
                        console.print(f"[green]HS Code {code} - {desc} added successfully![/green]")
                    else:
                        console.print(f"[red]HS Code {code} - {desc} already exists or could not be added.[/red]")
                elif crud_choice == 2:
                    codes = load_hs_codes_xlsx()
                    if not codes:
                        console.print("[red]No HS codes to edit.[/red]")
                        continue
                    console.print("[bold]Select HS code to edit:[/bold]")
                    for idx, (code, desc) in enumerate(codes, 1):
                        console.print(f"[cyan]{idx}.[/cyan] {code} - {desc}")
                    idx = typer.prompt("Enter number to edit", type=int)
                    if 1 <= idx <= len(codes):
                        old_code, old_desc = codes[idx-1]
                        new_code = typer.prompt("Enter new HS Code", default=old_code)
                        new_desc = typer.prompt("Enter new description", default=old_desc)
                        success = edit_hs_code(idx, new_code, new_desc)
                        if success:
                            console.print(f"[green]HS Code updated to: {new_code} - {new_desc}[/green]")
                        else:
                            console.print("[red]Failed to update HS Code.[/red]")
                    else:
                        console.print("[red]Invalid selection.[/red]")
                elif crud_choice == 3:
                    codes = load_hs_codes_xlsx()
                    if not codes:
                        console.print("[red]No HS codes to delete.[/red]")
                        continue
                    console.print("[bold]Select HS code to delete:[/bold]")
                    for idx, (code, desc) in enumerate(codes, 1):
                        console.print(f"[cyan]{idx}.[/cyan] {code} - {desc}")
                    idx = typer.prompt("Enter number to delete", type=int)
                    if 1 <= idx <= len(codes):
                        code, desc = codes[idx-1]
                        confirm = typer.confirm(f"Are you sure you want to delete {code} - {desc}?", default=False)
                        if confirm:
                            success = delete_hs_code(idx)
                            if success:
                                console.print(f"[green]HS Code {code} - {desc} deleted.[/green]")
                            else:
                                console.print("[red]Failed to delete HS Code.[/red]")
                        else:
                            console.print("[yellow]Delete cancelled.[/yellow]")
                    else:
                        console.print("[red]Invalid selection.[/red]")
                elif crud_choice == 4:
                    codes = load_hs_codes_xlsx()
                    if not codes:
                        console.print("[red]No HS codes found.[/red]")
                    else:
                        table = Table(title="HS Codes List")
                        table.add_column("No.", style="cyan", justify="right")
                        table.add_column("HS Code", style="magenta")
                        table.add_column("Description", style="green")
                        for idx, (code, desc) in enumerate(codes, 1):
                            table.add_row(str(idx), code, desc)
                        console.print(table)
                    # Future enhancement: Add search/filter functionality here
                elif crud_choice == 5:
                    break
                else:
                    console.print("[red]Invalid option. Please try again.[/red]")
        elif choice == 4:
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
                    break
                else:
                    console.print("[red]Invalid option. Please try again.[/red]")
        elif choice == 5:
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
        elif choice == 6:
            console.print("[green]Goodbye!")
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]")

if __name__ == "__main__":
    app() 