"""
KrystalOS — cli/commands/serve.py
`krystal serve` — Start the Core Gateway and Bento Dashboard via Uvicorn.
"""

from __future__ import annotations

import typer
import uvicorn
from rich.console import Console

console = Console()

def serve_gateway(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Run the FastAPI application via Uvicorn."""
    console.print(f"\n[bold cyan]🔷 KrystalOS Orchestrator[/] starting on [bold]http://{host}:{port}[/]")
    if reload:
        console.print("[dim]Hot-reload activated for widgets.[/]\n")
        
    # Programmatic uvicorn execution
    uvicorn.run(
        "core.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=["core", "widgets"] if reload else None,
        log_level="info",
    )
