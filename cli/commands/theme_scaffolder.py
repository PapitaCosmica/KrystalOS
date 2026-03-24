"""
KrystalOS — cli/commands/theme_scaffolder.py
Phase 7: Modular Themes Scaffolding
Creates robust templates for CORE_LAYOUT, COLOR_PALETTE, and WIDGET_SKINs.
"""

import os
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

from shared.utils import ensure_krystal_project

console = Console()
theme_app = typer.Typer(help="Theme & Modular UI Scaffolder commands.")

VALID_TYPES = [
    "CORE_LAYOUT",
    "WIDGET_SKIN",
    "COLOR_PALETTE",
    "ANIMATION_PACK",
    "SYSTEM_ASSETS",
    "FULL_OVERHAUL"
]

@theme_app.command("theme")
def make_theme(
    name: str = typer.Argument(None, help="Name of the theme"),
    type: str = typer.Option(None, "--type", "-t", help="Theme category (e.g. CORE_LAYOUT, COLOR_PALETTE)"),
    test: bool = typer.Option(False, "--test", help="Generates an isolated Visual Compositor Lab for this Theme")
):
    """
    Scaffold a new modular theme for the KrystalOS Compositor.
    """
    if test:
        if not name:
            name = typer.prompt("¿Cómo se llama tu Theme Lab?", default="my-theme-lab")
        clean = name.replace(" ", "-").lower()
        _generate_theme_lab(clean)
        return

    console.print("\n[bold magenta]🎨 KrystalOS Theme Scaffolder[/]")
    # v2.2.6.4: True Standalone — no crash outside project
    project_root = ensure_krystal_project(strict=False)
    standalone = not (project_root / "krystal.config.json").exists()

    if not name:
        name = Prompt.ask("[cyan]¿Cómo se llama tu tema modular?[/]", default="mi-tema-genial")

    if not type or type.upper() not in VALID_TYPES:
        console.print("\nTipos de Capas disponibles:")
        for idx, t in enumerate(VALID_TYPES):
            console.print(f"  [yellow]{idx+1}. {t}[/]")
        
        choice = Prompt.ask("[cyan]Elige un tipo de capa (1-6)[/]", default="3")
        try:
            type = VALID_TYPES[int(choice) - 1]
        except (ValueError, IndexError):
            console.print("[red]Opción inválida. Abortando.[/]")
            raise typer.Exit(1)
            
    type = type.upper()

    clean_name = name.lower().replace(" ", "-")
    if standalone:
        theme_dir = Path.cwd() / clean_name
        console.print(
            "[yellow]⚠[/]  Modo Standalone — generando Tema en [cyan]./{}[/]\n".format(clean_name)
        )
    else:
        theme_dir = project_root / "themes" / clean_name

    if theme_dir.exists():
        console.print(f"[red]✗ El directorio ya existe:[/] {theme_dir}")
        raise typer.Exit(1)

    theme_dir.mkdir(parents=True)
    
    # Framework Prompt
    framework_options = ["Puro CSS", "Tailwind CSS", "Bootstrap (SCSS)"]
    console.print("\n[yellow]¿Qué framework CSS vas a utilizar?[/]")
    for idx, fOpt in enumerate(framework_options):
        console.print(f"  [cyan]{idx+1}. {fOpt}[/]")
    f_choice = Prompt.ask("[yellow]Elige (1-3)[/]", default="1")
    try:
        framework = framework_options[int(f_choice) - 1]
    except:
        framework = "Puro CSS"

    # 1. Manifest
    priority = 10
    defines_structure = False
    
    if type == "CORE_LAYOUT":
        priority = 90
        defines_structure = True
    elif type == "FULL_OVERHAUL":
        priority = 100
        defines_structure = True
    elif type == "WIDGET_SKIN":
        priority = 50

    manifest = {
        "name": name,
        "version": "1.0.0",
        "theme_type": type,
        "framework": framework,
        "priority_level": priority,
        "defines_structure": defines_structure
    }
    
    with open(theme_dir / "composite.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

    # 2. Framework Scaffolding
    if framework == "Tailwind CSS":
        # Tailwind Boilerplate
        tw_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../../**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        kosBg: 'var(--kos-bg-main)',
        kosText: 'var(--kos-text-main)',
        kosAccent: 'var(--kos-accent)'
      }
    },
  },
  plugins: [],
}"""
        with open(theme_dir / "tailwind.config.js", "w", encoding="utf-8") as f:
            f.write(tw_config)
            
        with open(theme_dir / "style.css", "w", encoding="utf-8") as f:
            f.write("@tailwind base;\n@tailwind components;\n@tailwind utilities;\n")
            
        with open(theme_dir / "package.json", "w", encoding="utf-8") as f:
            pkg = {
                "name": clean_name,
                "scripts": { "build": "npx tailwindcss -i ./style.css -o ./dist.css --minify" },
                "devDependencies": { "tailwindcss": "^3.0.0" }
            }
            json.dump(pkg, f, indent=4)
            
    elif framework == "Bootstrap (SCSS)":
        # Bootstrap Boilerplate
        scss_content = f"""/* KrystalOS Bootstrap Override */
$primary: var(--kos-accent);
$body-bg: var(--kos-bg-main);
$body-color: var(--kos-text-main);

@import "bootstrap";
"""
        with open(theme_dir / "style.scss", "w", encoding="utf-8") as f:
            f.write(scss_content)
        
        with open(theme_dir / "package.json", "w", encoding="utf-8") as f:
            pkg = {
                "name": clean_name,
                "scripts": { "build": "npx sass style.scss dist.css --no-source-map" },
                "devDependencies": { "sass": "^1.0.0", "bootstrap": "^5.0.0" }
            }
            json.dump(pkg, f, indent=4)

    else:
        # Puro CSS Boilerplate
        css_content = f"/* KrystalOS Theme: {name} | Type: {type} */\n\n"
        if type == "COLOR_PALETTE":
            css_content += ":root {\n    --kos-primary: #8b5cf6;\n    --kos-bg-main: #0f172a;\n    --kos-text-main: #f8fafc;\n}\n"
        elif type == "CORE_LAYOUT":
            css_content += "body {\n    display: grid;\n    grid-template-areas: \n        \"krystal-taskbar krystal-desktop\"\n        \"krystal-taskbar krystal-notifications\";\n    grid-template-columns: 80px 1fr;\n    grid-template-rows: 1fr auto;\n}\n.krystal-taskbar { flex-direction: column; }\n"
        elif type == "WIDGET_SKIN":
            css_content += ".kos-widget-frame {\n    border-radius: 24px;\n    box-shadow: 0 10px 30px rgba(0,0,0,0.3);\n    border: 1px solid rgba(255, 255, 255, 0.1);\n}\n"
        else:
            css_content += "/* Escribe tus reglas CSS aquí... */\n"

        with open(theme_dir / "style.css", "w", encoding="utf-8") as f:
            f.write(css_content)

    console.print(f"\n[green]✓ Tema Modular '{name}' andamiado exitosamente.[/]")
    console.print(f"Directorio: [cyan]{theme_dir}[/]")
    console.print(f"Framework: [magenta]{framework}[/]")


def _generate_theme_lab(theme_name: str) -> None:
    """Generate a Mini-OS Showcase Lab (lab-env/) for a standalone Theme."""
    from pathlib import Path
    from rich.panel import Panel
    from rich.prompt import Confirm

    lab_dir  = Path.cwd() / theme_name / "lab-env"
    lab_dir.mkdir(parents=True, exist_ok=True)

    # ── live-injector.js — CSS hot reload via href cache-bust  ──────────────
    injector_js = """
/**
 * KrystalOS Mini-OS Lab — live-injector.js
 * Cache-busts the theme stylesheet href every 1500ms so CSS changes
 * are reflected in showcase.html without a page reload.
 */
(function () {
  'use strict';
  const LINK_ID = 'theme-link';
  const INTERVAL = 1500;

  const badge = document.createElement('div');
  badge.id = '__kos-hot-badge';
  badge.textContent = '\u26a1 HOT RELOAD';
  Object.assign(badge.style, {
    position:'fixed', bottom:'12px', left:'12px', zIndex:'99999',
    background:'rgba(0,255,204,0.15)', border:'1px solid #00FFCC',
    color:'#00FFCC', fontSize:'10px', fontWeight:'700',
    padding:'4px 10px', borderRadius:'20px', fontFamily:'monospace',
    letterSpacing:'0.06em',
  });
  document.addEventListener('DOMContentLoaded', () => document.body.appendChild(badge));

  setInterval(() => {
    const link = document.getElementById(LINK_ID);
    if (!link) return;
    const base = link.href.split('?')[0];
    link.href = base + '?v=' + Date.now();
    badge.style.opacity = '1';
    setTimeout(() => { badge.style.opacity = '0.5'; }, 300);
  }, INTERVAL);

  console.log('[LiveInjector] \u26a1 CSS Hot Reload activo.');
})();
"""
    (lab_dir / "live-injector.js").write_text(injector_js, encoding="utf-8")

    # ── showcase.html — Full KrystalOS fake layout ───────────────────────
    showcase_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>KrystalOS — {theme_name} Showcase</title>
  <!-- Developer's theme sheet (live-injected) -->
  <link id="theme-link" rel="stylesheet" href="../style.css">
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    :root{{
      /* KrystalOS Design Tokens (overridden by your theme) */
      --kos-bg-primary:#0f0c29;
      --kos-bg-secondary:rgba(255,255,255,0.04);
      --kos-surface:rgba(255,255,255,0.07);
      --kos-border:rgba(255,255,255,0.1);
      --kos-accent:#00FFCC;
      --kos-accent2:#7C3AED;
      --kos-text-main:rgba(255,255,255,0.85);
      --kos-text-dim:rgba(255,255,255,0.4);
      --kos-radius:16px;
      --kos-shadow:0 8px 32px rgba(0,0,0,0.4);
    }}
    html,body{{height:100%;background:var(--kos-bg-primary);color:var(--kos-text-main);font-family:system-ui,sans-serif}}

    /* ─ Layout ─────────────────────── */
    .kos-shell{{display:grid;grid-template-rows:48px 1fr;grid-template-columns:220px 1fr;height:100vh}}
    nav.kos-navbar{{
      grid-column:1/-1;display:flex;align-items:center;gap:12px;
      background:var(--kos-bg-secondary);border-bottom:1px solid var(--kos-border);
      padding:0 20px;
    }}
    nav.kos-navbar .logo{{font-size:15px;font-weight:800;letter-spacing:-.02em;color:var(--kos-accent)}}
    nav.kos-navbar .nav-links{{display:flex;gap:20px;margin-left:auto}}
    nav.kos-navbar .nav-links a{{color:var(--kos-text-dim);text-decoration:none;font-size:13px;transition:color .2s}}
    nav.kos-navbar .nav-links a:hover{{color:var(--kos-text-main)}}

    aside.kos-sidebar{{
      background:var(--kos-surface);border-right:1px solid var(--kos-border);
      padding:16px 12px;display:flex;flex-direction:column;gap:4px;
    }}
    .sidebar-item{{padding:8px 12px;border-radius:10px;font-size:13px;color:var(--kos-text-dim);cursor:pointer;transition:all .2s}}
    .sidebar-item:hover,.sidebar-item.active{{background:rgba(255,255,255,.06);color:var(--kos-text-main)}}
    .sidebar-item.active{{border-left:2px solid var(--kos-accent)}}

    main.kos-desktop{{padding:20px;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;align-content:start;overflow-y:auto}}

    /* ─ Widget Base ─────────────────── */
    .kos-widget{{
      background:var(--kos-surface);
      border:1px solid var(--kos-border);
      border-radius:var(--kos-radius);
      box-shadow:var(--kos-shadow);
      padding:18px;
      display:flex;flex-direction:column;gap:10px;
    }}
    .kos-widget .widget-header{{display:flex;align-items:center;gap:8px}}
    .kos-widget .widget-icon{{font-size:20px}}
    .kos-widget .widget-title{{font-size:13px;font-weight:700;color:var(--kos-text-main)}}
    .kos-widget .widget-subtitle{{font-size:11px;color:var(--kos-text-dim)}}

    /* ─ Widget A: Text ───────────────── */
    .widget-a p{{font-size:13px;color:var(--kos-text-main);line-height:1.6}}
    .kos-chip{{display:inline-block;background:rgba(0,255,204,0.1);color:var(--kos-accent);border-radius:20px;padding:2px 10px;font-size:10px;font-weight:700;border:1px solid rgba(0,255,204,0.25)}}

    /* ─ Widget B: Form ───────────────── */
    .widget-b input{{width:100%;background:rgba(0,0,0,.25);border:1px solid var(--kos-border);border-radius:8px;padding:7px 10px;color:var(--kos-text-main);font-size:12px;outline:none}}
    .widget-b input:focus{{border-color:var(--kos-accent)}}
    .kos-btn{{padding:7px 16px;border-radius:10px;border:none;background:var(--kos-accent);color:#000;font-weight:700;font-size:12px;cursor:pointer;align-self:flex-start;transition:opacity .2s}}
    .kos-btn:hover{{opacity:.8}}

    /* ─ Widget C: Table ──────────────── */
    .widget-c table{{width:100%;border-collapse:collapse;font-size:12px}}
    .widget-c th{{color:var(--kos-text-dim);font-weight:600;text-align:left;padding:4px 8px;border-bottom:1px solid var(--kos-border)}}
    .widget-c td{{padding:6px 8px;color:var(--kos-text-main)}}
    .widget-c tr:hover td{{background:rgba(255,255,255,.03)}}
    .dot{{width:8px;height:8px;border-radius:50%;display:inline-block}}
    .dot.green{{background:#22c55e}}.dot.yellow{{background:#eab308}}.dot.red{{background:#ef4444}}
  </style>
</head>
<body>
  <div class="kos-shell">

    <!-- Navbar -->
    <nav class="kos-navbar">
      <span class="logo">🔷 KrystalOS</span>
      <div class="nav-links">
        <a href="#">Dashboard</a>
        <a href="#">Widgets</a>
        <a href="#">Themes</a>
        <a href="#">Settings</a>
      </div>
    </nav>

    <!-- Sidebar -->
    <aside class="kos-sidebar">
      <div class="sidebar-item active">🏠 Inicio</div>
      <div class="sidebar-item">🧩 Widgets</div>
      <div class="sidebar-item">🎨 Temas</div>
      <div class="sidebar-item">📊 Analytics</div>
      <div class="sidebar-item">⚙️ Ajustes</div>
    </aside>

    <!-- Desktop / Widget Grid -->
    <main class="kos-desktop">

      <!-- Widget A: Texto -->
      <div class="kos-widget widget-a">
        <div class="widget-header">
          <span class="widget-icon">📝</span>
          <div>
            <div class="widget-title">Widget de Texto</div>
            <div class="widget-subtitle">Contenido dinámico</div>
          </div>
        </div>
        <p>Este widget muestra contenido usando <code>--kos-text-main</code>.
           Es ideal para noticias, logs o estados del sistema.</p>
        <span class="kos-chip">ONLINE</span>
      </div>

      <!-- Widget B: Formulario -->
      <div class="kos-widget widget-b">
        <div class="widget-header">
          <span class="widget-icon">💬</span>
          <div>
            <div class="widget-title">Widget de Formulario</div>
            <div class="widget-subtitle">Input / Output</div>
          </div>
        </div>
        <input type="text" placeholder="Nombre de usuario..." />
        <input type="email" placeholder="Email..." />
        <button class="kos-btn">➕ Agregar Usuario</button>
      </div>

      <!-- Widget C: Tabla -->
      <div class="kos-widget widget-c">
        <div class="widget-header">
          <span class="widget-icon">📊</span>
          <div>
            <div class="widget-title">Widget de Datos</div>
            <div class="widget-subtitle">Data Table Demo</div>
          </div>
        </div>
        <table>
          <thead>
            <tr><th>Nombre</th><th>Estado</th><th>Score</th></tr>
          </thead>
          <tbody>
            <tr><td>Módulo Alpha</td><td><span class="dot green"></span> Activo</td><td>98%</td></tr>
            <tr><td>Módulo Beta</td><td><span class="dot yellow"></span> Espera</td><td>72%</td></tr>
            <tr><td>Módulo Gamma</td><td><span class="dot red"></span> Error</td><td>14%</td></tr>
          </tbody>
        </table>
      </div>

    </main>
  </div>
  <script src="live-injector.js"></script>
</body>
</html>"""
    (lab_dir / "showcase.html").write_text(showcase_html, encoding="utf-8")

    console.print(
        Panel(
            f"[green]✓ Theme Showcase Lab generado en:[/] [cyan]{lab_dir}[/]\n"
            f"  • [yellow]showcase.html[/] — Layout completo con Navbar, Sidebar y 3 Dummy Widgets\n"
            f"  • [yellow]live-injector.js[/] — CSS Hot Reload cada 1.5s (no recarga la página)",
            title="🎨 Theme Lab listo",
            border_style="cyan",
        )
    )

    # CLI Server Prompt
    if Confirm.ask("🧪 ¿Deseas iniciar el Mini-KrystalOS Server para probar tu tema ahora?", default=False):
        import webbrowser, subprocess
        console.print("[cyan]Sirviendo en http://localhost:8080/showcase.html ...[/]")
        webbrowser.open("http://localhost:8080/showcase.html")
        subprocess.run(["python", "-m", "http.server", "8080", "--directory", str(lab_dir)])
