import os
import typer
from rich.console import Console
import csv

# Use the new advanced Apollo extraction logic
from apollo_extraction import buyer_extraction, apollo_company_extraction, remove_duplicate_companies

console = Console()

def apollo_menu():
    while True:
        console.rule("[bold blue]Find Decision Makers with Apollo.io")
        console.print("[bold]Select option:[/bold]")
        console.print("[cyan]1.[/cyan] Company Extraction")
        console.print("[cyan]2.[/cyan] Buyer Extraction")
        console.print("[cyan]3.[/cyan] Remove Duplicate Companies")
        console.print("[cyan]4.[/cyan] Back")
        choice = typer.prompt("Select an option", type=int)
        if choice == 1:
            apollo_company_extraction()
        elif choice == 2:
            buyer_extraction()
        elif choice == 3:
            remove_duplicate_companies()
        elif choice == 4:
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]") 