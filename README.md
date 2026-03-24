# KrystalOS 🔷

> A modular micro-services orchestrator that runs PHP, Python and JavaScript widgets simultaneously on a Bento-Grid dashboard.

## Installation

```bash
pip install -e .
```

## 📖 Official Documentation
Read the complete guide and comprehensive manuals on how to use KrystalOS at the **[Official GitHub Wiki](https://github.com/PapitaCosmica/KrystalOS/wiki)**.

## CLI Command Reference (`krystal --help`)

### `krystal init [OPTIONS] [NAME]`
Scaffold a new KrystalOS project directory.
- `[NAME]`: Project directory name (default: `my_krystal_project`).

### `krystal make:widget`
Interactive wizard to scaffold a new widget. 
*v2.0.0-alpha Feature:* You can now generate standalone widgets with a built-in `krystal-mock.js` simulator to program in LiveServer anywhere in your filesystem.

### `krystal make:theme`
Interactive wizard to scaffold a Modular UI Theme layer (`CORE_LAYOUT`, `WIDGET_SKIN`, `COLOR_PALETTE`, etc.) generating a strictly prioritized `composite.json`. 
*v2.2.2 Feature:* Polyglot scaffolding support for pure CSS, Tailwind, or Bootstrap.

### `krystal deploy`
*v2.2.2 Feature:* Orchestrates the entire KrystalOS infrastructure into a Production-ready Docker Compose environment.

### `krystal post <target>`
*v2.2.2 Feature:* Packages your Widget, Mod, or Theme into a compressed `.kzip` for the ecosystem registry simulating an `npm publish`.

### `krystal env:set <LITE|PRO>`
*v2.2.3 Feature:* Forces the current Workspace's target profile. LITE enforces SQLite and resource ceilings; PRO unlocks Docker, PostgreSQL, and unlimited binaries.

### `krystal init <name>`
*v2.2.3 Feature:* Asks for LITE or PRO before scaffolding a new project and writes `target_env` into `krystal.config.json`.

### `krystal dev-server --lab <path>`
*v2.2.4 Feature:* Starts a WebSocket HMR (Hot Module Replacement) dev server for a Lab folder. CSS/HTML changes are injected surgically into Shadow DOM without refresh. JS/WASM changes restart only the relevant Web Worker.

### `krystal serve [COMMAND] [OPTIONS]`
The core gateway orchestrator and process manager.
- `krystal serve start [--port 8000]`: Boots up Uvicorn, launches the widget auto-discovery engine, and hosts the dashboard. Tracks PIDs.
- `krystal serve status`: Shows a live table of all running background subprocesses (PHP-CGI, Node, Gateway) and their exact memory footprints.
- `krystal serve destroy [--port 8000] [--force]`: Scans for the process occupying the port and safely terminates it.
- `krystal serve destroy --all`: Cleanly kills all known sub-children to free up RAM.

### `krystal bundle create [OPTIONS]`
*Phase 4 Feature:* Packages the framework for standalone distribution.
- `[--out|-o output_name.zip]`: Name of the generated zip archive. Automatically creates cryptographic hash verification.

### `krystal doctor [OPTIONS]`
Diagnostics assistant to detect installed environments (PHP, Python, Node, Docker) and evaluate resources.
- Analyzes CPU frequency and free memory.
- Suggests disabling CSS Glassmorphism if RAM < 2GB.
- Recommends the optimal Lite/Pro execution mode.
- `[--bundle]`: Prepares portable binaries.


## Quick Start

```bash
krystal init myproject
cd myproject
krystal make:widget
krystal doctor
krystal serve start
```

## `krystal.json` Schema

Every widget must contain a `krystal.json` at its root:

```json
{
  "name": "my-widget",
  "version": "0.1.0",
  "author": "you",
  "runtime": {
    "language": "python",
    "version": "3.11"
  },
  "ui": {
    "grid_size": { "w": 2, "h": 2 },
    "icon": "🔷",
    "theme_color": "#7C3AED"
  },
  "capabilities": {
    "events_emitted": ["widget:ready"],
    "events_subscribed": ["theme:change"]
  },
  "modes": {
    "native": true,
    "docker": false
  }
}
```

## Roadmap

| Phase | Focus |
|---|---|
| Phase 1 | Foundation & CLI ✅ |
| Phase 2 | Gateway — dynamic PHP port mapping ✅ |
| Phase 3 | Event Bus — WebSocket EventManager ✅ |
| Phase 4 | Lite Mode & Bundler — portable binary bundles ✅ |
| Phase 5 | Community — GitHub widget registry & Market ✅ |
| Phase 6 | The Factory — standalone dev & K-ZIP absorber ✅ |
| Phase 6.1 | Dependency Engine — Zero Data-Loss Auto-Migrator ✅ |
| Phase 7 | Modular UI Compositor — hot-swappable themes and Layouts ✅ |
| Phase 7.1 | The Krystal Lab — Zero-Config Standalone UI/Data Sandbox ✅ |
| Phase 7.2 | Interactive CLI — Polyglot WASM Scaffolder & Package Manager ✅ |
| Phase 7.3 | Environment Targeting — LITE/PRO Profiles, Dependency Registry & Hibernation ✅ |
| Phase 7.4 | Fluid UI & Off-Main-Thread — GridManager, ThreadBridge (Web Workers) & HMR ✅ |

---
**Desarrollado con ❤ por PapitaCosmica**
