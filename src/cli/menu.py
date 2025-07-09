# menu.py - CLI main menu logic and navigation
import typer
from rich.console import Console

# Import feature menus (to be implemented)
from .buyer_search import buyer_search_menu
from .apollo_menu import apollo_menu
from .hs_code_menu import hs_code_menu
from .buyer_list_menu import buyer_list_menu
from .export_menu import export_menu

console = Console()

MENU_OPTIONS = [
    "Search Buyers with DeepSeek (Asia/Global/International)",
    "Find Decision Makers with Apollo.io",
    "Manage HS Codes (CRUD)",
    "Manage Potential Buyer List",
    "Export Results (CSV) [In Progress]",
    "Exit"
]

def main_menu():
    console.rule("[bold blue]🧠 Glove Buyer Intel CLI 🧠")
    for idx, option in enumerate(MENU_OPTIONS, 1):
        console.print(f"[cyan]{idx}.[/cyan] {option}")
    choice = typer.prompt("\nSelect an option", type=int)
    return choice

def run_cli():
    while True:
        choice = main_menu()
        if choice == 1:
            buyer_search_menu()
        elif choice == 2:
            apollo_menu()
        elif choice == 3:
            hs_code_menu()
        elif choice == 4:
            buyer_list_menu()
        elif choice == 5:
            export_menu()
        elif choice == 6:
            console.print("[green]Goodbye!")
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]") 