"""
KrystalOS — core/market.py
Phase 5: The Market
Handles fetching, updating, and statically scanning third-party widgets
for obvious security vulnerabilities before activation.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from shared.utils import ensure_krystal_project

logger = logging.getLogger("krystal.market")
console = Console()

# Basic static analysis regexes to catch the most obvious malicious vectors
# Note: This is a Sandbox Heuristic, NOT a watertight VM isolation.
DANGEROUS_PATTERNS = {
    "python": [
        (r"os\.system\s*\(", "os.system() call detected"),
        (r"subprocess\.", "subprocess access detected"),
        (r"eval\s*\(", "eval() call detected"),
        (r"exec\s*\(", "exec() call detected"),
        (r"__import__\s*\(", "dynamic __import__ detected"),
    ],
    "javascript": [
        (r"eval\s*\(", "eval() call detected"),
        (r"require\s*\(\s*['\"]child_process['\"]\s*\)", "child_process execution detected"),
        (r"fs\.rmSync", "fs.rmSync deletion detected"),
    ],
    "php": [
        (r"exec\s*\(", "exec() shell execution detected"),
        (r"shell_exec\s*\(", "shell_exec() detected"),
        (r"system\s*\(", "system() detected"),
        (r"eval\s*\(", "PHP eval() detected"),
    ]
}

def scan_sandbox(widget_dir: Path) -> list[str]:
    """
    Statistically analyze source code files in a directory 
    for dangerous patterns depending on file extension.
    Returns a list of warning messages.
    """
    warnings = []
    
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".php": "php"
    }

    for filepath in widget_dir.rglob("*"):
        if filepath.is_dir() or filepath.suffix not in ext_map:
            continue
            
        lang = ext_map[filepath.suffix]
        patterns = DANGEROUS_PATTERNS.get(lang, [])
        
        try:
            content = filepath.read_text("utf-8")
            for pattern, description in patterns:
                if re.search(pattern, content):
                    rel_path = filepath.relative_to(widget_dir).as_posix()
                    warnings.append(f"{description} in {rel_path}")
        except Exception as e:
            logger.error("Could not scan %s: %s", filepath, e)

    return warnings


def install_from_git(repo_url: str, dest_name: str | None = None) -> tuple[bool, str]:
    """
    Clone a repository from GitHub into the KrystalOS widgets directory.
    Returns (Success, PathOrErrorMsg).
    """
    try:
        project_root = ensure_krystal_project()
    except FileNotFoundError:
        return False, "Not inside a KrystalOS project."

    widgets_dir = project_root / "widgets"
    widgets_dir.mkdir(exist_ok=True)
    
    # --- URL Normalization (Short Name -> GitHub URL) ---
    original_input = repo_url
    if not repo_url.startswith("http") and not repo_url.startswith("git@"):
        # Auto-expand to official PapitaCosmica registry if only a short name is given
        repo_url = f"https://github.com/PapitaCosmica/WidgetKOs-{repo_url}.git"
    
    # --- Extract clean folder name ---
    if not dest_name:
        # e.g https://github.com/.../WidgetKOs-mi-widget.git -> WidgetKOs-mi-widget
        raw_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        # Remove ecosystem prefixes for clean local folder
        dest_name = raw_name.replace("WidgetKOs-", "").replace("ThemeKOs-", "").replace("ModKOs-", "")
        
        # Fallback si el usuario no usó el prefijo en la URL custom
        if not dest_name:
            dest_name = raw_name

    target_dir = widgets_dir / dest_name

    if target_dir.exists():
        return False, f"Widget folder '{dest_name}' already exists. Use `krystal update` instead."

    # Execute git clone
    result = subprocess.run(
        ["git", "clone", repo_url, str(target_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode != 0:
        return False, f"Git clone failed: {result.stderr.strip()}"

    # Perform Sandbox Scan
    warnings = scan_sandbox(target_dir)
    if warnings:
        # Prepend the warning text
        warn_text = "\n".join(f"  - [red]{w}[/]" for w in warnings)
        return True, f"[yellow]⚠ Sandbox warnings detected![/]\n{warn_text}\n\nPlease review the code before running."

    return True, str(target_dir)


def update_git_repo(widget_dir: Path) -> tuple[bool, str]:
    """Perform a git pull on an existing widget."""
    dot_git = widget_dir / ".git"
    if not dot_git.exists():
        return False, "Not a git repository."
        
    result = subprocess.run(
        ["git", "pull"],
        cwd=str(widget_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode != 0:
        return False, result.stderr.strip()
        
    return True, result.stdout.strip()
