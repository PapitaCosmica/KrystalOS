"""
KrystalOS — core/dependency_manager.py
Sprint v2.1.0: Dependency & Auto-Migration Engine
Analyzes widget schemas to evaluate exclusive dependencies and grant
Safe-Tier status (Silent Install bypass).
"""

from __future__ import annotations

from typing import Optional
from dataclasses import dataclass

from core.schema import KrystalWidget


@dataclass
class Authorization:
    silent: bool
    warnings: list[str]


class DependencyAnalyzer:
    """
    Evaluates widget installations to determine their isolation level.
    Widgets requiring <= 1 Mod are granted Safe-Tier.
    """

    @classmethod
    def evaluate(cls, manifest: KrystalWidget) -> Authorization:
        """
        Scope Check: Reads the manifest.needs array.
        Returns an Authorization object deciding whether avoiding warning dialogs.
        """
        warnings = []
        needs = getattr(manifest, "needs", [])

        if not needs:
            return Authorization(silent=True, warnings=[])

        if len(needs) == 1:
            # Safe-Tier: Single isolated dependency
            return Authorization(silent=True, warnings=[])

        # Conflict-Tier: Needs multiple mods, could cause data collisions easily
        warnings.append(
            f"El widget '{manifest.name}' requiere múltiples Mods: {', '.join(needs)}. "
            "Se requiere intercepción activa para evitar corrupción."
        )

        return Authorization(silent=False, warnings=warnings)

    @classmethod
    def get_primary_mod(cls, manifest: KrystalWidget) -> Optional[str]:
        """Returns the specific primary namespace Mod that the widget is targeting."""
        needs = getattr(manifest, "needs", [])
        return needs[0] if needs else None
