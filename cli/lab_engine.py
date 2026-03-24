"""
KrystalOS — cli/lab_engine.py
Sprint v2.2.1 / v2.2.6.4: The Krystal Lab SDK
Generates Zero-Config isolated Vanilla JS environments for testing.
v2.2.6.4: get_krystal_project_root() now accepts strict=False for True Standalone mode.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from rich.console import Console

console = Console()


def get_krystal_project_root(strict: bool = True) -> Path:
    """
    Return the KrystalOS project root.

    Args:
        strict: If False, returns Path.cwd() when no krystal.config.json is found
                instead of raising FileNotFoundError (True Standalone mode).
    """
    from shared.utils import ensure_krystal_project
    return ensure_krystal_project(strict=strict)


def is_standalone(root: Path) -> bool:
    """Return True when the resolved root is just cwd (Standalone mode)."""
    return root == Path.cwd() and not (root / "krystal.config.json").exists()


def deploy_lab(lab_type: str, project_name: str) -> None:
    """
    Scaffolds a specific lab under /labs/[project_name]/ (project mode)
    or ./[project_name]/ (standalone mode).
    Always uses strict=False so it works outside a KrystalOS project.
    """
    root = get_krystal_project_root(strict=False)

    # Standalone: write directly in cwd instead of project /labs/
    if is_standalone(root):
        lab_dir = Path.cwd() / project_name
    else:
        lab_dir = root / "labs" / project_name

    if lab_dir.exists():
        console.print(f"[yellow]El Lab '{project_name}' ya existe. Sobreescribiendo archivos base...[/]")
    else:
        lab_dir.mkdir(parents=True)

    template_dir = root / "templates" / "krystal_lab" / lab_type
    shared_dir   = root / "templates" / "krystal_lab" / "shared"

    # Copy specific template files if they exist locally
    if template_dir.exists():
        for item in template_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, lab_dir / item.name)
    else:
        console.print(f"[dim]Warning: Plantillas nativas de {lab_type} no encontradas. Generando minimal...[/]")

    # Copy shared Performance Profiler + HMR Client
    if shared_dir.exists():
        for shared_file in ["profiler.js", "hmr-client.js"]:
            src = shared_dir / shared_file
            if src.exists():
                shutil.copy2(src, lab_dir / shared_file)

    # Inject hmr-client.js <script> into every HTML file in the lab
    hmr_tag = '<script src="./hmr-client.js"></script>\n'
    for html_file in lab_dir.glob("*.html"):
        content = html_file.read_text(encoding="utf-8")
        if "hmr-client.js" not in content:
            content = content.replace("</body>", f"  {hmr_tag}</body>")
            html_file.write_text(content, encoding="utf-8")

    console.print(f"\n[bold green]🧪 {lab_type.upper()} LAB INICIALIZADO EN:[/] {lab_dir}")
    console.print("[dim]Abre index o dashboard HTML en tu navegador (LiveServer recomendado para fetch).[/]")
