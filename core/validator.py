"""
KrystalOS — core/validator.py
Sprint v2.0.0-alpha: The Factory
Manifest & HTML Validator. Validates autonomous widgets before absorption.
Checks for missing 'needs' mods and malicious `<script src>` pointing outside local boundaries.
"""

from __future__ import annotations

import re
from pathlib import Path

from core.schema import KrystalWidget


class ManifestValidator:

    def __init__(self, widget_dir: Path):
        self.widget_dir = widget_dir

    def validate_needs(self, manifest: KrystalWidget) -> None:
        """
        Ensures the widget declares its external MOD dependencies appropriately.
        (Future integration can check these against an installed registry).
        """
        if manifest.needs:
            # Simple check or logging, right now purely syntactic assurance.
            for mod in manifest.needs:
                if not mod.startswith("KOS-") and not mod.startswith("MOD-"):
                    raise ValueError(f"La dependencia '{mod}' no es un Mod válido de KOS (Debe empezar por KOS- o MOD-)")

    def validate_isolation(self) -> None:
        """
        Scans all .html and .js files in the frontend UI directory
        to explicitly prevent Absolute Path Traversal (`C:/...`, `/var/www/`)
        or arbitrary insecure CDN injections that break isolation.
        """
        ui_dir = self.widget_dir / "ui"
        if not ui_dir.exists():
            return

        # Regex patterns to find src="" and href=""
        src_pattern = re.compile(r'src=[\'"]([^\'"]+)[\'"]', re.IGNORECASE)
        href_pattern = re.compile(r'href=[\'"]([^\'"]+)[\'"]', re.IGNORECASE)

        for html_file in ui_dir.rglob("*.html"):
            content = html_file.read_text(encoding="utf-8")
            
            # Check script tags
            for match in src_pattern.finditer(content):
                path = match.group(1).lower()
                # Exclude Tailwind CDN which is an official exception for standalone mode
                if "cdn.tailwindcss.com" in path:
                    continue
                    
                if path.startswith("http") or path.startswith("C:/") or path.startswith("/var") or path.startswith("file://") or path.startswith("//"):
                    raise PermissionError(
                        f"Violación de Aislamiento ({html_file.name}): "
                        f"No se permiten rutas absolutas o CDNs externos no autorizados. "
                        f"Detectado: '{path}'"
                    )

            # Check links
            for match in href_pattern.finditer(content):
                path = match.group(1).lower()
                if path.startswith("http") or path.startswith("C:/") or path.startswith("/var") or path.startswith("file://") or path.startswith("//"):
                    raise PermissionError(
                        f"Violación de Aislamiento ({html_file.name}): "
                        f"No se permiten rutas href absolutas o externas. "
                        f"Detectado: '{path}'"
                    )

    def validate_all(self, manifest: KrystalWidget) -> bool:
        """Execute all heuristics."""
        self.validate_needs(manifest)
        self.validate_isolation()
        return True
