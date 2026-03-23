"""
KrystalOS — cli/process_manager.py
Phase 3: Advanced Process and Port Management
Tracks running orchestrator instances and their child processes safely.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import psutil
from rich.console import Console

from shared.utils import ensure_krystal_project

console = Console()
logger = logging.getLogger("krystal.process_manager")

# ---------------------------------------------------------------------------
# PID Persistence
# ---------------------------------------------------------------------------

class PidManager:
    """Manages tracking of running KrystalOS processes in .krystal/pids.json"""

    def __init__(self) -> None:
        try:
            self.project_root = ensure_krystal_project()
        except FileNotFoundError:
            self.project_root = Path.cwd()
        
        self.pids_file = self.project_root / ".krystal" / "pids.json"
        
        if not self.pids_file.parent.exists():
            self.pids_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, list[int]]:
        """Load currently tracked PIDs."""
        if not self.pids_file.exists():
            return {"gateways": [], "children": []}
        try:
            with open(self.pids_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"gateways": [], "children": []}

    def save(self, data: dict[str, list[int]]) -> None:
        """Save PID dictionary to file."""
        with open(self.pids_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_gateway(self, pid: int) -> None:
        """Track a main Orchestrator (Gateway) process."""
        data = self.load()
        if pid not in data["gateways"]:
            data["gateways"].append(pid)
        self.save(data)

    def add_child(self, pid: int) -> None:
        """Track a spawned child process (PHP-CGI, Node, etc.)."""
        data = self.load()
        if pid not in data["children"]:
            data["children"].append(pid)
        self.save(data)

    def remove_pid(self, pid: int) -> None:
        """Remove a PID from all trackers."""
        data = self.load()
        changed = False
        if pid in data["gateways"]:
            data["gateways"].remove(pid)
            changed = True
        if pid in data["children"]:
            data["children"].remove(pid)
            changed = True
        
        if changed:
            self.save(data)


# ---------------------------------------------------------------------------
# Port Scanner & Process Killer
# ---------------------------------------------------------------------------

def get_process_by_port(port: int) -> psutil.Process | None:
    """Find a running process bound to the specified TCP port."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='tcp'):
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return proc
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
    return None

def kill_process_by_port(port: int, force: bool = False) -> bool:
    """Find and kill the process listening on a specific port."""
    if port < 1024 and not force:
        console.print(f"[bold red]WARNING:[/] Port {port} is a privileged system port.")
        console.print("To forcefully destroy it, use `--force`.")
        return False

    proc = get_process_by_port(port)
    if not proc:
        console.print(f"[yellow]No active process found listening on port {port}.[/]")
        return False

    try:
        proc_name = proc.name()
        pid = proc.pid
        proc.terminate()
        proc.wait(timeout=3)
        console.print(f"[bold green]PORT :{port} LIBERADO[/] ([dim]Killed {proc_name} PID:{pid}[/])")
        PidManager().remove_pid(pid)
        return True
    except psutil.TimeoutExpired:
        if force:
            proc.kill()
            console.print(f"[bold green]PORT :{port} LIBERADO[/] ([dim]Force Killed {proc_name} PID:{pid}[/])")
            PidManager().remove_pid(pid)
            return True
        console.print(f"[red]Failed to gracefully terminate process {pid}. Use --force.[/]")
        return False
    except Exception as e:
        console.print(f"[red]Error terminating process:[/] {e}")
        return False

def kill_all_tracked() -> int:
    """Kill all tracked KrystalOS processes recorded in pids.json to free RAM."""
    pm = PidManager()
    data = pm.load()
    killed = 0

    all_pids = data["children"] + data["gateways"]
    
    for pid in all_pids:
        try:
            p = psutil.Process(pid)
            name = p.name()
            p.terminate()
            p.wait(timeout=2)
            console.print(f"[dim]Terminated tracked process {name} (PID:{pid})[/]")
            killed += 1
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            # Already dead
            pass
        except Exception as e:
            console.print(f"[yellow]Could not terminate PID:{pid} - {e}[/]")

    # Clear tracking file
    pm.save({"gateways": [], "children": []})
    
    # DB cleanup for Lite mode
    # Check if SQLite DB WAL/SHM files are lingering and clean them up
    project_root = pm.project_root
    db_path = project_root / ".krystal" / "krystal.db"
    for suffix in ["-shm", "-wal"]:
        temp_file = db_path.with_name(f"krystal.db{suffix}")
        if temp_file.exists():
            try:
                temp_file.unlink()
                console.print(f"[dim]Cleaned up stranded database file: {temp_file.name}[/]")
            except Exception:
                pass

    return killed
