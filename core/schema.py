"""
KrystalOS — core/schema.py
Pydantic v2 validation model for krystal.json widget manifests.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SupportedLanguage(str, Enum):
    PHP = "php"
    PYTHON = "python"
    JAVASCRIPT = "js"
    NODE = "node"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class GridSize(BaseModel):
    """Bento-grid cell dimensions."""
    w: int = Field(ge=1, le=12, description="Width in grid columns (1-12)")
    h: int = Field(ge=1, le=12, description="Height in grid rows (1-12)")


class Runtime(BaseModel):
    """Execution runtime specification."""
    language: SupportedLanguage = Field(description="Target language runtime")
    version: str = Field(
        min_length=1,
        description="Runtime version string (e.g. '3.11', '8.2', '5.6')",
    )

    @field_validator("version")
    @classmethod
    def version_format(cls, v: str) -> str:
        """Loose semver-style check: must start with a digit."""
        if not v[0].isdigit():
            raise ValueError("version must start with a digit (e.g. '3.11')")
        return v


class UI(BaseModel):
    """Visual / Bento-grid appearance config."""
    grid_size: GridSize = Field(default_factory=lambda: GridSize(w=2, h=2))
    icon: str = Field(default="🔷", description="Emoji or icon identifier")
    theme_color: str = Field(
        default="#7C3AED",
        pattern=r"^#[0-9A-Fa-f]{3,6}$",
        description="Hex color for widget accent (e.g. '#7C3AED')",
    )


class Capabilities(BaseModel):
    """Event Bus capabilities — used by Phase 3 EventManager."""
    events_emitted: list[str] = Field(
        default_factory=list,
        description="Event names this widget publishes",
    )
    events_subscribed: list[str] = Field(
        default_factory=list,
        description="Event names this widget listens for",
    )


class Modes(BaseModel):
    """
    Execution mode flags.
    native=True  → Lite Mode (no Docker required, Phase 4 portable bundles).
    docker=True  → Pro Mode (full containerised environment).
    """
    native: bool = Field(default=True, description="Supports native / Lite mode")
    docker: bool = Field(default=False, description="Requires Docker / Pro mode")


# ---------------------------------------------------------------------------
# Root model
# ---------------------------------------------------------------------------

class KrystalWidget(BaseModel):
    """
    Complete krystal.json manifest model.

    Every widget in KrystalOS must ship a valid krystal.json at its root.
    Use KrystalWidget.model_validate_json(raw_json) or
    KrystalWidget(**dict_data) for validation.
    """

    # Identity
    name: str = Field(min_length=1, description="Unique widget slug (kebab-case)")
    version: str = Field(
        default="0.1.0",
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version (MAJOR.MINOR.PATCH)",
    )
    author: str = Field(min_length=1, description="Author name or handle")

    # Runtime
    runtime: Runtime

    # UI
    ui: UI = Field(default_factory=UI)

    # Capabilities (Phase 3 hook)
    capabilities: Capabilities = Field(default_factory=Capabilities)

    # Multi-Mode
    modes: Modes = Field(default_factory=Modes)

    # Profiling (v1.1.0-beta)
    widget_class: str = Field(default="standard", alias="class", description="standard or heavy")

    def to_krystal_json(self) -> dict:
        """Export back to a krystal.json-compatible dict."""
        return self.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_widget_manifest(path: str) -> KrystalWidget:
    """Load and validate a krystal.json file from *path*."""
    import json
    from pathlib import Path

    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    return KrystalWidget(**data)
