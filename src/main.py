import typer
from rich.console import Console
import sys
import os
sys.path.append("..")  # Ensure parent dir is in path for imports
from hs_code_manager import load_hs_codes_xlsx, select_hs_code, add_hs_code, edit_hs_code, delete_hs_code
from rich.table import Table
from deepseek_agent import query_deepseek

app = typer.Typer()
console = Console()

MENU_OPTIONS = [
    "Select HS Code to Search",
    "Search Buyers with DeepSeek",
    "Manage HS Codes (CRUD)",
    "View Past Results",
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
                keyword = typer.prompt("Enter product keyword (press Enter to use 'glove')", default="glove")
                console.print(f"[yellow]Searching buyers for HS Code {hs_code} ({desc}) in {country} with keyword '{keyword}'...[/yellow]")
                try:
                    result = query_deepseek(hs_code, keyword, country)
                    console.print("[bold green]DeepSeek Results:[/bold green]")
                    console.print(result)
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
            console.print("[yellow]Feature coming soon: View Past Results[/yellow]")
        elif choice == 5:
            console.print("[yellow]Feature coming soon: Export Results (CSV)[/yellow]")
        elif choice == 6:
            console.print("[green]Goodbye!")
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]")

if __name__ == "__main__":
    app() 