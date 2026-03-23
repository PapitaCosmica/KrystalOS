"""
KrystalOS — core/discovery.py
Phase 2: Widget Autodiscovery Engine

Scans the /widgets directory at server startup, validates each widget's
krystal.json contract, and builds an in-memory WidgetRegistry.
"""

from __future__ import annotations

import logging
import asyncio
from pathlib import Path
from typing import Any

from core.schema import KrystalWidget, load_widget_manifest

logger = logging.getLogger("krystal.discovery")

# ---------------------------------------------------------------------------
# Registry entry
# ---------------------------------------------------------------------------

class WidgetEntry:
    """Live registry record for a discovered widget."""

    def __init__(self, manifest: KrystalWidget, widget_dir: Path) -> None:
        self.manifest = manifest
        self.widget_dir = widget_dir.resolve()
        self.port: int | None = None          # assigned by PortMapper on demand
        self.process: asyncio.subprocess.Process | None = None  # live subprocess
        self.last_used: float = 0.0           # epoch timestamp for idle-timeout

    def __repr__(self) -> str:
        return (
            f"<WidgetEntry name={self.manifest.name!r} "
            f"lang={self.manifest.runtime.language} "
            f"port={self.port}>"
        )


# ---------------------------------------------------------------------------
# Registry (singleton)
# ---------------------------------------------------------------------------

class WidgetRegistry:
    """
    In-memory map of all valid widgets discovered at startup.
    Thread-safe for asyncio; use asyncio.Lock if accessing from multiple tasks.
    """

    def __init__(self) -> None:
        self._entries: dict[str, WidgetEntry] = {}

    def register(self, entry: WidgetEntry) -> None:
        self._entries[entry.manifest.name] = entry

    def get(self, name: str) -> WidgetEntry | None:
        return self._entries.get(name)

    def all(self) -> list[WidgetEntry]:
        return list(self._entries.values())

    def names(self) -> list[str]:
        return list(self._entries.keys())

    def summary(self) -> list[dict[str, Any]]:
        return [
            {
                "name": e.manifest.name,
                "language": e.manifest.runtime.language,
                "version": e.manifest.runtime.version,
                "grid": e.manifest.ui.grid_size.model_dump(),
                "modes": e.manifest.modes.model_dump(),
                "port": e.port,
            }
            for e in self._entries.values()
        ]


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

class WidgetScanner:
    """
    Scans <widgets_dir> for KrystalOS widgets at server startup.

    Usage:
        scanner = WidgetScanner(widgets_dir=Path("widgets"))
        registry = scanner.scan()
    """

    def __init__(self, widgets_dir: Path) -> None:
        self.widgets_dir = widgets_dir.resolve()

    # ------------------------------------------------------------------
    # Path Traversal Protection
    # ------------------------------------------------------------------

    def _is_safe_path(self, path: Path) -> bool:
        """
        Ensure *path* is strictly inside self.widgets_dir.
        Rejects any path containing '..' or symlinks that escape the boundary.
        """
        try:
            path.resolve().relative_to(self.widgets_dir)
            return True
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self) -> WidgetRegistry:
        """
        Walk widgets_dir, validate each krystal.json, populate registry.

        Returns:
            WidgetRegistry populated with all valid widgets.
        """
        registry = WidgetRegistry()

        if not self.widgets_dir.exists():
            logger.warning(
                "widgets/ directory not found at %s — no widgets loaded.",
                self.widgets_dir,
            )
            return registry

        candidates = [p for p in self.widgets_dir.iterdir() if p.is_dir()]

        if not candidates:
            logger.info("No widget subdirectories found in %s.", self.widgets_dir)
            return registry

        ok_count = 0
        for widget_dir in sorted(candidates):
            name = widget_dir.name

            # Skip hidden dirs
            if name.startswith("."):
                continue

            # Path traversal guard
            if not self._is_safe_path(widget_dir):
                logger.error(
                    "[%s] Rejected — path escapes widgets/ boundary: %s",
                    name, widget_dir,
                )
                continue

            manifest_path = widget_dir / "krystal.json"

            # Missing manifest
            if not manifest_path.exists():
                logger.error(
                    "[%s] Skipped — krystal.json not found.", name
                )
                continue

            # Validate manifest
            try:
                manifest = load_widget_manifest(str(manifest_path))
            except Exception as exc:
                logger.error(
                    "[%s] Skipped — invalid krystal.json: %s", name, exc
                )
                continue

            entry = WidgetEntry(manifest=manifest, widget_dir=widget_dir)
            registry.register(entry)
            ok_count += 1

            logger.info(
                "[%s] ✓ Loaded — language=%s version=%s grid=%dx%d mode=%s",
                manifest.name,
                manifest.runtime.language,
                manifest.runtime.version,
                manifest.ui.grid_size.w,
                manifest.ui.grid_size.h,
                "docker" if manifest.modes.docker else "native",
            )

        logger.info(
            "Discovery complete: %d/%d widgets loaded.", ok_count, len(candidates)
        )
        return registry


# ---------------------------------------------------------------------------
# Validate proxy path (used by gateway)
# ---------------------------------------------------------------------------

def validate_proxy_path(widget_entry: WidgetEntry, sub_path: str) -> Path:
    """
    Resolve and validate a sub-path within a widget directory.

    Args:
        widget_entry: The registered widget.
        sub_path: URL sub-path from the proxy request (e.g. "data/info").

    Returns:
        Resolved absolute Path guaranteed to be inside widget_dir.

    Raises:
        ValueError: if the path would escape the widget directory.
    """
    # Strip leading slashes to prevent os.path.join absolute override
    clean = sub_path.lstrip("/").replace("..", "")
    resolved = (widget_entry.widget_dir / clean).resolve()

    try:
        resolved.relative_to(widget_entry.widget_dir)
    except ValueError:
        raise ValueError(
            f"Path traversal attempt blocked: '{sub_path}' → '{resolved}'"
        )

    return resolved
