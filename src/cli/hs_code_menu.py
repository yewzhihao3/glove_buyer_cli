import typer
from rich.console import Console
from rich.table import Table
from db import (
    get_all_global_hs_codes, get_all_asia_hs_codes, get_all_international_hs_codes,
    save_global_hs_code, save_asia_hs_code, update_global_hs_code, update_asia_hs_code,
    delete_global_hs_code, delete_asia_hs_code, get_available_countries_asia, get_available_countries_global
)
from deepseek_agent import query_deepseek_for_hs_codes, query_deepseek_for_global_hs_codes, parse_hs_codes_from_deepseek
import os
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

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

def hs_code_menu():
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
                country_list = get_available_countries_asia()
                current_scope = "Asia"
            elif scope_choice == 2:
                country_list = get_available_countries_global()
                current_scope = "Global"
            else:
                console.print("[red]Invalid scope selection.[/red]")
                continue
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
            console.print("[bold]How would you like to add HS codes for this selection?[/bold]")
            console.print("[cyan]1.[/cyan] Query DeepSeek for HS codes")
            console.print("[cyan]2.[/cyan] Manually add HS code")
            console.print("[cyan]3.[/cyan] Back to previous menu")
            add_method = typer.prompt("Select method", type=int)
            if add_method == 3:
                continue
            if add_method == 1:
                if country == "Global":
                    console.print("[yellow]Querying DeepSeek for global HS codes...[yellow]")
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
                    console.print(f"[yellow]Querying DeepSeek for {country}-specific HS codes...[yellow]")
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
            # Edit Existing HS Code
            console.print("[bold]Select scope for HS code to edit:[/bold]")
            console.print("[cyan]1.[/cyan] Asia")
            console.print("[cyan]2.[/cyan] Global")
            console.print("[cyan]3.[/cyan] Back to HS Code Management")
            scope_choice = typer.prompt("Select scope", type=int)
            if scope_choice == 3:
                continue
            if scope_choice == 1:
                country_list = get_available_countries_asia()
                current_scope = "Asia"
                get_codes = get_all_asia_hs_codes
                update_code = update_asia_hs_code
            elif scope_choice == 2:
                country_list = get_available_countries_global()
                current_scope = "Global"
                get_codes = get_all_global_hs_codes
                update_code = update_global_hs_code
            else:
                console.print("[red]Invalid scope selection.[/red]")
                continue
            console.print(f"[bold]Select a country from {current_scope}:[/bold]")
            for idx, country in enumerate(country_list, 1):
                console.print(f"[cyan]{idx}.[/cyan] {country}")
            console.print(f"[cyan]{len(country_list)+1}.[/cyan] Back to Scope Selection")
            country_idx = typer.prompt("Enter number to select country", type=int)
            if country_idx == len(country_list)+1:
                continue
            if 1 <= country_idx <= len(country_list):
                country = country_list[country_idx-1]
            else:
                console.print("[red]Invalid country selection.[/red]")
                continue
            codes = [c for c in get_codes() if c['country'].lower() == country.lower()]
            if not codes:
                console.print(f"[yellow]No HS codes found for {country}.[/yellow]")
                continue
            table = Table(title=f"HS Codes for {country}")
            table.add_column("No.", style="cyan", justify="right")
            table.add_column("HS Code", style="green")
            table.add_column("Description", style="white")
            for idx, c in enumerate(codes, 1):
                table.add_row(str(idx), c['hs_code'], c['description'])
            console.print(table)
            code_idx = typer.prompt("Select HS code to edit by number", type=int)
            if not (1 <= code_idx <= len(codes)):
                console.print("[red]Invalid selection.[/red]")
                continue
            selected = codes[code_idx-1]
            new_code = typer.prompt(f"Enter new HS Code [{selected['hs_code']}]", default=selected['hs_code'])
            new_desc = typer.prompt(f"Enter new description [{selected['description']}]", default=selected['description'])
            success = update_code(selected['id'], new_code, new_desc)
            if success:
                console.print(f"[green]HS Code updated successfully.[/green]")
            else:
                console.print(f"[red]Failed to update HS Code.[/red]")
        elif crud_choice == 3:
            # Delete HS Code
            console.print("[bold]Select scope for HS code to delete:[/bold]")
            console.print("[cyan]1.[/cyan] Asia")
            console.print("[cyan]2.[/cyan] Global")
            console.print("[cyan]3.[/cyan] Back to HS Code Management")
            scope_choice = typer.prompt("Select scope", type=int)
            if scope_choice == 3:
                continue
            if scope_choice == 1:
                country_list = get_available_countries_asia()
                current_scope = "Asia"
                get_codes = get_all_asia_hs_codes
                delete_code = delete_asia_hs_code
            elif scope_choice == 2:
                country_list = get_available_countries_global()
                current_scope = "Global"
                get_codes = get_all_global_hs_codes
                delete_code = delete_global_hs_code
            else:
                console.print("[red]Invalid scope selection.[/red]")
                continue
            console.print(f"[bold]Select a country from {current_scope}:[/bold]")
            for idx, country in enumerate(country_list, 1):
                console.print(f"[cyan]{idx}.[/cyan] {country}")
            console.print(f"[cyan]{len(country_list)+1}.[/cyan] Back to Scope Selection")
            country_idx = typer.prompt("Enter number to select country", type=int)
            if country_idx == len(country_list)+1:
                continue
            if 1 <= country_idx <= len(country_list):
                country = country_list[country_idx-1]
            else:
                console.print("[red]Invalid country selection.[/red]")
                continue
            codes = [c for c in get_codes() if c['country'].lower() == country.lower()]
            if not codes:
                console.print(f"[yellow]No HS codes found for {country}.[/yellow]")
                continue
            table = Table(title=f"HS Codes for {country}")
            table.add_column("No.", style="cyan", justify="right")
            table.add_column("HS Code", style="green")
            table.add_column("Description", style="white")
            for idx, c in enumerate(codes, 1):
                table.add_row(str(idx), c['hs_code'], c['description'])
            console.print(table)
            code_idx = typer.prompt("Select HS code to delete by number", type=int)
            if not (1 <= code_idx <= len(codes)):
                console.print("[red]Invalid selection.[/red]")
                continue
            selected = codes[code_idx-1]
            confirm = typer.confirm(f"Are you sure you want to delete HS Code {selected['hs_code']} - {selected['description']}?")
            if not confirm:
                console.print("[yellow]Deletion cancelled.[/yellow]")
                continue
            success = delete_code(selected['id'])
            if success:
                console.print(f"[green]HS Code deleted successfully.[/green]")
            else:
                console.print(f"[red]Failed to delete HS Code.[/red]")
        elif crud_choice == 4:
            # View All HS Codes
            console.print("[bold]Select scope to view HS codes:[/bold]")
            console.print("[cyan]1.[/cyan] Asia")
            console.print("[cyan]2.[/cyan] Global")
            console.print("[cyan]3.[/cyan] Back to HS Code Management")
            scope_choice = typer.prompt("Select scope", type=int)
            if scope_choice == 3:
                continue
            if scope_choice == 1:
                country_list = get_available_countries_asia()
                current_scope = "Asia"
                get_codes = get_all_asia_hs_codes
            elif scope_choice == 2:
                country_list = get_available_countries_global()
                current_scope = "Global"
                get_codes = get_all_global_hs_codes
            else:
                console.print("[red]Invalid scope selection.[/red]")
                continue
            console.print(f"[bold]Select a country from {current_scope}:[/bold]")
            for idx, country in enumerate(country_list, 1):
                console.print(f"[cyan]{idx}.[/cyan] {country}")
            console.print(f"[cyan]{len(country_list)+1}.[/cyan] Back to Scope Selection")
            country_idx = typer.prompt("Enter number to select country", type=int)
            if country_idx == len(country_list)+1:
                continue
            if 1 <= country_idx <= len(country_list):
                country = country_list[country_idx-1]
            else:
                console.print("[red]Invalid country selection.[/red]")
                continue
            codes = [c for c in get_codes() if c['country'].lower() == country.lower()]
            if not codes:
                console.print(f"[yellow]No HS codes found for {country}.[/yellow]")
                continue
            table = Table(title=f"HS Codes for {country}")
            table.add_column("No.", style="cyan", justify="right")
            table.add_column("HS Code", style="green")
            table.add_column("Description", style="white")
            for idx, c in enumerate(codes, 1):
                table.add_row(str(idx), c['hs_code'], c['description'])
            console.print(table)
        elif crud_choice == 5:
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]") 