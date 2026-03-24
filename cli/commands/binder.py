"""
KrystalOS — cli/commands/binder.py
Phase 7.6: Data Mesh — krystal bind <source> <target>

Validates the Krystal Dictionary (inputs/outputs with kos.* schemas) between
two components, then writes a routing rule to core/config/pipelines.json.

Usage:
    krystal bind <source_path_or_name> <target_path_or_name>
    krystal bind weather-widget map-widget --output temp --input city_temp
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# ─── KOS Namespace validator ───────────────────────────────────────────────────
def _is_valid_kos(schema: str) -> bool:
    """Validates the kos.<domain>.<variable> naming convention."""
    parts = schema.split(".")
    return len(parts) >= 3 and parts[0] == "kos" and all(p.isidentifier() for p in parts[1:])


def _load_manifest(path: Path) -> dict:
    """Load krystal.json from a component directory or full path."""
    if path.is_dir():
        manifest_path = path / "krystal.json"
    else:
        manifest_path = path
    if not manifest_path.exists():
        raise FileNotFoundError(f"krystal.json no encontrado en: {path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_component(name: str, project_root: Path) -> Path:
    """Locate a widget or mod directory by name in the project."""
    candidates = [
        project_root / "widgets" / name,
        project_root / "mods"    / name,
        project_root / "shared"  / "mods" / name,
        Path(name),  # absolute or relative path
    ]
    for c in candidates:
        if c.exists() and (c / "krystal.json").exists():
            return c
    raise FileNotFoundError(
        f"Componente '{name}' no encontrado. "
        "Asegúrate de que exista un krystal.json en su directorio."
    )


def _write_pipeline(
    project_root: Path,
    from_id: str,
    to_id: str,
    output_key: str,
    input_key: str,
    schema: str,
) -> str:
    """Appends a new routing rule to core/config/pipelines.json."""
    pipelines_path = project_root / "core" / "config" / "pipelines.json"
    pipelines_path.parent.mkdir(parents=True, exist_ok=True)

    if pipelines_path.exists():
        with open(pipelines_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"version": "1.0", "pipelines": []}

    pipeline_id = str(uuid.uuid4())[:8]
    rule = {
        "id":         pipeline_id,
        "from":       from_id,
        "to":         to_id,
        "output_key": output_key,
        "input_key":  input_key,
        "schema":     schema,
        "active":     True,
    }
    data["pipelines"].append(rule)

    with open(pipelines_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return pipeline_id


def run_bind(
    source: str,
    target: str,
    output_key: str | None = None,
    input_key:  str | None = None,
) -> None:
    """Core bind logic — validate Dictionary and write pipeline."""

    from shared.utils import ensure_krystal_project
    project_root = ensure_krystal_project()

    console.print(f"\n[bold cyan]🔗 krystal bind:[/] [yellow]{source}[/] → [yellow]{target}[/]\n")

    # ── Load manifests ─────────────────────────────────────────────────────────
    try:
        src_dir  = _find_component(source, project_root)
        tgt_dir  = _find_component(target, project_root)
        src_data = _load_manifest(src_dir)
        tgt_data = _load_manifest(tgt_dir)
    except FileNotFoundError as e:
        console.print(f"[red]✗ {e}[/]")
        raise typer.Exit(1)

    src_name = src_data.get("name", source)
    tgt_name = tgt_data.get("name", target)

    src_outputs = src_data.get("outputs", {})
    tgt_inputs  = tgt_data.get("inputs",  {})

    if not src_outputs:
        console.print(f"[red]✗ '{src_name}' no declara ningún [bold]output[/] en su krystal.json.[/]")
        raise typer.Exit(1)
    if not tgt_inputs:
        console.print(f"[red]✗ '{tgt_name}' no declara ningún [bold]input[/] en su krystal.json.[/]")
        raise typer.Exit(1)

    # ── Auto-detect binding keys if not specified ──────────────────────────────
    if not output_key:
        output_key = next(iter(src_outputs))
    if not input_key:
        input_key = next(iter(tgt_inputs))

    if output_key not in src_outputs:
        console.print(f"[red]✗ Output '[bold]{output_key}[/]' no existe en '{src_name}'.[/]")
        console.print(f"[dim]Outputs disponibles: {', '.join(src_outputs.keys())}[/]")
        raise typer.Exit(1)

    if input_key not in tgt_inputs:
        console.print(f"[red]✗ Input '[bold]{input_key}[/]' no existe en '{tgt_name}'.[/]")
        console.print(f"[dim]Inputs disponibles: {', '.join(tgt_inputs.keys())}[/]")
        raise typer.Exit(1)

    src_schema = src_outputs[output_key].get("schema", "")
    tgt_schema = tgt_inputs[input_key].get("schema",  "")

    # ── Validate kos.* namespace ───────────────────────────────────────────────
    schema_errors = []
    if not _is_valid_kos(src_schema):
        schema_errors.append(f"Output schema inválido: '{src_schema}' (debe ser kos.<domain>.<variable>)")
    if not _is_valid_kos(tgt_schema):
        schema_errors.append(f"Input schema inválido:  '{tgt_schema}' (debe ser kos.<domain>.<variable>)")

    if schema_errors:
        for err in schema_errors:
            console.print(f"[red]✗ {err}[/]")
        console.print(
            "\n[yellow]💡 Ajusta la nomenclatura al estándar [bold]kos.*[/] en tu krystal.json.[/]"
        )
        raise typer.Exit(1)

    # ── Strict schema matching ─────────────────────────────────────────────────
    if src_schema != tgt_schema:
        table = Table(show_header=True, header_style="bold red")
        table.add_column("Campo",  style="dim",    width=16)
        table.add_column("Origen",  style="cyan",   width=25)
        table.add_column("Destino", style="magenta", width=25)
        table.add_row("Componente", src_name,   tgt_name)
        table.add_row("Key",        output_key, input_key)
        table.add_row("Schema",     src_schema, tgt_schema)

        console.print("[bold red]⛔ SCHEMA MISMATCH — Binding rechazado[/]")
        console.print(table)
        console.print(
            Panel(
                f"[yellow]Output:[/] [cyan]{src_schema}[/]\n"
                f"[yellow]Input:[/]  [magenta]{tgt_schema}[/]\n\n"
                "Los schemas deben ser idénticos. Opciones:\n"
                "  [dim]1. Actualiza el schema del krystal.json de uno de los dos componentes.[/]\n"
                "  [dim]2. Instala o crea un [bold]Mod Traductor[/] que convierta entre ambos tipos.[/]\n"
                "     [dim]→ `krystal make:mod --type translator`[/]",
                title="💡 Sugerencia del Krystal Binder",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)

    # ── Write pipeline ─────────────────────────────────────────────────────────
    pipeline_id = _write_pipeline(
        project_root, src_name, tgt_name, output_key, input_key, src_schema
    )

    console.print(
        Panel(
            f"[green]✓ Pipeline creado exitosamente[/]\n\n"
            f"  [dim]ID:[/]          [bold]{pipeline_id}[/]\n"
            f"  [dim]Origen:[/]     [cyan]{src_name}[/] → [bold]{output_key}[/]  ([dim]{src_schema}[/])\n"
            f"  [dim]Destino:[/]    [magenta]{tgt_name}[/] → [bold]{input_key}[/] ([dim]{tgt_schema}[/])\n\n"
            f"  → Guardado en [yellow]core/config/pipelines.json[/]\n"
            f"  → El [bold]IpcRouter[/] cargará esta ruta automáticamente al iniciar.",
            title="🔗 Data Mesh — Binding Completo",
            border_style="green",
        )
    )
