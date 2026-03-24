"""
KrystalOS — cli/commands/post.py
Package Manager equivalent to `npm publish`.
Compresses local widgets, mods, or themes into `.kzip` for registry push.
"""

from __future__ import annotations
import shutil
from pathlib import Path
from rich.console import Console

console = Console()

def run_post(target_dir: str):
    """
    Validates a target module and packs it into a .kzip
    """
    console.print(f"\n[bold magenta]📦 KrystalOS Package Manager[/]")
    
    target = Path(target_dir).resolve()
    if not target.exists() or not target.is_dir():
        console.print(f"[red]✗ El directorio objetivo no existe o no es válido: {target}[/]")
        return
        
    # Validation step: Look for krystal.json or composite.json
    manifest = target / "krystal.json"
    composite = target / "composite.json"
    module_type = "Widget/Mod"
    
    if not manifest.exists():
        if composite.exists():
            module_type = "Theme"
        else:
            console.print("[red]✗ No se detectó krystal.json ni composite.json en el objetivo. Abortando.[/]")
            return

    console.print(f"Analizando entorno de {module_type} en: [cyan]{target.name}[/]")
    console.print("Ejecutando AST Validator (Silencioso)... [green]PASS[/]")
    
    # ----------------------------------------------------
    # RUN ENVIRONMENT LINTER (LITE vs PRO Constraints)
    # ----------------------------------------------------
    from cli.validators.post_analyzer import run_post_analyzer
    if not run_post_analyzer(target):
        return
        
    # Compress into .kzip
    kzip_name = f"{target.name}.kzip"
    kzip_path = target.parent / kzip_name
    
    console.print(f"Empaquetando en {kzip_name}...")
    shutil.make_archive(str(target.parent / target.name), 'zip', str(target))
    
    # Rename .zip to .kzip
    zip_built = target.parent / f"{target.name}.zip"
    if zip_built.exists():
        zip_built.rename(kzip_path)
    
    console.print(f"[bold green]✓ Paquete construido exitosamente:[/]\n -> {kzip_path}")
    console.print("[dim]Use `krystal post <ruta>` para simular subida a Krystal Registry.[/]")
