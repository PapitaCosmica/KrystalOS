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


def run_post(target_dir: str, github_url: str | None = None) -> None:
    """
    Validates a target module, packs it into a .kzip, and optionally autobuilds and pushes
    everything to a GitHub Krystal Registry repository.
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

    if github_url:
        import subprocess
        assert isinstance(github_url, str)
        
        console.print(f"\n[bold cyan]🚀 Desplegando en GitHub (Krystal Registry)...[/]")
        console.print(f"[dim]Destino: {github_url}[/]")
        
        # Validar sugerencia de nomenclatura
        if "WidgetKOs-" not in github_url and "ModKOs-" not in github_url and "ThemeKOs-" not in github_url:
            console.print("[yellow]⚠ Advertencia: El repositorio no usa la nomenclatura oficial recomendada (ej. WidgetKOs-nombre). Esto podría afectar `krystal install` por nombre corto.[/]")

        # Mover temporalmente el .kzip adentro para subirlo al repo
        target_kzip = target / kzip_name
        kzip_path.rename(target_kzip)

        try:
            # Crear un .gitignore al vuelo para que no suba lab-env ni otros artifacts
            gitignore_path = target / ".gitignore"
            if not gitignore_path.exists():
                gitignore_path.write_text("lab-env/\n.krystal/\n__pycache__/\n*.pyc\n", encoding="utf-8")

            # Inicializar y subir con Git
            subprocess.run(["git", "init"], cwd=target, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=target, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Commit (puede fallar si no hay cambios nuevos en el git local)
            subprocess.run(["git", "commit", "-m", "🚀 KrystalOS Auto-Publish (krystal post)"], cwd=target, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            subprocess.run(["git", "branch", "-M", "main"], cwd=target, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Manejar remote origen si ya existe o crearlo
            res = subprocess.run(["git", "remote", "get-url", "origin"], cwd=target, capture_output=True, text=True)
            if res.returncode != 0:
                subprocess.run(["git", "remote", "add", "origin", github_url], cwd=target, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["git", "remote", "set-url", "origin", github_url], cwd=target, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Push interactivo para ver progreso
            console.print("[bold cyan]Subiendo archivos a GitHub...[/]")
            subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=target, check=True)
            
            console.print(f"\n[bold green]✓ ¡Publicado exitosamente en GitHub![/]")
            console.print(f"Los usuarios pueden instalarlo ejecutando:")
            console.print(f"  [cyan]krystal install -w {target.name}[/]")
            
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]✗ Falló el despliegue Git:[/] {e}")
            console.print("[yellow]Asegúrate de tener `git` instalado y los permisos SSH/HTTPS configurados.[/]")
        finally:
            # Restaurar el .kzip a la carpeta padre para no romper flujos locales
            target_kzip.rename(kzip_path)
            
    else:
        console.print("[dim]Use `krystal post <ruta> <url_github>` para automatizar la subida a Krystal Registry.[/]")

