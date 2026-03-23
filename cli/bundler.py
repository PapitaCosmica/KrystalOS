"""
KrystalOS — cli/bundler.py
Phase 4: The Bundler
Packages a KrystalOS project into a portable ZIP archive, generating a
cryptographic manifest for integrity checking.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from shared.utils import ensure_krystal_project

console = Console()
bundle_app = typer.Typer(help="Package and deploy KrystalOS applications.")

def calculate_hash(filepath: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_manifest(root: Path) -> dict:
    """Walk critical directories and generate a secure manifest."""
    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "files": {}
    }
    
    # Directories we care about for integrity
    critical_dirs = ["core", "widgets", "shared", "static", "bin"]
    
    for dname in critical_dirs:
        dir_path = root / dname
        if not dir_path.exists():
            continue
            
        for filepath in dir_path.rglob("*"):
            if filepath.is_file():
                rel_path = filepath.relative_to(root).as_posix()
                manifest["files"][rel_path] = calculate_hash(filepath)
                
    return manifest

@bundle_app.command("create")
def bundle_create(
    output_name: str = typer.Option("krystal_app.zip", "--out", "-o", help="Output archive name."),
) -> None:
    """
    Compress the current KrystalOS Orchestrator project into a standalone portable bundle.
    """
    try:
        project_root = ensure_krystal_project()
    except FileNotFoundError:
        console.print("[red]Not inside a KrystalOS project. Run `krystal init` first.[/]")
        raise typer.Exit(code=1)

    console.print(f"\n[cyan]📦 Assembling KrystalOS Bundle: {output_name}[/]")

    # 1. Generate Manifest
    console.print("[dim]Generating cryptographic manifest...[/]")
    krystal_dir = project_root / ".krystal"
    manifest_data = generate_manifest(project_root)
    
    manifest_path = krystal_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
    
    # 2. Package into ZIP
    # We will copy allowed root files and directories to a temp directory, then zip it.
    console.print("[dim]Compiling project files...[/]")
    
    exclude_dirs = {".git", ".krystal", "__pycache__", "venv", ".idea", ".vscode"}
    exclude_files = {output_name, "pids.json", "krystal.db", "krystal.db-shm", "krystal.db-wal"}
    
    bundle_name = output_name[:-4] if output_name.endswith(".zip") else output_name
    temp_build_dir = project_root / f".build_{bundle_name}"
    
    if temp_build_dir.exists():
        shutil.rmtree(temp_build_dir)
    temp_build_dir.mkdir()
    
    try:
        for item in project_root.iterdir():
            if item.name in exclude_dirs or item.name in exclude_files:
                continue
            
            dest = temp_build_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns("*.pyc", "__pycache__", ".DS_Store"))
            else:
                shutil.copy2(item, dest)
                
        # Copy the .krystal folder but exclude temp DB runtime files
        krystal_dest = temp_build_dir / ".krystal"
        shutil.copytree(krystal_dir, krystal_dest, ignore=shutil.ignore_patterns("pids.json", "*.db*"))

        # Create zip
        console.print("[dim]Zipping archive...[/]")
        shutil.make_archive(
            base_name=str(project_root / bundle_name),
            format="zip",
            root_dir=temp_build_dir
        )
        console.print(f"[bold green]✓ Bundle finalized successfully: {bundle_name}.zip[/]\n")
        
    except Exception as e:
        console.print(f"[bold red]❌ Bundling failed:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        # Cleanup
        if temp_build_dir.exists():
            shutil.rmtree(temp_build_dir)
