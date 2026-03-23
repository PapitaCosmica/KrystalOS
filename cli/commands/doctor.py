"""
KrystalOS — cli/commands/doctor.py
`krystal doctor [--bundle]` — hardware & software diagnostic report.

Hardware:  RAM (total/available), CPU count & current usage.
Software:  PATH detection for php, python, node, docker.
AI Hint:   Suggests Lite Mode when available RAM < 4 GB.
--bundle:  Phase 4 stub — portable binary bundle preparation.
"""

from __future__ import annotations

import shutil
import platform
import importlib.util

import psutil
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

# Binaries to check for in PATH
_BINARIES = ["php", "python", "python3", "node", "docker"]

# 4 GB threshold for Lite Mode suggestion (bytes)
_LITE_MODE_RAM_THRESHOLD = 4 * 1024 ** 3


def _bytes_to_gb(b: int) -> str:
    return f"{b / (1024 ** 3):.2f} GB"


def _status_icon(ok: bool) -> str:
    return "[bold green]✓[/]" if ok else "[bold red]✗[/]"


def run_doctor(bundle: bool = False) -> None:
    """Execute the full KrystalOS doctor diagnostic suite."""

    console.print("\n[bold cyan]🔷 KrystalOS Doctor[/] — System Diagnostics\n")

    # ------------------------------------------------------------------ #
    # Phase 4 Bundle Stub                                                  #
    # ------------------------------------------------------------------ #
    if bundle:
        console.print(
            Panel(
                "[yellow]Phase 4 — Bundle Mode is not yet implemented.[/]\n\n"
                "When available, [bold]--bundle[/] will prepare portable binaries\n"
                "(php-cgi, python, node) so KrystalOS can run on machines\n"
                "without a system-wide runtime.",
                title="[bold yellow]📦 Bundle Mode (Phase 4)[/]",
                border_style="yellow",
            )
        )
        return

    # ------------------------------------------------------------------ #
    # 1. Hardware Diagnostics                                              #
    # ------------------------------------------------------------------ #
    mem = psutil.virtual_memory()
    cpu_count_physical = psutil.cpu_count(logical=False) or 0
    cpu_count_logical = psutil.cpu_count(logical=True) or 0
    cpu_usage = psutil.cpu_percent(interval=0.5)

    hw_table = Table(
        title="[bold]🖥  Hardware[/]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
    )
    hw_table.add_column("Metric", style="dim", width=24)
    hw_table.add_column("Value", justify="right")
    hw_table.add_column("Status", justify="center", width=10)

    hw_table.add_row("RAM Total", _bytes_to_gb(mem.total), "")
    hw_table.add_row(
        "RAM Available",
        _bytes_to_gb(mem.available),
        "[green]OK[/]" if mem.available >= _LITE_MODE_RAM_THRESHOLD else "[yellow]LOW[/]",
    )
    hw_table.add_row("RAM Usage", f"{mem.percent:.1f}%", "")
    hw_table.add_row(
        "CPU Cores",
        f"{cpu_count_physical} physical / {cpu_count_logical} logical",
        "",
    )
    hw_table.add_row("CPU Usage", f"{cpu_usage:.1f}%", "")
    hw_table.add_row("Platform", platform.system() + " " + platform.release(), "")

    console.print(hw_table)
    console.print()

    # ------------------------------------------------------------------ #
    # 2. Software / PATH Diagnostics                                       #
    # ------------------------------------------------------------------ #
    sw_table = Table(
        title="[bold]🔧 Software (PATH)[/]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
    )
    sw_table.add_column("Binary", style="bold", width=14)
    sw_table.add_column("Path", style="dim")
    sw_table.add_column("Found", justify="center", width=10)

    found_map: dict[str, bool] = {}
    for binary in _BINARIES:
        path = shutil.which(binary)
        found = path is not None
        found_map[binary] = found
        sw_table.add_row(
            binary,
            path or "[dim italic]not found[/]",
            _status_icon(found),
        )

    # Add Phase 2 Framework Checks
    sw_table.add_section()
    for pkg in ["fastapi", "uvicorn", "sqlmodel"]:
        spec = importlib.util.find_spec(pkg)
        found = spec is not None
        sw_table.add_row(
            f"📦 {pkg}",
            spec.origin if found and spec.origin else "[dim italic]not installed[/]",
            _status_icon(found),
        )

    console.print(sw_table)
    console.print()

    # ------------------------------------------------------------------ #
    # 3. AI Suggestion — Hardware & Empathetic Assistant                 #
    # ------------------------------------------------------------------ #
    # 2GB RAM threshold (Phase 4 Guard)
    ram_guard = 2 * 1024 ** 3 
    
    suggestions = []
    
    # RAM Check
    if mem.available < ram_guard:
        suggestions.append(
            "[yellow]He notado que tu RAM libre es algo ajustada (< 2GB).[/]\n"
            "El [bold]RAM Guard[/] de KrystalOS se activará automáticamente para frenar tareas\n"
            "pesadas y comprimir imágenes. ¿Quizás quieras desactivar el modo Glassmorphism?"
        )
    
    # CPU Check
    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq and cpu_freq.max and cpu_freq.max < 2000:
            suggestions.append(
                "[yellow]Parece que tu procesador es un poco antiguo (< 2.0 GHz).[/]\n"
                "Para que KrystalOS siga [italic bold]volando[/], recomendaría desactivar las sombras pesadas."
            )
    except Exception:
        pass

    # Missing Binary Empathy
    if not found_map.get("php"):
        suggestions.append(
            "[reset]Parece que tu PC no tiene PHP, pero no te preocupes, ¡yo me encargo de traer una\n"
            "versión ligera (php-cgi) portable para ti cuando corras [cyan]krystal bundle[/]![/]"
        )

    if suggestions:
        console.print(
            Panel(
                "\n\n".join(suggestions),
                title="[bold magenta]💡 Krystal AI Assistant[/]",
                border_style="magenta",
            )
        )

    # ------------------------------------------------------------------ #
    # 4. Quick Summary                                                     #
    # ------------------------------------------------------------------ #
    docker_found = found_map.get("docker", False)
    php_found = found_map.get("php", False)
    python_found = found_map.get("python", False) or found_map.get("python3", False)
    node_found = found_map.get("node", False)

    modes_available = []
    if python_found or php_found or node_found:
        modes_available.append("[green]Lite Mode (native)[/]")
    if docker_found:
        modes_available.append("[cyan]Pro Mode (docker)[/]")

    summary_lines = "\n".join(f"  [green]•[/] {m}" for m in modes_available) or (
        "  [red]No supported runtimes detected.[/]"
    )

    console.print(
        Panel(
            f"[bold]Available execution modes:[/]\n{summary_lines}\n\n"
            + ("[green]✓ System is ready for KrystalOS development.[/]"
               if modes_available else
               "[red]✗ Install at least one runtime (php, python, node) to proceed.[/]"),
            title="[bold cyan]🔷 Doctor Summary[/]",
            border_style="cyan",
        )
    )
