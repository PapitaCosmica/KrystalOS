"""
KrystalOS — cli/commands/mod_scaffolder.py
Generates a Backend Mod or its isolated Lab testing environment.
"""

import os
import typer
from rich.console import Console
from rich.prompt import Prompt

from shared.utils import ensure_krystal_project
from cli.lab_engine import deploy_lab

console = Console()

def make_mod(
    name: str = typer.Argument(None, help="Name of the Mod"),
    test: bool = typer.Option(False, "--test", help="Generates an isolated Sandbox Lab for this Mod")
):
    """
    Scaffold a new backend Mod.
    If --test is passed, creates a Zero-Config UI dashboard (Swagger style) for testing.
    """
    console.print("\n[bold magenta]🧩 KrystalOS Mod Scaffolder[/]")
    project_root = ensure_krystal_project()

    if not name:
        name = Prompt.ask("[cyan]¿Cómo se llama tu Mod?[/]", default="MOD-USERS")
        
    clean_name = name.upper().replace(" ", "-")

    if test:
        # Generate the Testing Lab in /labs/[name]
        deploy_lab("mod", clean_name)
        return

    # Standard Generation
    mod_dir = project_root / "mods" / clean_name
    if mod_dir.exists():
        console.print(f"[red]✗ El Mod ya existe:[/] {mod_dir}")
        raise typer.Exit(1)

    console.print("\n[yellow]¿Cuál es el alcance y nivel de acceso de este Mod?[/]")
    scope_options = [
        "Core Modification (Acceso profundo, altera Kernel o DB)",
        "Feature Integration (APIs de terceros, OCR, Clima)",
        "Background Daemon/Service (Procesos invisibles, indexadores)"
    ]
    for idx, opt in enumerate(scope_options):
        console.print(f"  [cyan]{idx+1}. {opt}[/]")
    
    scope_choice = Prompt.ask("[yellow]Elige el alcance (1-3)[/]", default="2")
    
    permissions = []
    scope_id = "FEATURE"
    
    if scope_choice == "1":
        scope_id = "CORE_MOD"
        permissions = ["DB_WRITE", "DB_READ", "KERNEL_HOOK", "FILE_SYSTEM"]
    elif scope_choice == "3":
        scope_id = "DAEMON"
        permissions = ["BACKGROUND_WORKER", "NETWORK_SOCKET"]
    else:
        permissions = ["NETWORK_REST", "DB_READ_ONLY"]

    # Target Environment
    console.print("\n[yellow]¿Target Mode?[/] (LITE bloquea procesos intensivos)")
    target_env = Prompt.ask("[bold]Target Environment[/]", choices=["LITE", "PRO"], default="LITE")

    mod_dir.mkdir(parents=True)
    
    import json
    manifest = {
        "name": clean_name,
        "version": "1.0.0",
        "author": "krystal-dev",
        "target": target_env,
        "scope": scope_id,
        "permissions": permissions,
        "shared_tools": [],
        "timeout_idle": "5m",
        "entrypoint": "main.py"
    }
    
    with open(mod_dir / "krystal.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    # Generate basic boilerplate
    with open(mod_dir / "main.py", "w", encoding="utf-8") as f:
        f.write("def run():\n    pass\n")

    console.print(f"\n[green]✓ Mod {clean_name} creado exitosamente.[/]")
    console.print(f"Scope: [magenta]{scope_id}[/]")
    console.print(f"Persmisos Asignados: [yellow]{permissions}[/]")
