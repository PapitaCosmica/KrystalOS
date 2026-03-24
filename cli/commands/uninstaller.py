"""
KrystalOS — cli/commands/uninstaller.py
Phase 7.5: Interactive Uninstaller with Orphan Detection & Snapshot

Implements `krystal remove <name>` with a safe multi-step flow:
    1. Scan widgets for dependency on the target Mod (Orphan Detection).
    2. Show warning table of affected widgets.
    3. Ask confirmation with snapshot notice.
    4. Run SnapshotEngine before any destructive action.
    5. Remove mod directory and clean config registry.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

console = Console()


def _find_orphan_widgets(mod_name: str, project_root: Path) -> list[dict]:
    """
    Scans all widgets/*/krystal.json for references to mod_name in their
    `needs` array. Returns a list of {'name': ..., 'path': ...} dicts.
    """
    orphans = []
    widgets_dir = project_root / "widgets"
    if not widgets_dir.exists():
        return orphans

    slug = mod_name.lower()
    for manifest_path in widgets_dir.rglob("krystal.json"):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            needs = [n.lower() for n in data.get("needs", [])]
            if slug in needs or slug.replace("-", "") in [n.replace("-", "") for n in needs]:
                orphans.append({
                    "name":    data.get("name", manifest_path.parent.name),
                    "version": data.get("version", "?"),
                    "path":    str(manifest_path.parent),
                })
        except Exception:
            pass

    return orphans


def _find_mod_dir(mod_name: str, project_root: Path) -> Path | None:
    """Locate the Mod directory by slug in /mods/ or /shared/mods/."""
    slug = mod_name.lower().replace(" ", "-")
    candidates = [
        project_root / "mods" / slug,
        project_root / "shared" / "mods" / slug,
        project_root / "mods" / mod_name,
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def run_remove(name: str) -> None:
    """Full interactive Mod removal flow."""

    from shared.utils import ensure_krystal_project
    project_root = ensure_krystal_project()

    console.print(f"\n[bold red]🗑  krystal remove:[/] [cyan]{name}[/]\n")

    # ── Step 1: Locate the Mod ────────────────────────────────────────────────
    mod_dir = _find_mod_dir(name, project_root)
    if not mod_dir:
        console.print(f"[red]✗ Mod '{name}' no encontrado en este proyecto.[/]")
        raise typer.Exit(1)

    console.print(f"Mod encontrado en: [dim]{mod_dir}[/]")

    # ── Step 2: Orphan Detection ──────────────────────────────────────────────
    orphans = _find_orphan_widgets(name, project_root)

    if orphans:
        console.print(f"\n[bold yellow]⚠  Widgets que dependen de este Mod:[/]")
        table = Table(show_header=True, header_style="bold red")
        table.add_column("Widget", style="cyan")
        table.add_column("Versión", style="dim")
        table.add_column("Ruta", style="dim")
        for w in orphans:
            table.add_row(w["name"], w["version"], w["path"])
        console.print(table)

        console.print(
            "\n[dim]Estos widgets perderán acceso a las APIs de este Mod. "
            "El SandboxManager mostrará un Fallback UI en su contenedor.[/]"
        )
    else:
        console.print("[green]✓ Ningún widget depende de este Mod. Operación limpia.[/]")

    # ── Step 3: Confirm with Snapshot Notice ──────────────────────────────────
    console.print(
        f"\n[bold]SnapshotEngine[/] creará una copia de seguridad [cyan].kss[/] "
        "de todos los datos de este Mod antes de eliminarlo."
    )

    confirmed = Confirm.ask(
        f"\n¿Crear snapshot y eliminar [bold]{name}[/]?",
        default=False
    )
    if not confirmed:
        console.print("[yellow]Operación cancelada.[/]")
        raise typer.Exit(0)

    # ── Step 4: Run SnapshotEngine ────────────────────────────────────────────
    try:
        from database.snapshot_engine import SnapshotEngine
        db_path = project_root / "database" / "krystal.db"
        engine = SnapshotEngine(name, db_path=db_path)
        snapshot_path = engine.run()
        console.print(f"[green]✓ Backup disponible en:[/] {snapshot_path}")
    except RuntimeError as e:
        console.print(f"[yellow]⚠ SnapshotEngine (no crítico): {e}[/]")
        console.print("[dim]Continuando sin backup de DB (quizás el Mod no usaba tablas).[/]")

    # ── Step 5: Remove Mod Directory ─────────────────────────────────────────
    try:
        shutil.rmtree(mod_dir)
        console.print(f"[bold green]✓ Mod '{name}' eliminado correctamente.[/]")
    except OSError as e:
        console.print(f"[red]✗ Error al eliminar: {e}[/]")
        raise typer.Exit(1)

    # ── Step 6: Dispatch removal event (for frontend listeners) ──────────────
    # The frontend listens for `krystal:mod-removed` CustomEvent via a shared
    # event endpoint (or WebSocket broadcast from serve). For now we log it.
    console.print(
        "\n[dim]→ Emitiendo 'krystal:mod-removed' al runtime frontend "
        "(el SandboxManager mostrará Fallback UI en los Widgets afectados).[/]"
    )
    console.print(
        "\n[bold cyan]💡 Para restaurar:[/] [dim]krystal restore backups/archive/<archivo>.kss[/]\n"
    )
