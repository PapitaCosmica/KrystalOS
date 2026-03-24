"""
KrystalOS — core/middleware/collision_handler.py
Sprint v2.1.0: Dependency & Auto-Migration Engine
Intercepts and evaluates data overwrites between Widgets and Mods.
"""

from __future__ import annotations

from typing import Any, Callable

from core.schema import KrystalWidget
from core.dependency_manager import DependencyAnalyzer


class CollisionMiddleware:
    """
    Middleware that wraps around database or Mod execution functions.
    It performs a preventative Catch (Catch Preventivo) if a widget
    attempts to corrupt shared Mod Schemas.
    """

    @classmethod
    def intercept(
        cls, 
        widget_manifest: KrystalWidget, 
        target_mod: str, 
        action: Callable[..., Any], 
        *args, 
        **kwargs
    ) -> Any:
        """
        Catches risky execution calls.
        - widget_manifest: The widget attempting the modification.
        - target_mod: The Mod being modified (e.g. MOD-USERS).
        - action: The unsafe callback altering data/schema.
        """
        # 1. Dependency Check
        auth = DependencyAnalyzer.evaluate(widget_manifest)
        
        # 2. Collision Classification
        # If the widget explicitly needs this Mod, it's authorized.
        # But if it triggers a multi-dependency warning, we MUST intercept.
        if target_mod not in getattr(widget_manifest, "needs", []):
            raise PermissionError(
                f"[Interceptor] Bloqueo Preventivo: "
                f"El widget '{widget_manifest.name}' intentó alterar '{target_mod}' "
                "sin declararlo explícitamente en su krystal.json ('needs' array)."
            )

        if not auth.silent:
            # Multi-Mod Interception
            # Launch Auto-Migration Sequence since it is not Safe-Tier 
            # (which means multiple frameworks are colliding).
            from database.auto_migrator import AutoMigrator
            migrator = AutoMigrator()
            
            # The action is suspended. We yield to the Zero Data-Loss Migrator.
            return migrator.execute_safe_mutation(target_mod, widget_manifest.name, action, *args, **kwargs)

        # Safe-Tier Execution (Bypass)
        return action(*args, **kwargs)
