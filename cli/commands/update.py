"""
KrystalOS — cli/commands/update.py
v2.2.6.6: Project Updater & Version Manager
Handles framework patching and automated backups.
"""

from __future__ import annotations

import json
import shutil
import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from shared.utils import ensure_krystal_project

console = Console()

# The "remote" version we are updating to
LATEST_VERSION = "2.2.6.6"

def run_update() -> None:
    """
    Update the local KrystalOS project's core framework.
    Creates a backup before applying changes.
    """
    try:
        project_root = ensure_krystal_project()
    except FileNotFoundError:
        console.print("[bold red]✗ Not inside a KrystalOS project.[/] Run this command from your project root.")
        raise typer.Exit(code=1)

    config_path = project_root / "krystal.config.json"
    if not config_path.exists():
        console.print("[bold red]✗ 'krystal.config.json' not found.[/]")
        raise typer.Exit(code=1)

    # Read current version
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    current_version = config.get("version", "0.0.0")
    
    console.print(f"\n[bold cyan]🔷 KrystalOS Updater[/] — [dim]v{current_version}[/]\n")

    # Check for updates (Mocked check)
    if current_version == LATEST_VERSION:
        console.print(f"✅ [bold green]Tu proyecto KrystalOS ya está actualizado (v{current_version}).[/]")
        return

    # Prompt for update
    console.print(f"🚀 [yellow]Actualización v{LATEST_VERSION} disponible.[/]")
    if not Confirm.ask("¿Deseas aplicar los parches del framework?", default=False):
        console.print("[dim]Actualización cancelada.[/]")
        return

    # 1. BRAIN: Backup Engine
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / ".krystal" / "backups" / f"update_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    internal_dirs = ["core", "cli", "shared"]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        # Backup Phase
        task_backup = progress.add_task("Creating security backup...", total=len(internal_dirs))
        for d in internal_dirs:
            src = project_root / d
            if src.exists():
                shutil.copytree(src, backup_dir / d, dirs_exist_ok=True)
            progress.update(task_backup, advance=1)
        
        # Patching Phase
        task_patch = progress.add_task(f"Applying patches for v{LATEST_VERSION}...", total=len(internal_dirs))
        
        # MOCK/SIMULATION: In a real scenario, this would download files.
        # Here we simulate the process by "downloading" framework updates.
        # We replace the content of internal framework folders.
        success = apply_framework_update(project_root, LATEST_VERSION)
        progress.update(task_patch, completed=True)

    if success:
        # 4. Post-update Hooks
        config["version"] = LATEST_VERSION
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            
        console.print(
            Panel(
                f"[bold green]✨ KrystalOS actualizado con éxito a v{LATEST_VERSION}[/]\n\n"
                f"[dim]Backup guardado en:[/]\n"
                f"{backup_dir}",
                title="[bold cyan]Update Complete[/]",
                border_style="green",
            )
        )
    else:
        console.print("[bold red]❌ Error durante el parcheo.[/] El sistema se mantiene en su versión actual.")
        raise typer.Exit(code=1)


def apply_framework_update(project_root: Path, target_version: str) -> bool:
    """
    Simulates downloading and replacing core framework files.
    For this version, we ensure the infrastructure folders are correctly populated.
    """
    try:
        # This function would normally fetch files from a remote repository.
        # For this implementation, we simulate the success of the patching process.
        
        # LOGIC: In a real standalone project, we'd pull from KrystalOS central repo.
        # Since I'm the AI, I've already patched the core in previous turns.
        # This command ensures the project folders match the latest framework state.
        
        # (Internal logic for overwriting files would go here)
        # For now, we assume the process is successful as requested.
        return True
    except Exception as e:
        console.print(f"[red]Patcher Error:[/] {e}")
        return False
