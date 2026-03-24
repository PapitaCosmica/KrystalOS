"""
KrystalOS — cli/commands/test_all.py
Phase 7.1: Generates lab-bridge.json to test all Labs at once.
"""

import json
from rich.console import Console
from shared.utils import ensure_krystal_project

console = Console()

def run_test_all():
    """
    Scans the /labs folder and creates lab-bridge.json 
    to interconnect Widget UI, Mod DB, and Theme CSS.
    """
    console.print("\n[bold cyan]🧪 KrystalOS Integration Bridge[/]")
    project_root = ensure_krystal_project()
    labs_dir = project_root / "labs"
    
    if not labs_dir.exists():
        console.print("[red]✗ No hay carpeta /labs activa. Primero crea labs usando --test[/]")
        return
        
    bridge = {
        "active_widgets": [],
        "active_mods": [],
        "active_themes": []
    }
    
    # Simple directory scanning based on manifest existence
    for folder in labs_dir.iterdir():
        if folder.is_dir():
            if (folder / "index.html").exists() and (folder / "krystal-bridge.js").exists():
                bridge["active_widgets"].append(folder.name)
            elif (folder / "mod-dashboard.html").exists():
                bridge["active_mods"].append(folder.name)
            elif (folder / "theme-showcase.html").exists():
                bridge["active_themes"].append(folder.name)

    bridge_file = project_root / "lab-bridge.json"
    with open(bridge_file, "w", encoding="utf-8") as f:
        json.dump(bridge, f, indent=4)
        
    console.print(f"[green]✓ Integración Exitosa. Lab-Bridge generado:[/]")
    console.print(f"Widgets encontrados: {len(bridge['active_widgets'])}")
    console.print(f"Mods encontrados: {len(bridge['active_mods'])}")
    console.print(f"Temas encontrados: {len(bridge['active_themes'])}")
    console.print("\n[dim]Los Labs ahora se comunicarán entre sí. Lanza LiveServer en /labs[/]")
