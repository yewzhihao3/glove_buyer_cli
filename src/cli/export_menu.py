import os
import typer
from rich.console import Console
import csv
from db import fetch_all_results

console = Console()

def export_menu():
    results = fetch_all_results()
    if not results:
        console.print("[red]No results to export.[/red]")
    else:
        export_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'EXPORT')
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