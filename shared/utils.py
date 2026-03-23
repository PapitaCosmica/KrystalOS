"""
KrystalOS — shared/utils.py
Common helpers used across CLI commands and core modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(path: str | Path) -> dict[str, Any]:
    """
    Load a JSON config file and return it as a dict.

    Args:
        path: Absolute or relative path to the JSON file.

    Returns:
        Parsed dict. Returns an empty dict if the file doesn't exist.
    """
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_config(path: str | Path, data: dict[str, Any]) -> None:
    """
    Serialise *data* as pretty-printed JSON and write to *path*.

    Args:
        path: Target file path. Parent directories will be created.
        data: JSON-serialisable dict.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def ensure_krystal_project(cwd: Path | None = None) -> Path:
    """
    Walk up from *cwd* to find a directory containing krystal.config.json.

    Returns:
        Path to the project root.

    Raises:
        FileNotFoundError: if no KrystalOS project root is found.
    """
    cwd = Path(cwd or Path.cwd())
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "krystal.config.json").exists():
            return candidate
    raise FileNotFoundError(
        "Not inside a KrystalOS project. Run `krystal init <name>` first."
    )

import platform

def get_php_executable() -> str:
    """Resolve the portable PHP executable or fallback to OS default."""
    try:
        project_root = ensure_krystal_project()
        local_php = project_root / "bin" / ("php-cgi.exe" if platform.system() == "Windows" else "php-cgi")
        if local_php.exists():
            return str(local_php)
    except FileNotFoundError:
        pass
        
    return "php-cgi.exe" if platform.system() == "Windows" else "php-cgi"

def get_node_executable() -> str:
    """Resolve the portable Node executable or fallback to OS default."""
    try:
        project_root = ensure_krystal_project()
        local_node = project_root / "bin" / ("node.exe" if platform.system() == "Windows" else "node")
        if local_node.exists():
            return str(local_node)
    except FileNotFoundError:
        pass

    return "node"
