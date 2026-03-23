"""
KrystalOS — cli/commands/install.py
PHASE 5 STUB: `krystal install <url>` — install a widget from a GitHub URL.

Phase 5 will use sparse-checkout or degit to clone only the widget
subdirectory from any GitHub repo, then validate its krystal.json
before adding it to the local /widgets directory.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

console = Console()


def install_widget(url: str) -> None:
    """
    Install a KrystalOS widget from a GitHub URL.

    Phase 5 planned behaviour:
      1. Parse the GitHub URL to extract repo + subdirectory.
      2. Use `git clone --filter=blob:none --sparse` for minimal download.
      3. Validate the widget's krystal.json via KrystalWidget.
      4. Copy widget folder into project's /widgets directory.
      5. Register widget in .krystal/state.json.

    Current status: stub — prints informational notice.
    """
    console.print(
        Panel(
            f"[yellow]Phase 5 — Community Registry is not yet implemented.[/]\n\n"
            f"Requested URL: [bold]{url}[/]\n\n"
            "When available, this command will:\n"
            "  [dim]• Sparse-clone only the widget subfolder from GitHub[/]\n"
            "  [dim]• Validate krystal.json before installation[/]\n"
            "  [dim]• Register the widget in .krystal/state.json[/]",
            title="[bold yellow]📦 Install Widget (Phase 5)[/]",
            border_style="yellow",
        )
    )
