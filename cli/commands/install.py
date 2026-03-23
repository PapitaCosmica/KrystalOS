"""
KrystalOS — cli/commands/install.py
Phase 5: Install & Update
Handles secure downloading from GitHub and subsequent updates.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.market import install_from_git, update_git_repo
from shared.utils import ensure_krystal_project

console = Console()

def install_widget(url: str) -> None:
    """
    Install a KrystalOS widget, theme, or mod from a GitHub repository.
    Auto-scans the repository for potential security risks.
    """
    try:
        project_root = ensure_krystal_project()
    except FileNotFoundError:
        console.print("[red]Not inside a KrystalOS project. Run `krystal init` first.[/]")
        raise typer.Exit(code=1)

    console.print(f"\n[cyan]📦 Krystal Market Install:[/] {url}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Downloading and securing codebase...", total=None)
        success, message = install_from_git(url)
        progress.update(task, completed=True)

    if success:
        console.print(f"\n[bold green]✓ Installation Complete![/]")
        if "[yellow]⚠ Sandbox" in message:
            console.print(Panel(message, title="Security Notice", border_style="yellow"))
        else:
            console.print(f"Widget successfully isolated at: [dim]{message}[/]")
    else:
        console.print(f"\n[bold red]❌ Installation Failed:[/] {message}")
        raise typer.Exit(code=1)


def update_widget(widget_name: str) -> None:
    """
    Updates an installed widget by fetching the latest code from its repository.
    """
    try:
        project_root = ensure_krystal_project()
    except FileNotFoundError:
        console.print("[red]Not inside a KrystalOS project. Run `krystal init` first.[/]")
        raise typer.Exit(code=1)

    widget_dir = project_root / "widgets" / widget_name
    if not widget_dir.exists():
        console.print(f"[red]Widget '{widget_name}' is not installed.[/]")
        raise typer.Exit(code=1)

    console.print(f"\n[cyan]🔄 Updating '{widget_name}'...[/]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Pulling latest telemetry from GitHub...", total=None)
        success, message = update_git_repo(widget_dir)
        progress.update(task, completed=True)

    if success:
        console.print(f"[bold green]✓ Update Successful![/]")
        console.print(f"[dim]{message}[/]")
    else:
        console.print(f"[bold red]❌ Update Failed:[/] {message}")
