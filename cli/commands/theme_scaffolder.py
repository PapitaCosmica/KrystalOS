"""
KrystalOS — cli/commands/theme_scaffolder.py
Phase 7: Modular Themes Scaffolding
Creates robust templates for CORE_LAYOUT, COLOR_PALETTE, and WIDGET_SKINs.
"""

import os
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

from shared.utils import ensure_krystal_project

console = Console()
theme_app = typer.Typer(help="Theme & Modular UI Scaffolder commands.")

VALID_TYPES = [
    "CORE_LAYOUT",
    "WIDGET_SKIN",
    "COLOR_PALETTE",
    "ANIMATION_PACK",
    "SYSTEM_ASSETS",
    "FULL_OVERHAUL"
]

@theme_app.command("theme")
def make_theme(
    name: str = typer.Argument(None, help="Name of the theme"),
    type: str = typer.Option(None, "--type", "-t", help="Theme category (e.g. CORE_LAYOUT, COLOR_PALETTE)")
):
    """
    Scaffold a new modular theme for the KrystalOS Compositor.
    """
    console.print("\n[bold magenta]🎨 KrystalOS Theme Scaffolder[/]")
    project_root = ensure_krystal_project()

    if not name:
        name = Prompt.ask("[cyan]¿Cómo se llama tu tema modular?[/]", default="mi-tema-genial")

    if not type or type.upper() not in VALID_TYPES:
        console.print("\nTipos de Capas disponibles:")
        for idx, t in enumerate(VALID_TYPES):
            console.print(f"  [yellow]{idx+1}. {t}[/]")
        
        choice = Prompt.ask("[cyan]Elige un tipo de capa (1-6)[/]", default="3")
        try:
            type = VALID_TYPES[int(choice) - 1]
        except (ValueError, IndexError):
            console.print("[red]Opción inválida. Abortando.[/]")
            raise typer.Exit(1)
            
    type = type.upper()

    clean_name = name.lower().replace(" ", "-")
    theme_dir = project_root / "themes" / clean_name

    if theme_dir.exists():
        console.print(f"[red]✗ El directorio ya existe:[/] {theme_dir}")
        raise typer.Exit(1)

    theme_dir.mkdir(parents=True)
    
    # 1. Manifest
    priority = 10
    defines_structure = False
    
    if type == "CORE_LAYOUT":
        priority = 90
        defines_structure = True
    elif type == "FULL_OVERHAUL":
        priority = 100
        defines_structure = True
    elif type == "WIDGET_SKIN":
        priority = 50

    manifest = {
        "name": name,
        "version": "1.0.0",
        "theme_type": type,
        "priority_level": priority,
        "defines_structure": defines_structure
    }
    
    with open(theme_dir / "composite.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

    # 2. Boilerplate CSS
    css_content = f"/* KrystalOS Theme: {name} | Type: {type} */\n\n"
    
    if type == "COLOR_PALETTE":
        css_content += ":root {\n    --kos-primary: #8b5cf6;\n    --kos-bg-main: #0f172a;\n    --kos-text-main: #f8fafc;\n}\n"
    elif type == "CORE_LAYOUT":
        css_content += """body {
    display: grid;
    /* Move taskbar to the left instead of bottom */
    grid-template-areas: 
        "krystal-taskbar krystal-desktop"
        "krystal-taskbar krystal-notifications";
    grid-template-columns: 80px 1fr;
    grid-template-rows: 1fr auto;
}
.krystal-taskbar { flex-direction: column; }
"""
    elif type == "WIDGET_SKIN":
        css_content += """.kos-widget-frame {
    border-radius: 24px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
"""
    else:
        css_content += "/* Escribe tus reglas CSS aquí... */\n"

    with open(theme_dir / "style.css", "w", encoding="utf-8") as f:
        f.write(css_content)

    console.print(f"\n[green]✓ Tema Modular '{name}' andamiado exitosamente.[/]")
    console.print(f"Directorio: [cyan]{theme_dir}[/]")
    console.print(f"Capa Inyectada: [yellow]{type}[/] (Prioridad: {priority})\n")
