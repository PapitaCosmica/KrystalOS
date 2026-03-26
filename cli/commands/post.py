"""
KrystalOS — cli/commands/post.py
v2.2.6.7: Build Engine & Git Auto-Push
Compresses local modules and applies sandboxing before deployment.
"""

from __future__ import annotations
import zipfile
import re
import json
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

# Directories never included in the distributable .kzip
_EXCLUDED_DIRS: set[str] = {"lab-env"}


def compile_widget(target: Path, name: str) -> bool:
    """
    KrystalOS Build Engine Phase:
    - CSS Scoping: Prefixes all rules with #kos-widget-[name]
    - JS Sandboxing: Wraps <script> in IIFE
    - Output to /dist/bundle.html
    """
    source_file = target / "ui.html"
    if not source_file.exists():
        source_file = target / "index.html"
    
    if not source_file.exists():
        console.print("[yellow]⚠ No se encontró ui.html o index.html. Saltando paso de compilación.[/]")
        return False

    dist_dir = target / "dist"
    dist_dir.mkdir(exist_ok=True)
    
    content = source_file.read_text(encoding="utf-8")
    widget_id = f"kos-widget-{name}"

    # 1. CSS Scoping
    def prefix_css(match):
        css = match.group(1)
        # Sencillez: buscamos selectores que no empiecen por @ y les ponemos el prefijo
        scoped = re.sub(r'([^{};]+)({)', rf'#{widget_id} \1 \2', css)
        return f"<style>\n{scoped}\n</style>"

    content = re.sub(r'<style>(.*?)</style>', prefix_css, content, flags=re.DOTALL)

    # 2. JS Sandboxing (IIFE)
    def wrap_js(match):
        js = match.group(1)
        return f"<script>\n(() => {{\n{js}\n}})();\n</script>"

    content = re.sub(r'<script>(.*?)</script>', wrap_js, content, flags=re.DOTALL)

    # 3. Save Bundle
    bundle_path = dist_dir / "bundle.html"
    bundle_path.write_text(content, encoding="utf-8")
    
    # 4. Update krystal.json
    manifest_path = target / "krystal.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data["main"] = "dist/bundle.html"
            
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[yellow]⚠ Error actualizando krystal.json: {e}[/]")

    return True


def run_post(target_dir: str, github_url: str | None = None) -> None:
    """
    Validates a target module, compiles it for production (Sandboxing),
    packs it into a .kzip, and optionally pushes to GitHub.
    """
    console.print(f"\n[bold magenta]📦 KrystalOS Build & Publish Engine[/]")

    target = Path(target_dir).resolve()
    if not target.exists() or not target.is_dir():
        console.print(f"[red]✗ El directorio objetivo no existe o no es válido: {target}[/]")
        return

    # Validation
    manifest = target / "krystal.json"
    composite = target / "composite.json"
    module_name = target.name
    
    if not manifest.exists() and not composite.exists():
        console.print("[red]✗ No se detectó krystal.json ni composite.json en el objetivo.[/]")
        return

    # --- PHASE 1 & 2: Build & Sandbox ---
    console.print(f"🛠  Compilando [cyan]{module_name}[/] para producción...")
    if compile_widget(target, module_name):
        console.print("[bold green]✓ Build successful:[/] [dim]Sandbox applied & /dist/ generado.[/]")
    
    # --- PHASE: Analysis ---
    from cli.validators.post_analyzer import run_post_analyzer
    if not run_post_analyzer(target):
        return

    # --- PHASE: Compression ---
    kzip_name = f"{module_name}.kzip"
    kzip_path = target.parent / kzip_name

    console.print(f"📦 Empaquetando en [cyan]{kzip_name}[/]...")
    
    files_included = 0
    files_skipped = 0

    with zipfile.ZipFile(kzip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in target.rglob("*"):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(target)
            if any(part in _EXCLUDED_DIRS for part in rel.parts):
                files_skipped += 1
                continue
            zf.write(file_path, arcname=str(rel))
            files_included += 1

    console.print(
        f"[bold green]✓ Paquete construido exitosamente:[/]\n"
        f"  [dim]→[/] {kzip_path}\n"
        f"  [dim]Archivos incluidos:[/] [cyan]{files_included}[/] ([yellow]{files_skipped}[/] excluidos)"
    )

    # --- PHASE 3: Git Auto-Deploy ---
    if github_url or (target / ".git").exists():
        console.print(f"\n[bold cyan]🚀 Git Auto-Deploy Engine...[/]")
        
        target_kzip = target / kzip_name
        kzip_path.rename(target_kzip)

        try:
            # 1. .gitignore
            gitignore_path = target / ".gitignore"
            if not gitignore_path.exists():
                gitignore_path.write_text("lab-env/\n.krystal/\n__pycache__/\n*.pyc\n", encoding="utf-8")

            # 2. Git Init
            res_git = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=target, capture_output=True)
            if res_git.returncode != 0:
                subprocess.run(["git", "init"], cwd=target, check=True, stdout=subprocess.DEVNULL)
            
            # 3. Remote
            if github_url:
                res_rem = subprocess.run(["git", "remote", "get-url", "origin"], cwd=target, capture_output=True, text=True)
                if res_rem.returncode != 0:
                    subprocess.run(["git", "remote", "add", "origin", github_url], cwd=target, check=True)
                else:
                    subprocess.run(["git", "remote", "set-url", "origin", github_url], cwd=target, check=True)

            # 4. Commit & Push
            subprocess.run(["git", "add", "."], cwd=target, check=True)
            subprocess.run(["git", "commit", "-m", "🚀 KrystalOS Auto-Build: Compilado y empaquetado para producción"], 
                           cwd=target, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "branch", "-M", "main"], cwd=target, check=True)
            
            if github_url:
                console.print("[bold cyan]Subiendo a GitHub...[/]")
                subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=target, check=True)
                console.print(f"[bold green]✓ Publicado satisfactoriamente en GitHub.[/]")
            else:
                console.print("[bold green]✓ Git commit local completado exitosamente.[/]")
            
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]✗ Error en el flujo Git:[/] {e}")
        finally:
            if target_kzip.exists():
                target_kzip.rename(kzip_path)
    else:
        console.print("[dim]Sin repositorio Git detectado. Use krystal post <ruta> [url] para desplegar.[/]")
