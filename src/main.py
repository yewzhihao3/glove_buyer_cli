import typer
from cli.menu import run_cli

app = typer.Typer()

@app.command()
def run():
    run_cli()

if __name__ == "__main__":
    app() 