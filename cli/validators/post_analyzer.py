"""
KrystalOS — cli/validators/post_analyzer.py
Analyzer for `krystal post` preventing LITE environments from exceeding constraints.
"""

from __future__ import annotations
import json
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
import typer

console = Console()

def run_post_analyzer(target_dir: Path) -> bool:
    """
    Evaluates performance and sizes before packaging.
    Warns the developer if target="LITE" limits are exceeded.
    Returns True if safe to continue.
    """
    manifest_path = target_dir / "krystal.json"
    if not manifest_path.exists():
        return True  # Skip if Theme or no manifest
        
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception:
        return True
        
    target_env = manifest.get("target", "PRO").upper()
    
    if target_env == "LITE":
        console.print("[dim]🔍 Target analizado: LITE. Validando heurísticas de peso y rendimiento...[/]")
        
        # 1. Size constraints
        total_size_bytes = sum(f.stat().st_size for f in target_dir.rglob('*') if f.is_file())
        size_mb = total_size_bytes / (1024 * 1024)
        
        warnings = []
        if size_mb > 10.0:
            warnings.append(f"El empaquetado ({size_mb:.2f} MB) supera el umbral LITE de 10.0 MB.")
            
        # 2. Network Analysis (Looking for raw WebSockets instead of EventBus)
        has_ws = False
        for js_file in target_dir.rglob("*.js"):
            if "node_modules" in js_file.parts: continue
            content = js_file.read_text(encoding="utf-8", errors="ignore")
            if "new WebSocket" in content or "io(" in content:
                has_ws = True
                break
                
        if has_ws:
            warnings.append("Detectado uso de WebSockets en crudo (Incompatible con políticas LITE). Usa EventBus.")
            
        if warnings:
            console.print(f"\n[bold red]⚠️  ATENCIÓN: EL COMPONENTE ROMPE LOS LÍMITES DEL MODO LITE[/]")
            for w in warnings:
                console.print(f"  [red]- {w}[/]")
                
            ans = Confirm.ask("\n¿Deseas empaquetarlo (publicarlo) de todos modos ignorando las alertas de LITE?", default=False)
            if not ans:
                console.print("[yellow]Operación abortada por el Linter LITE.[/]")
                return False
        else:
            console.print("[green]✓ Auditoría Heurística de Entorno LITE superada con honores.[/]")
            
    return True
