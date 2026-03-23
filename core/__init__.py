"""KrystalOS core package."""
from .schema import KrystalWidget, load_widget_manifest
from .event_manager import EventManager

__all__ = ["KrystalWidget", "load_widget_manifest", "EventManager"]
