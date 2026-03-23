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

    # krystal.config.json
    config_path = root / "krystal.config.json"
    config_data = {**_DEFAULT_CONFIG, "name": name}
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
            f"[bold green]✓[/] Project [bold]{name}[/] created at [dim]{root}[/]\n\n"
            f"  [dim]Next steps:[/]\n"
            f"  [bold]cd {name}[/]\n"
            f"  [bold]krystal make:widget[/]\n"
            f"  [bold]krystal doctor[/]",
            title="[bold cyan]🔷 Project Ready[/]",
            border_style="cyan",
        )
    )
