"""
KrystalOS — cli/commands/mod_scaffolder.py
Generates a Backend Mod or its isolated Lab testing environment.
"""

import os
import typer
from rich.console import Console
from rich.prompt import Prompt

from shared.utils import ensure_krystal_project
from cli.lab_engine import deploy_lab

console = Console()

def make_mod(
    name: str = typer.Argument(None, help="Name of the Mod"),
    test: bool = typer.Option(False, "--test", help="Generates an isolated Sandbox Lab for this Mod")
):
    """
    Scaffold a new backend Mod.
    If --test is passed, creates a Zero-Config UI dashboard (Swagger style) for testing.
    """
    console.print("\n[bold magenta]🧩 KrystalOS Mod Scaffolder[/]")
    project_root = ensure_krystal_project()

    if not name:
        name = Prompt.ask("[cyan]¿Cómo se llama tu Mod?[/]", default="MOD-USERS")
        
    clean_name = name.upper().replace(" ", "-")

    if test:
        _generate_mod_lab(clean_name)
        return

    # Standard Generation
    mod_dir = project_root / "mods" / clean_name
    if mod_dir.exists():
        console.print(f"[red]✗ El Mod ya existe:[/] {mod_dir}")
        raise typer.Exit(1)

    console.print("\n[yellow]¿Cuál es el alcance y nivel de acceso de este Mod?[/]")
    scope_options = [
        "Core Modification (Acceso profundo, altera Kernel o DB)",
        "Feature Integration (APIs de terceros, OCR, Clima)",
        "Background Daemon/Service (Procesos invisibles, indexadores)"
    ]
    for idx, opt in enumerate(scope_options):
        console.print(f"  [cyan]{idx+1}. {opt}[/]")
    
    scope_choice = Prompt.ask("[yellow]Elige el alcance (1-3)[/]", default="2")
    
    permissions = []
    scope_id = "FEATURE"
    
    if scope_choice == "1":
        scope_id = "CORE_MOD"
        permissions = ["DB_WRITE", "DB_READ", "KERNEL_HOOK", "FILE_SYSTEM"]
    elif scope_choice == "3":
        scope_id = "DAEMON"
        permissions = ["BACKGROUND_WORKER", "NETWORK_SOCKET"]
    else:
        permissions = ["NETWORK_REST", "DB_READ_ONLY"]

    # Target Environment
    console.print("\n[yellow]¿Target Mode?[/] (LITE bloquea procesos intensivos)")
    target_env = Prompt.ask("[bold]Target Environment[/]", choices=["LITE", "PRO"], default="LITE")

    mod_dir.mkdir(parents=True)
    
    import json
    manifest = {
        "name": clean_name,
        "version": "1.0.0",
        "author": "krystal-dev",
        "target": target_env,
        "scope": scope_id,
        "permissions": permissions,
        "shared_tools": [],
        "timeout_idle": "5m",
        "entrypoint": "main.py"
    }
    
    with open(mod_dir / "krystal.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    # Generate basic boilerplate
    with open(mod_dir / "main.py", "w", encoding="utf-8") as f:
        f.write("def run():\n    pass\n")

    console.print(f"\n[green]✓ Mod {clean_name} creado exitosamente.[/]")
    console.print(f"Scope: [magenta]{scope_id}[/]")
    console.print(f"Persmisos Asignados: [yellow]{permissions}[/]")


def _generate_mod_lab(mod_name: str) -> None:
    """Generate a Mini-OS Lab (lab-env/) inside a standalone Mod folder."""
    import subprocess
    import webbrowser
    from pathlib import Path
    from rich.panel import Panel

    lab_dir = Path.cwd() / mod_name / "lab-env"
    lab_dir.mkdir(parents=True, exist_ok=True)
    mod_dir  = lab_dir.parent

    # ── mock-database.js ─────────────────────────────────────────────────────
    mock_db = """/**
 * KrystalOS Mini-OS Lab — mock-database.js
 * Simulates Krystal.db (SQLite/Postgres) using localStorage.
 * Auto-loaded by dashboard.html before the Mod's own JS.
 */
(function() {
  'use strict';
  if (!window.Krystal) window.Krystal = {};

  window.Krystal.db = {
    save: async function(key, value) {
      await _delay();
      _checkError();
      localStorage.setItem('kos_mock_' + key, JSON.stringify(value));
      return { ok: true, key };
    },
    get: async function(key) {
      await _delay();
      _checkError();
      const raw = localStorage.getItem('kos_mock_' + key);
      return raw ? JSON.parse(raw) : null;
    },
    delete: async function(key) {
      await _delay();
      _checkError();
      localStorage.removeItem('kos_mock_' + key);
      return { ok: true };
    },
    list: async function() {
      await _delay();
      _checkError();
      const keys = Object.keys(localStorage).filter(k => k.startsWith('kos_mock_'));
      return keys.map(k => k.replace('kos_mock_', ''));
    }
  };

  function _delay() {
    const ms = window.__kosLatency ? 2000 : 0;
    return new Promise(r => setTimeout(r, ms));
  }
  function _checkError() {
    if (window.__kosForceError) throw { code: 500, message: 'Forced HTTP 500 (stress simulator)' };
  }

  console.log('[Krystal.db] \u{1F4BE} Mock Database Online (localStorage mode)');
})();
"""
    (lab_dir / "mock-database.js").write_text(mock_db, encoding="utf-8")

    # ── dashboard.html ───────────────────────────────────────────────────────
    dashboard_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>KrystalOS — {mod_name} Dev Dashboard</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    :root{{
      --kos-bg:#0f0c29; --kos-surface:rgba(255,255,255,0.06);
      --kos-accent:#00FFCC; --kos-text:rgba(255,255,255,0.85);
      --kos-error:#FF4C4C; --kos-warn:#FFB800;
    }}
    body{{background:var(--kos-bg);color:var(--kos-text);font-family:system-ui,sans-serif;min-height:100vh;padding:24px}}
    header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px;border-bottom:1px solid rgba(255,255,255,.1);padding-bottom:16px}}
    header h1{{font-size:22px;font-weight:800;letter-spacing:-.02em}}
    header h1 span{{color:var(--kos-accent)}}
    .badge{{font-size:10px;padding:3px 10px;border-radius:20px;border:1px solid;font-weight:700;letter-spacing:.06em}}
    .badge-mod{{border-color:var(--kos-accent);color:var(--kos-accent)}}
    .stress-bar{{display:flex;gap:10px;margin-bottom:24px;flex-wrap:wrap}}
    .toggle-btn{{padding:6px 16px;border-radius:20px;border:1px solid;background:transparent;cursor:pointer;font-size:12px;font-weight:600;transition:all .2s}}
    .toggle-btn.active{{background:var(--kos-accent);border-color:var(--kos-accent);color:#000}}
    #latency-btn{{border-color:var(--kos-warn);color:var(--kos-warn)}}
    #latency-btn.active{{background:var(--kos-warn);color:#000}}
    #error-btn{{border-color:var(--kos-error);color:var(--kos-error)}}
    #error-btn.active{{background:var(--kos-error);color:#fff}}
    .status-strip{{font-size:11px;padding:6px 14px;border-radius:8px;background:rgba(255,255,255,.04);margin-bottom:20px;color:rgba(255,255,255,.4)}}
    .status-strip .label{{font-weight:700;color:var(--kos-accent)}}
    .methods{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
    .card{{background:var(--kos-surface);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:18px;display:flex;flex-direction:column;gap:10px}}
    .card h3{{font-size:13px;font-weight:700;color:#fff}}
    .card p{{font-size:11px;color:rgba(255,255,255,.4);line-height:1.5}}
    .card textarea{{width:100%;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:8px;color:var(--kos-text);font-family:monospace;font-size:11px;resize:vertical;min-height:60px}}
    .run-btn{{padding:7px 14px;border-radius:10px;border:none;background:var(--kos-accent);color:#000;font-weight:700;font-size:12px;cursor:pointer;align-self:flex-start;transition:opacity .2s}}
    .run-btn:hover{{opacity:.8}}
    .response{{background:rgba(0,0,0,.4);border:1px solid rgba(255,255,255,.07);border-radius:8px;padding:10px;font-family:monospace;font-size:11px;white-space:pre-wrap;word-break:break-word;color:rgba(255,255,255,.7);min-height:40px;max-height:120px;overflow:auto}}
  </style>
</head>
<body>
  <header>
    <h1>🧩 <span>{mod_name}</span> — Dev Dashboard</h1>
    <span class="badge badge-mod">MOD LAB</span>
  </header>

  <div class="stress-bar">
    <button id="latency-btn" class="toggle-btn" onclick="toggleLatency(this)">⏰ Simular Latencia (2s)</button>
    <button id="error-btn"   class="toggle-btn" onclick="toggleError(this)">⚠️ Forzar Error 500</button>
  </div>

  <div class="status-strip">
    Estado: <span class="label" id="status-text">Listo ✔</span>
    &nbsp;&bull;&nbsp; Latencia: <span id="lat-label">OFF</span>
    &nbsp;&bull;&nbsp; Error 500: <span id="err-label">OFF</span>
  </div>

  <div class="methods" id="methods-grid">
    <!-- Cards are injected by the inline script below -->
  </div>

  <script src="mock-database.js"></script>
  <script>
    // ── API Method Map — customize these to match your Mod's exported functions ──
    // Format: {{ id, label, description, defaultInput }}
    const API_MAP = [
      {{ id: 'db_save',   label: 'db.save(key, value)',   description: 'Saves a value to the mock database.',  defaultInput: '{{"key": "user_1", "value": {{"name": "Ozzy"}}}}' }},
      {{ id: 'db_get',    label: 'db.get(key)',            description: 'Retrieves a value by key.',             defaultInput: '{{"key": "user_1"}}' }},
      {{ id: 'db_list',   label: 'db.list()',              description: 'Lists all stored keys.',                defaultInput: '{{}}' }},
      {{ id: 'db_delete', label: 'db.delete(key)',         description: 'Removes a value from the DB.',         defaultInput: '{{"key": "user_1"}}' }},
    ];

    // Render cards
    const grid = document.getElementById('methods-grid');
    API_MAP.forEach(method => {{
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <h3>${{method.label}}</h3>
        <p>${{method.description}}</p>
        <textarea id="inp-${{method.id}}">${{method.defaultInput}}</textarea>
        <button class="run-btn" onclick="runMethod('${{method.id}}')">▶ Ejecutar</button>
        <div class="response" id="res-${{method.id}}">Esperando...</div>
      `;
      grid.appendChild(card);
    }});

    async function runMethod(id) {{
      const input = document.getElementById('inp-' + id).value;
      const resEl = document.getElementById('res-' + id);
      let args = {{}};
      try {{ args = JSON.parse(input); }} catch {{ resEl.textContent = '⚠ JSON inválido'; return; }}
      resEl.textContent = 'Ejecutando...';
      try {{
        let result;
        if (id === 'db_save')   result = await Krystal.db.save(args.key, args.value);
        if (id === 'db_get')    result = await Krystal.db.get(args.key);
        if (id === 'db_list')   result = await Krystal.db.list();
        if (id === 'db_delete') result = await Krystal.db.delete(args.key);
        resEl.textContent = JSON.stringify(result, null, 2);
        resEl.style.color = 'rgba(255,255,255,.7)';
      }} catch(e) {{
        resEl.textContent = '⚠ ' + (e.message || JSON.stringify(e));
        resEl.style.color = '#FF4C4C';
      }}
    }}

    function toggleLatency(btn) {{
      window.__kosLatency = !window.__kosLatency;
      btn.classList.toggle('active');
      document.getElementById('lat-label').textContent = window.__kosLatency ? 'ON (2s)' : 'OFF';
    }}
    function toggleError(btn) {{
      window.__kosForceError = !window.__kosForceError;
      btn.classList.toggle('active');
      document.getElementById('err-label').textContent = window.__kosForceError ? 'ON' : 'OFF';
      document.getElementById('status-text').textContent = window.__kosForceError ? 'STRESS MODE ⚠' : 'Listo ✔';
    }}
  </script>
</body>
</html>"""
    (lab_dir / "dashboard.html").write_text(dashboard_html, encoding="utf-8")

    console.print(
        Panel(
            f"[green]✓ Mini-OS Lab generado en:[/] [cyan]{lab_dir}[/]\n"
            f"  • [yellow]dashboard.html[/] — Swagger UI con toggles de Latencia / Error 500\n"
            f"  • [yellow]mock-database.js[/] — Krystal.db simulado en localStorage",
            title="🧪 Mod Lab listo",
            border_style="magenta",
        )
    )

    # CLI Server Prompt
    from rich.prompt import Confirm
    if Confirm.ask("🧪 ¿Deseas iniciar el Mini-KrystalOS Server para probar tu Mod ahora?", default=False):
        import webbrowser, subprocess
        console.print(f"[cyan]Sirviendo en http://localhost:8080/dashboard.html ...[/]")
        webbrowser.open("http://localhost:8080/dashboard.html")
        subprocess.run(["python", "-m", "http.server", "8080", "--directory", str(lab_dir)])

