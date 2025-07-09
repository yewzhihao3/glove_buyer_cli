import typer
from rich.console import Console
from rich.table import Table
from db_apollo import get_all_contacts, update_contact, delete_contact, find_duplicate_contacts

console = Console()

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

def buyer_list_menu():
    while True:
        crud_choice = buyer_history_crud_menu()
        if crud_choice == 1:
            # View All Potential Buyers
            buyers = get_all_contacts()
            if not buyers:
                console.print("[yellow]No potential buyers found.[/yellow]")
                continue
            table = Table(title="Potential Buyers", show_lines=True)
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("Company", style="bold")
            table.add_column("Name", style="green")
            table.add_column("Title", style="yellow")
            table.add_column("Email", style="magenta")
            table.add_column("LinkedIn", style="blue")
            for b in buyers:
                table.add_row(str(b['id']), b.get('company_name',''), b.get('name',''), b.get('title',''), b.get('email',''), b.get('linkedin',''))
            console.print(table)
        elif crud_choice == 2:
            # Edit Buyer Record
            buyers = get_all_contacts()
            if not buyers:
                console.print("[yellow]No potential buyers to edit.[/yellow]")
                continue
            table = Table(title="Select Buyer to Edit", show_lines=True)
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("Company", style="bold")
            table.add_column("Name", style="green")
            table.add_column("Title", style="yellow")
            table.add_column("Email", style="magenta")
            for b in buyers:
                table.add_row(str(b['id']), b.get('company_name',''), b.get('name',''), b.get('title',''), b.get('email',''))
            console.print(table)
            contact_id = typer.prompt("Enter the ID of the buyer to edit", type=int)
            selected = next((b for b in buyers if b['id'] == contact_id), None)
            if not selected:
                console.print("[red]Invalid ID selected.[/red]")
                continue
            new_name = typer.prompt(f"Enter new name [{selected['name']}]:", default=selected['name'])
            new_title = typer.prompt(f"Enter new title [{selected['title']}]:", default=selected['title'])
            new_email = typer.prompt(f"Enter new email [{selected['email']}]:", default=selected['email'])
            new_linkedin = typer.prompt(f"Enter new LinkedIn [{selected['linkedin']}]:", default=selected['linkedin'])
            updated = update_contact(contact_id, {
                'name': new_name,
                'title': new_title,
                'email': new_email,
                'linkedin': new_linkedin
            })
            if updated:
                console.print("[green]Buyer record updated successfully.[/green]")
            else:
                console.print("[red]Failed to update buyer record.[/red]")
        elif crud_choice == 3:
            # Delete Buyer Record
            buyers = get_all_contacts()
            if not buyers:
                console.print("[yellow]No potential buyers to delete.[/yellow]")
                continue
            table = Table(title="Select Buyer to Delete", show_lines=True)
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("Company", style="bold")
            table.add_column("Name", style="green")
            table.add_column("Title", style="yellow")
            table.add_column("Email", style="magenta")
            for b in buyers:
                table.add_row(str(b['id']), b.get('company_name',''), b.get('name',''), b.get('title',''), b.get('email',''))
            console.print(table)
            contact_id = typer.prompt("Enter the ID of the buyer to delete", type=int)
            selected = next((b for b in buyers if b['id'] == contact_id), None)
            if not selected:
                console.print("[red]Invalid ID selected.[/red]")
                continue
            confirm = typer.confirm(f"Are you sure you want to delete buyer {selected['name']} ({selected['email']})?", default=False)
            if not confirm:
                console.print("[yellow]Deletion cancelled.[/yellow]")
                continue
            deleted = delete_contact(contact_id)
            if deleted:
                console.print("[green]Buyer record deleted successfully.[/green]")
            else:
                console.print("[red]Failed to delete buyer record.[/red]")
        elif crud_choice == 4:
            # Check for Duplicates
            dups = find_duplicate_contacts()
            if not dups:
                console.print("[green]No duplicate buyer records found.[/green]")
                continue
            for group in dups:
                table = Table(title="Duplicate Buyer Group", show_lines=True)
                table.add_column("ID", style="cyan", justify="right")
                table.add_column("Company", style="bold")
                table.add_column("Name", style="green")
                table.add_column("Title", style="yellow")
                table.add_column("Email", style="magenta")
                table.add_column("LinkedIn", style="blue")
                for b in group:
                    table.add_row(str(b['id']), b.get('company_name',''), b.get('name',''), b.get('title',''), b.get('email',''), b.get('linkedin',''))
                console.print(table)
        elif crud_choice == 5:
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]") 