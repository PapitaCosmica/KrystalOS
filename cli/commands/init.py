"""
KrystalOS — cli/commands/init.py
`krystal init <name>` — scaffold a new KrystalOS project directory.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.prompt import Prompt

console = Console()

# Default top-level directories created for every new project
_PROJECT_DIRS = ["cli", "core", "widgets", "shared", ".krystal"]

# Default global framework config
_DEFAULT_CONFIG = {
    "krystalOS": True,
    "version": "0.1.0",
    "default_mode": "native",
    "event_bus": {
        "host": "localhost",
        "port": 4242,
    },
    "gateway": {
        "base_port": 9000,
    },
}


def init_project(name: str) -> None:
    """
    Create a new KrystalOS project directory tree.

    Raises:
        typer.Exit: on conflict or permission errors.
    """
    root = Path.cwd() / name

    # Guard against overwriting an existing project
    if root.exists():
        console.print(
            f"[bold red]✗[/] Directory [yellow]{root}[/] already exists.",
            highlight=False,
        )
        raise typer.Exit(code=1)

    console.print(f"\n[bold cyan]🔷 KrystalOS[/] — Initialising project [bold]{name}[/]\n")

    # Build directory tree
    tree = Tree(f"[bold green]{name}/[/]")
    root.mkdir(parents=True)

    for d in _PROJECT_DIRS:
        (root / d).mkdir()
        label = f"[dim cyan]{d}/[/]" if d.startswith(".") else f"[cyan]{d}/[/]"
        tree.add(label)

    # Environment Consultant
    console.print("\n[yellow]¿Este proyecto es para un entorno LITE (Recursos limitados, SQLite) o PRO (Alto rendimiento, PostgreSQL/Docker)?[/]")
    env_choices = ["LITE", "PRO"]
    env_ans = Prompt.ask("[bold cyan]Target Environment[/]", choices=env_choices, default="PRO")

    # krystal.config.json
    config_path = root / "krystal.config.json"
    config_data = {**_DEFAULT_CONFIG, "name": name, "target_env": env_ans}
    config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
    tree.add("[bold yellow]krystal.config.json[/]")

    # .krystal/state.json (Phase 2/3 runtime state)
    (root / ".krystal" / "state.json").write_text(
        json.dumps({"active_ports": {}, "active_widgets": []}, indent=2),
        encoding="utf-8",
    )

    console.print(tree)
    console.print(
        Panel(
            f"[bold green]✓[/] Project [bold]{name}[/] created at [dim]{root}[/]\n"
            f"  [cyan]Target Env:[/] [bold]{env_ans}[/]\n\n"
            f"  [dim]Next steps:[/]\n"
            f"  [bold]cd {name}[/]\n"
            f"  [bold]krystal doctor[/] [dim](Recomendado para verificar dependencias {env_ans})[/]\n"
            f"  [bold]krystal make:widget[/]",
            title="[bold cyan]🔷 Project Ready[/]",
            border_style="cyan",
        )
    )

def set_env(target: str) -> None:
    """Forces the workspace environment mode."""
    target = target.upper()
    if target not in ["LITE", "PRO"]:
        console.print("[red]✗ El entorno debe ser 'LITE' o 'PRO'[/]")
        raise typer.Exit(1)
        
    try:
        from shared.utils import ensure_krystal_project
        root = ensure_krystal_project()
        config_path = root / "krystal.config.json"
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        data["target_env"] = target
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        console.print(f"[bold green]✓ Workspace configurado forzosamente para:[/] [cyan]{target}[/]")
    except Exception as e:
        console.print(f"[red]✗ Error al cambiar entorno:[/] {e}")
        raise typer.Exit(1)

