"""
KrystalOS — cli/lab_engine.py
Sprint v2.2.1: The Krystal Lab SDK
Generates Zero-Config isolated Vanilla JS environments for testing.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from rich.console import Console

console = Console()

def get_krystal_project_root() -> Path:
    from shared.utils import ensure_krystal_project
    return ensure_krystal_project()

def deploy_lab(lab_type: str, project_name: str) -> None:
    """
    Scaffolds a specific lab under /labs/[project_name]/
    """
    root = get_krystal_project_root()
    lab_dir = root / "labs" / project_name
    
    if lab_dir.exists():
        console.print(f"[yellow]El Lab '{project_name}' ya existe. Sobreescribiendo archivos base...[/]")
    else:
        lab_dir.mkdir(parents=True)
        
    template_dir = root / "templates" / "krystal_lab" / lab_type
    shared_dir = root / "templates" / "krystal_lab" / "shared"
    
    # We copy the specific template files if they exist locally
    if template_dir.exists():
        for item in template_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, lab_dir / item.name)
    else:
        # Fallback if templates are missing from OS
        console.print(f"[dim]Warning: Plantillas nativas de {lab_type} no encontradas. Generando minimal...[/]")
        
    # Copy shared Performance Profiler
    if shared_dir.exists():
        profiler = shared_dir / "profiler.js"
        if profiler.exists():
            shutil.copy2(profiler, lab_dir / "profiler.js")

    console.print(f"\n[bold green]🧪 {lab_type.upper()} LAB INICIALIZADO EN:[/] {lab_dir}")
    console.print(f"[dim]Abre index o dashboard HTML en tu navegador (LiveServer recomendado para fetch).[/]")
