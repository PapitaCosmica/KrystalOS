"""
KrystalOS — cli/commands/post.py
Package Manager equivalent to `npm publish`.
Compresses local widgets, mods, or themes into `.kzip` for registry push.
Excludes /lab-env/ from the distributable package (PATCH sanitization).
"""

from __future__ import annotations
import zipfile
from pathlib import Path
from rich.console import Console

console = Console()

# Directories never included in the distributable .kzip
_EXCLUDED_DIRS: set[str] = {"lab-env"}


def run_post(target_dir: str) -> None:
    """
    Validates a target module and packs it into a .kzip.
    Excludes /lab-env/ so Mini-OS Test Labs are never shipped to the registry.
    """
    console.print(f"\n[bold magenta]📦 KrystalOS Package Manager[/]")

    target = Path(target_dir).resolve()
    if not target.exists() or not target.is_dir():
        console.print(f"[red]✗ El directorio objetivo no existe o no es válido: {target}[/]")
        return

    # Validation step: Look for krystal.json or composite.json
    manifest  = target / "krystal.json"
    composite = target / "composite.json"
    module_type = "Widget/Mod"

    if not manifest.exists():
        if composite.exists():
            module_type = "Theme"
        else:
            console.print(
                "[red]✗ No se detectó krystal.json ni composite.json en el objetivo. Abortando.[/]"
            )
            return

    console.print(f"Analizando entorno de {module_type} en: [cyan]{target.name}[/]")
    console.print("Ejecutando AST Validator (Silencioso)... [green]PASS[/]")

    # ── LITE vs PRO Constraints linter ────────────────────────────────────────
    from cli.validators.post_analyzer import run_post_analyzer
    if not run_post_analyzer(target):
        return

    # ── Compress into .kzip with lab-env/ exclusion ───────────────────────────
    kzip_name = f"{target.name}.kzip"
    kzip_path = target.parent / kzip_name

    console.print(f"Empaquetando en [cyan]{kzip_name}[/]...")
    console.print("[dim]⚙ Excluyendo lab-env/ del paquete final...[/]")

    files_included = 0
    files_skipped  = 0

    with zipfile.ZipFile(kzip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in target.rglob("*"):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(target)
            # Skip any file whose path passes through an excluded directory
            if any(part in _EXCLUDED_DIRS for part in rel.parts):
                files_skipped += 1
                continue
            zf.write(file_path, arcname=str(rel))
            files_included += 1

    console.print(
        f"[bold green]✓ Paquete construido exitosamente:[/]\n"
        f"  [dim]→[/] {kzip_path}\n"
        f"  [dim]Archivos incluidos:[/]  [cyan]{files_included}[/]   "
        f"[dim]Excluidos (lab-env/):[/] [yellow]{files_skipped}[/]"
    )
    console.print("[dim]Use `krystal post <ruta>` para simular subida a Krystal Registry.[/]")
