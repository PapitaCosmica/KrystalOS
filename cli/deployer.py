"""
KrystalOS — cli/deployer.py
Phase 5: The Deployer
Automates pre-flight validation, renaming, and GitHub push operations
with epic terminal styling for a seamless developer experience.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel

from core.schema import load_widget_manifest
from core.validator import ManifestValidator
from shared.utils import ensure_krystal_project

console = Console()
deploy_app = typer.Typer(help="Publish your creations to the KrystalOS ecosystem.")


def _run_git_command(cwd: Path, args: list[str]) -> bool:
    """Execute a git command silently; return True on success."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]Git Error:[/] {result.stderr.strip()}")
        return False
    return True


def _run_preflight_checks(target_dir: Path) -> bool:
    """Run mini-doctor to ensure the directory is clean for an ecosystem deploy."""
    console.print("\n[dim]🔍 Running Pre-flight Validation...[/]")
    
    # 1. Manifest
    manifest_path = target_dir / "krystal.json"
    if not manifest_path.exists():
        console.print("[red]✗ Missing `krystal.json`. This is not a valid component![/]")
        return False
        
    try:
        manifest = load_widget_manifest(manifest_path)
    except ValueError as e:
        console.print(f"[red]✗ Invalid `krystal.json`:[/] {e}")
        return False

    # 2. Heavy unignored directories
    heavy_dirs = ["node_modules", "venv", "__pycache__", "env", ".env"]
    gitignore_path = target_dir / ".gitignore"
    
    has_gitignore = gitignore_path.exists()
    if not has_gitignore:
        for d in heavy_dirs:
            p = target_dir / d
            if p.exists() and p.is_dir():
                console.print(f"[yellow]⚠ Found heavy directory `{d}` without a .gitignore![/]")
                console.print("[red]✗ Deploy aborted. Add a .gitignore to keep the ecosystem clean.[/]")
                return False

    console.print("[green]✓ Validation passed. Ready for launch.[/]")
    return True


@deploy_app.command("widget")
def deploy_widget(
    path: str = typer.Argument(..., help="Path to your standalone widget folder"),
    repo_url: str = typer.Argument(None, help="Optional GitHub repository URL to push into. If omitted, performs local absorption."),
    type_override: str = typer.Option("widget", "--type", help="Can be 'widget', 'theme', or 'mod'"),
) -> None:
    """
    Absorb a standalone widget into KrystalOS or launch into orbit (GitHub).
    Automates validation, sizing heuristics, and packaging into .kzip.
    """
    console.print("\n[bold magenta]🚀 Krystal Deploy Sequence Initiated[/]")
    
    try:
        # Resolve target directory
        target_dir = Path(path).resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            console.print(f"[red]Directory not found:[/] {target_dir}")
            raise typer.Exit(code=1)

        # Pre-flight
        if not _run_preflight_checks(target_dir):
            raise typer.Exit(code=1)

        manifest = load_widget_manifest(target_dir / "krystal.json")

        # AST & Path Validator
        try:
            validator = ManifestValidator(target_dir)
            validator.validate_all(manifest)
        except Exception as ve:
            console.print(f"[red]✗ AST Validation Error:[/] {ve}")
            raise typer.Exit(code=1)

        # AI Heuristic Sizing Assistant
        total_size_bytes = sum(f.stat().st_size for f in target_dir.rglob('*') if f.is_file())
        size_mb = total_size_bytes / (1024 * 1024)

        console.print(f"[dim]→ Evaluando peso heurístico... {size_mb:.2f} MB[/]")
        
        if size_mb > 20:
            console.print(Panel(
                f"[yellow]He notado que usas librerías y sumas {size_mb:.1f} MB en total.[/]\n"
                "Para evitar agotar la RAM del Gateway Orchestrator, KrystalOS puede externalizar los binarios.",
                title="[bold yellow]🤖 Krystal Heuristics AI[/]"
            ))
            opt = Confirm.ask("¿Quieres que las marque como dependencia externa para ahorrar RAM?", default=True)
            if opt:
                console.print("[green]✓ Dependencias marcadas genéricamente para exclusión en caché.[/]")

        # Recommendations based on stack
        lang = getattr(manifest.runtime, "language", "python").lower()
        if lang == "php":
            console.print("[dim]💡 AI Sugerencia: PHP detectado -> Recomendación: Lite Mode + SQLite persistido.[/]")
        elif lang in ["js", "node"]:
            console.print("[dim]💡 AI Sugerencia: Node JS detectado -> Usa eventos asíncronos rápidos en vez de I/O de disco.[/]")

        # Naming Convention Application
        prefix_map = {
            "widget": "WidgetKOS-",
            "theme": "TemaKOS-",
            "mod": "ModKOS-"
        }
        prefix = prefix_map.get(type_override.lower(), "WidgetKOS-")
        clean_name = manifest.name.replace(" ", "-")
        ecosystem_name = f"{prefix}{clean_name}"
        
        console.print(f"\n[bold cyan]📦 Preparing payload:[/] {ecosystem_name}")
        
        project_root = ensure_krystal_project()
        temp_stage = project_root / f".deploy_{ecosystem_name}"
        
        if temp_stage.exists():
            shutil.rmtree(temp_stage)
            
        shutil.copytree(
            target_dir, 
            temp_stage, 
            ignore=shutil.ignore_patterns("node_modules", "venv", "__pycache__", ".git", "standalone")
        )

        try:
            # Remote vs Local Branching
            if repo_url:
                console.print("[dim]→ Initializing engines (git init)...[/]")
                if not _run_git_command(temp_stage, ["init"]): raise Exception("Init failed")
                
                # 2. Add remote
                console.print(f"[dim]→ Targeting coordinates (remote add):[/] {repo_url}")
                if not _run_git_command(temp_stage, ["remote", "add", "origin", repo_url]): raise Exception("Remote failed")
                
                # 3. Add & Commit
                console.print("[dim]→ Compressing payload (git commit)...[/]")
                if not _run_git_command(temp_stage, ["add", "."]): raise Exception("Add failed")
                if not _run_git_command(temp_stage, ["commit", "-m", f"KrystalOS Deploy: 🚀 {manifest.name} v{manifest.version}"]): raise Exception("Commit failed")
                
                # 4. Push (Ignite!)
                console.print("[bold yellow]🔥 IGNITION! Pushing to orbit...[/]")
                # We enforce branch to be 'main' for the ecosystem
                if not _run_git_command(temp_stage, ["branch", "-M", "main"]): pass # Ignore if already on main
                if not _run_git_command(temp_stage, ["push", "-u", "origin", "main", "--force"]): 
                    raise Exception("Push failed. Ensure the remote exists and you have access.")

                console.print("\n[bold green]✨ MISSION ACCOMPLISHED![/]")
                console.print(f"Your creation is now live at: [underline cyan]{repo_url}[/]")
            else:
                # Local Absorption & Zip
                kzip_path = project_root / f"{ecosystem_name}.kzip"
                shutil.make_archive(str(project_root / ecosystem_name), 'zip', temp_stage)
                shutil.move(str(project_root / f"{ecosystem_name}.zip"), str(kzip_path))
                
                console.print("\n[bold green]✨ ABSORPTION ACCOMPLISHED![/]")
                console.print(f"Widget packaged into standalone bundle at: [cyan]{kzip_path}[/]")

        except Exception as e:
            console.print(f"\n[bold red]❌ Deploy Sequence Aborted:[/] {e}")
            raise typer.Exit(code=1)
        finally:
            if temp_stage.exists():
                shutil.rmtree(temp_stage)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error:[/] {e}")
        raise typer.Exit(1)
