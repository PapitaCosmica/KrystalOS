"""
KrystalOS — cli/commands/serve.py
Phase 3: Subcommand Group for Process Management and Gateway execution.
"""

from __future__ import annotations

import os
import time

import typer
import uvicorn
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from pathlib import Path

from core.schema import load_widget_manifest
from cli.system_profiler import get_cached_env_state
from shared.utils import ensure_krystal_project

from cli.process_manager import PidManager, get_process_by_port, kill_process_by_port, kill_all_tracked

console = Console()
serve_app = typer.Typer(help="Manage KrystalOS gateway processes and start the server.")

def check_widget_compatibility() -> None:
    """
    Simulates reading widget requirements before launching in Krystal serve.
    Interrupts and prompts the user if they try to run a 'heavy' widget in a 'LITE' environment.
    """
    try:
        project_root = ensure_krystal_project()
    except FileNotFoundError:
        return

    env_state = get_cached_env_state()
    if env_state.environment != "LITE":
        return

    widgets_dir = project_root / "widgets"
    if not widgets_dir.exists():
        return
        
    for widget_folder in widgets_dir.iterdir():
        if not widget_folder.is_dir():
            continue
            
        manifest_path = widget_folder / "krystal.json"
        if not manifest_path.exists():
            continue
            
        try:
            widget = load_widget_manifest(str(manifest_path))
            # Use getattr to safely check since Pydantic handles the alias 'class' -> 'widget_class'
            is_heavy = getattr(widget, "widget_class", "standard") == "heavy"
            
            if is_heavy:
                console.print(
                    f"\n[bold yellow]\[!] ADVERTENCIA: El widget '{widget.name}' es \"Heavy-Class\"[/]\n"
                    f"[yellow]y tu sistema está actualmente en [/][bold yellow]Modo Lite[/][yellow].[/]\n"
                    f"[dim]Se recomienda usar la versión Lite del widget si existe o actualizar el hardware.[/]"
                )
                
                # rich.prompt.Confirm
                force = Confirm.ask(
                    "[bold red]¿Deseas forzar la ejecución bajo tu propio riesgo?[/]", 
                    default=False
                )
                
                if not force:
                    console.print("[dim]Operación abortada limpiamente.[/]")
                    raise typer.Exit(code=0)
                else:
                    console.print("[bold red]⚠ Forzando ejecución de widget pesado. Puede haber lag...[/]")
        except Exception:
            pass


@serve_app.command("start")
def serve_start(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind socket to this host."),
    port: int = typer.Option(8000, "--port", "-p", help="Bind socket to this port."),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload for widgets."),
) -> None:
    """Start the KrystalOS Core Gateway Server."""
    # Profiler / Hardware Guard interception
    check_widget_compatibility()

    # Process check
    if get_process_by_port(port):
        console.print(f"\n[bold red]ERROR:[/] Port {port} is already in use by another process.")
        console.print(f"Run `[cyan]krystal serve destroy --port {port}[/]` to free it, or use a different port.\n")
        raise typer.Exit(code=1)

    console.print(f"\n[bold cyan]🔷 KrystalOS Orchestrator[/] starting on [bold]http://{host}:{port}[/]")
    if reload:
        console.print("[dim]Hot-reload activated for widgets.[/]")
    
    # Track this new gateway instance
    pm = PidManager()
    pm.add_gateway(os.getpid())
    
    try:
        # Programmatic uvicorn execution
        uvicorn.run(
            "core.main:app",
            host=host,
            port=port,
            reload=reload,
            reload_dirs=["core", "widgets"] if reload else None,
            log_level="info",
        )
    finally:
        # Remove gateway PID upon graceful exit
        pm.remove_pid(os.getpid())

@serve_app.command("destroy")
def serve_destroy(
    port: int = typer.Option(None, "--port", "-p", help="Port number to forcefully free."),
    all: bool = typer.Option(False, "--all", "-a", help="Kill all KrystalOS gateway and widget subprocesses."),
    force: bool = typer.Option(False, "--force", "-f", help="Bypass safety prompts for privileged ports."),
) -> None:
    """Kill processes attached to a specific port or kill all tracked KrystalOS processes safely."""
    if not port and not all:
        console.print("[yellow]Please specify `--port <PORT>` or `--all`.[/]")
        raise typer.Exit(code=1)
        
    if all:
        console.print("\n[bold red]Terminating ALL KrystalOS processes...[/]")
        killed = kill_all_tracked()
        console.print(f"[bold green]✓ Cleanup complete. {killed} tracked processes eliminated.[/]\n")
        return
        
    if port:
        console.print(f"\n[cyan]Attempting to free port {port}...[/]")
        killed = kill_process_by_port(port, force=force)
        if not killed:
            raise typer.Exit(code=1)
        console.print()

@serve_app.command("status")
def serve_status() -> None:
    """Show live status of all orchestrator instances and their RAM usage."""
    from cli.process_manager import PidManager # Local import due to cyclical
    import psutil

    pm = PidManager()
    data = pm.load()
    
    table = Table(title="🔷 Active KrystalOS Processes")
    table.add_column("PID", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Status")
    table.add_column("RAM (MB)", justify="right")

    all_pids = [("Gateway", pid) for pid in data["gateways"]] + [("Widget Subprocess", pid) for pid in data["children"]]
    
    total_mb = 0.0

    if not all_pids:
        console.print("\n[yellow]No tracked processes running right now.[/]\n")
        return

    for ptype, pid in all_pids:
        try:
            p = psutil.Process(pid)
            mem = p.memory_info().rss / (1024 * 1024)
            total_mb += mem
            
            status = p.status()
            status_fmt = f"[green]{status}[/]" if status in ("running", "sleeping") else f"[red]{status}[/]"
            
            table.add_row(
                str(pid),
                ptype,
                p.name(),
                status_fmt,
                f"{mem:.1f}"
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    console.print()
    console.print(table)
    console.print(f"  [b]Total Memory Footprint:[/] {total_mb:.1f} MB\n")

