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
Interactive wizard to scaffold a new widget. Generates `krystal.json` and basic language-specific scaffolding inside the `widgets/` folder.

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

---
**Desarrollado con ❤ por PapitaCosmica**
