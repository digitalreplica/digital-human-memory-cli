#!/usr/bin/env python3
import os
import subprocess
import typer
import uuid

##### Globals #####
def copy_to_clipboard(text):
    """
    Copies the given text into the system clipboard
    :param text:
    :return:
    """
    subprocess.run("pbcopy", universal_newlines=True, input=text)

def open_file_in_editor(filename):
    """
    Opens a file in the preferred editor
    :param filename:
    :return:
    """
    subprocess.run(["atom", filename])

##### Typer #####
app = typer.Typer()

@app.command("guid")
def app_guid(
        verbose: bool = typer.Option(True, help="Verbose output")
):
    """
    Copy a random guid to the clipboard.
    """
    guid = str(uuid.uuid4())
    copy_to_clipboard(guid)
    if verbose:
        pretty_guid = typer.style(guid, fg=typer.colors.GREEN, bold=True)
        typer.echo(f"{pretty_guid} copied to clipboard")

@app.command("create")
def app_create(
        open_file: bool = typer.Option(True, "--open", help="Open the memory after creating"),
        verbose: bool = typer.Option(True, help="Verbose output")
):
    """
    Create a new memory.
    """
    while True:
        guid = str(uuid.uuid4())
        filename = f"{guid}.md"
        if not os.path.exists(filename):
            break
    if verbose:
        typer.echo("Creating new memory "+typer.style(filename, fg=typer.colors.GREEN, bold=True))
    with open(filename, 'w') as fp:
        pass
    if open_file:
        open_file_in_editor(filename)

@app.command("open")
def app_open(
        filename: str = typer.Argument("World", help="Filename to open"),
        verbose: bool = typer.Option(True, help="Verbose output")
):
    """
    Open an existing memory.
    """
    if not os.path.exists(filename):
        typer.echo("File does not exist.")
        raise typer.Exit(code=1)
    if verbose:
        typer.echo("Opening "+typer.style(filename, fg=typer.colors.GREEN, bold=True))
    open_file_in_editor(filename)

##### Main #####
if __name__ == "__main__":
    app()