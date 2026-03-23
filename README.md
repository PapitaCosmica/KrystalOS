# KrystalOS 🔷

> A modular micro-services orchestrator that runs PHP, Python and JavaScript widgets simultaneously on a Bento-Grid dashboard.

## Installation

```bash
pip install -e .
```

## CLI Commands (Phase 1)

| Command | Description |
|---|---|
| `krystal init <name>` | Scaffold a new KrystalOS project |
| `krystal make:widget` | Interactive widget generator |
| `krystal doctor` | System hardware & software diagnostics |
| `krystal install <url>` | *(Phase 5)* Install widget from GitHub |

## Quick Start

```bash
krystal init myproject
cd myproject
krystal make:widget
krystal doctor
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
| Phase 1 | Foundation & CLI *(current)* |
| Phase 2 | Gateway — dynamic PHP port mapping |
| Phase 3 | Event Bus — WebSocket EventManager |
| Phase 4 | Lite Mode — portable binary bundles |
| Phase 5 | Community — GitHub widget registry |
