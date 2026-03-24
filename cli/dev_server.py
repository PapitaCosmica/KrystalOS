"""
KrystalOS — cli/dev_server.py
Phase 7.4: Hot Module Replacement (HMR) Dev Server

Watches a Lab directory for file changes and pushes surgical live-reload messages
to connected browsers via WebSocket — no full page refresh required.

Usage:
    python cli/dev_server.py --lab ./labs/my-widget [--port 5173]

Dependencies:
    pip install websockets watchdog rich

Message Protocol (server → client):
    { "type": "RELOAD_STYLES", "file": "style.css",  "content": "<css text>" }
    { "type": "RELOAD_WORKER", "widgetId": "my-widget" }
    { "type": "RELOAD_PAGE" }   # fallback for unknown changes
"""

from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
import os
import signal
import sys
from pathlib import Path

from rich.console import Console

console = Console()

# ── Lazy-import guards (inform user of missing deps) ──────────────────────────
def _require(module: str, pip_name: str = ""):
    try:
        return __import__(module)
    except ImportError:
        pkg = pip_name or module
        console.print(f"[red]✗ Missing dependency:[/] [bold]{pkg}[/]. Run: [cyan]pip install {pkg}[/]")
        sys.exit(1)


# ── Connected clients registry ────────────────────────────────────────────────
_clients: set = set()


async def _broadcast(message: dict) -> None:
    """Send a JSON message to all connected WebSocket clients."""
    if not _clients:
        return
    payload = json.dumps(message)
    dead = set()
    for ws in list(_clients):
        try:
            await ws.send(payload)
        except Exception:
            dead.add(ws)
    _clients -= dead


# ── WebSocket Handler ─────────────────────────────────────────────────────────
async def _ws_handler(websocket) -> None:
    _clients.add(websocket)
    console.print(f"[green]⚡ HMR client connected[/] (total: {len(_clients)})")
    try:
        async for _ in websocket:
            pass  # We only push, not receive
    finally:
        _clients.discard(websocket)
        console.print(f"[dim]HMR client disconnected (remaining: {len(_clients)})[/]")


# ── File Change Event Handler ─────────────────────────────────────────────────
class _LabFileHandler:
    """Watchdog-compatible event handler that queues reload broadcasts."""

    def __init__(self, lab_path: Path, widget_id: str, loop: asyncio.AbstractEventLoop):
        self._lab     = lab_path
        self._widget  = widget_id
        self._loop    = loop

    def _schedule(self, coro) -> None:
        asyncio.run_coroutine_threadsafe(coro, self._loop)

    def _on_file_changed(self, event) -> None:
        path = Path(event.src_path)
        suffix = path.suffix.lower()

        console.print(f"[yellow]📁 Changed:[/] {path.name}")

        if suffix in {'.css', '.html'}:
            # Surgical: inject new content into Shadow DOM
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                content = ""
            self._schedule(_broadcast({
                "type":    "RELOAD_STYLES",
                "file":    path.name,
                "content": content,
            }))

        elif suffix in {'.js', '.mjs', '.wasm', '.py'}:
            # Restart the Web Worker only
            self._schedule(_broadcast({
                "type":     "RELOAD_WORKER",
                "widgetId": self._widget,
                "file":     path.name,
            }))

        else:
            # Unknown type — full page reload as fallback
            self._schedule(_broadcast({"type": "RELOAD_PAGE"}))

    # Watchdog FileSystemEventHandler interface
    def on_modified(self, event):
        if not event.is_directory:
            self._on_file_changed(event)

    def on_created(self, event):
        if not event.is_directory:
            self._on_file_changed(event)


# ── Main Entry Point ──────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="KrystalOS HMR Dev Server — Phase 7.4"
    )
    parser.add_argument("--lab",  type=str, default=".", help="Path to the Lab folder to watch.")
    parser.add_argument("--port", type=int, default=5173, help="WebSocket server port (default: 5173).")
    args = parser.parse_args()

    lab_path  = Path(args.lab).resolve()
    port      = args.port

    if not lab_path.exists():
        console.print(f"[red]✗ Lab path not found:[/] {lab_path}")
        sys.exit(1)

    # Derive widget ID from folder name
    widget_id = lab_path.name

    console.print(f"\n[bold cyan]🔥 KrystalOS HMR Dev Server[/]")
    console.print(f"Watching: [yellow]{lab_path}[/]")
    console.print(f"WebSocket: [cyan]ws://localhost:{port}[/]")
    console.print(f"Widget ID: [magenta]{widget_id}[/]")
    console.print("[dim]Press Ctrl+C to stop.[/]\n")

    # ── Import heavy deps here (after user sees startup message) ─────────────
    websockets_mod = _require("websockets")
    watchdog_obs   = _require("watchdog.observers", "watchdog")
    watchdog_evt   = _require("watchdog.events",    "watchdog")
    Observer       = watchdog_obs.Observer
    FileSystemEventHandler = watchdog_evt.FileSystemEventHandler

    async def _run() -> None:
        loop = asyncio.get_event_loop()

        # Build watcher
        handler = _LabFileHandler(lab_path, widget_id, loop)

        # Monkey-patch Watchdog's abstract methods onto our handler
        file_handler = FileSystemEventHandler()
        file_handler.on_modified = handler.on_modified
        file_handler.on_created  = handler.on_created

        observer = Observer()
        observer.schedule(file_handler, str(lab_path), recursive=True)
        observer.start()
        console.print("[green]✓ File watcher active.[/]")

        # Start WebSocket server
        async with websockets_mod.serve(_ws_handler, "localhost", port):
            console.print(f"[green]✓ WebSocket server listening on port {port}.[/]\n")
            try:
                await asyncio.Future()  # run forever
            except asyncio.CancelledError:
                pass
            finally:
                observer.stop()
                observer.join()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[dim]HMR Dev Server stopped.[/]")


if __name__ == "__main__":
    main()
