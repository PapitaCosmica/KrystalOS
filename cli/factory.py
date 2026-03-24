"""
KrystalOS — cli/factory.py
Sprint v2.0.0-alpha: The Factory
Contains autonomous widget generation and deep absorption mechanics.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from textwrap import dedent

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table

from core.schema import KrystalWidget, SupportedLanguage, Runtime, UI, GridSize, Capabilities, Modes
from shared.utils import ensure_krystal_project

console = Console()
factory_app = typer.Typer(help="The Factory: Scaffolder and deployment engine for KrystalOS widgets.")

_MOCK_JS_CONTENT = """\
/**
 * KrystalOS — standalone/krystal-mock.js
 * Mock Object to simulate the KrystalOS Core Gateway 
 * directly in the browser's console using LiveServer or XAMPP.
 */
window.Krystal = {
    emit: function(event, data = {}) {
        console.info(`[Krystal-Mock] 🛰️ Evento emitido: '${event}'`, data);
    },
    on: function(event, callback) {
        if (!this._listeners) this._listeners = {};
        if (!this._listeners[event]) this._listeners[event] = [];
        this._listeners[event].push(callback);
        console.log(`[Krystal-Mock] 👂 Suscrito al evento: '${event}'`);
    },
    _triggerMock: function(event, payload) {
        if (this._listeners && this._listeners[event]) {
            console.log(`[Krystal-Mock] ⚡ Simulating incoming event: '${event}'`);
            this._listeners[event].forEach(cb => cb(payload));
        }
    },
    DB: {
        save: async function(key, value) {
            localStorage.setItem(`k_mock_${key}`, JSON.stringify(value));
            return true;
        },
        get: async function(key) {
            const val = localStorage.getItem(`k_mock_${key}`);
            return val ? JSON.parse(val) : null;
        }
    }
};
console.log("[Krystal-Mock] 🔷 Development Bridge Activado.");
"""


def _ui_html(widget_name: str, theme_color: str) -> str:
    """Generate a Tailwind Glassmorphism base ui.html."""
    return dedent(f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <title>{widget_name} — Standalone</title>
          <script src="https://cdn.tailwindcss.com"></script>
          <!-- THE BRIDGE SIMULATOR -->
          <script src="../standalone/krystal-mock.js"></script>
          <style>
            :root {{ --accent: {theme_color}; }}
            body {{
              background: #0f0c29;
              min-height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
            }}
            .glass {{
              background: rgba(255, 255, 255, 0.08);
              backdrop-filter: blur(16px);
              border: 1px solid rgba(255, 255, 255, 0.15);
              box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            }}
          </style>
        </head>
        <body>
          <div class="glass rounded-2xl p-6 w-72 flex flex-col gap-4">
            <h1 class="text-lg font-bold">🔷 {widget_name}</h1>
            <button onclick="Krystal.emit('test-event', {{}})"
              class="w-full py-2 rounded-lg text-sm transition-all"
              style="background: {theme_color};">
              Test Mock Emit
            </button>
          </div>
        </body>
        </html>
    """)


@factory_app.command("make:widget")
def scaffolding_wizard() -> None:
    """Interactive autonomous wizard to create a decoupled widget."""
    console.print("\n[bold cyan]🔷 KrystalOS Factory[/] — Standalone Widget Generator\n")

    name = Prompt.ask("[bold]Widget name[/] (kebab-case)").strip().lower().replace(" ", "-")
    author = Prompt.ask("[bold]Author[/]", default="KOS Developer").strip()

    lang_choices = ["python", "php", "js", "node"]
    language = Prompt.ask(
        "[bold]Language[/] (python/php/js/node)",
        choices=lang_choices,
        default="python"
    )

    architectures = ["Simple", "MVC (Folders)", "AI-Ready"]
    arch = Prompt.ask(
        "[bold]Architecture type[/]",
        choices=architectures,
        default="MVC (Folders)"
    )

    w = IntPrompt.ask("[bold]Grid width[/] (1-12)", default=2)
    h = IntPrompt.ask("[bold]Grid height[/] (1-12)", default=2)
    theme_color = Prompt.ask("[bold]Theme color[/] (hex)", default="#00FFCC").strip()

    # Determine paths based on Krystal Context
    try:
        project_root = ensure_krystal_project()
        widget_dir = project_root / "widgets" / name
        standalone_mode = False
    except FileNotFoundError:
        # Standalone Desktop execution
        widget_dir = Path.cwd() / name
        standalone_mode = True
        console.print("[yellow]⚠ Krystal Core not detected. Creating Standalone Widget.[/]\n")

    if widget_dir.exists():
        console.print(f"[bold red]✗[/] Directory {widget_dir} already exists.")
        raise typer.Exit(code=1)

    # 1. Base folders
    widget_dir.mkdir(parents=True)
    ui_dir = widget_dir / "ui"
    ui_dir.mkdir()
    
    if arch == "MVC (Folders)":
        logic_dir = widget_dir / "logic"
        logic_dir.mkdir()
        (logic_dir / f"Controller.{'py' if language=='python' else 'php'}").write_text("// Controller Logic here")
    elif arch == "AI-Ready":
        ai_dir = widget_dir / "models"
        ai_dir.mkdir()
        (ai_dir / "prompt.txt").write_text("System prompt goes here...")

    # 2. krystal.json
    manifest = KrystalWidget(
        name=name,
        version="0.1.0",
        author=author,
        widget_class="standard",
        runtime=Runtime(language=language, version="latest"),
        ui=UI(grid_size=GridSize(w=w, h=h), icon="🔷", theme_color=theme_color),
        capabilities=Capabilities(events_emitted=["test-event"]),
        modes=Modes(native=True)
    )

    (widget_dir / "krystal.json").write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # 3. UI
    (ui_dir / "index.html").write_text(_ui_html(name, theme_color), encoding="utf-8")

    # 4. Mock
    mock_dir = widget_dir / "standalone"
    mock_dir.mkdir()
    (mock_dir / "krystal-mock.js").write_text(_MOCK_JS_CONTENT, encoding="utf-8")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column(style="bold white")
    table.add_row("Name", name)
    table.add_row("Language", language)
    table.add_row("Architecture", arch)
    table.add_row("Mode", "Standalone" if standalone_mode else "Integrated")
    table.add_row("Location", str(widget_dir))

    console.print(Panel(table, title="[bold cyan]🔷 Widget Scaffolder Done[/]", border_style="cyan"))
