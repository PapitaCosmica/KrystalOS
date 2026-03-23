# Changelog

All notable changes to KrystalOS will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2026-03-23

### Added — Phase 1: Foundation & CLI

- **`krystal init <name>`** — scaffolds a full KrystalOS project directory tree
- **`krystal make:widget`** — interactive wizard to generate widgets with Pydantic-validated `krystal.json`, language starters (PHP / Python / JS / Node), and Tailwind Glassmorphism `ui.html`
- **`krystal doctor [--bundle]`** — hardware (RAM, CPU) and software (php, python, node, docker PATH) diagnostics with Lite Mode suggestion when RAM < 4 GB
- **`krystal install <url>`** — Phase 5 stub (GitHub sparse-clone widget registry)
- **`core/schema.py`** — Pydantic v2 `KrystalWidget` model for `krystal.json` standard
- **`core/gateway.py`** — `PortMapper` stub (Phase 2: dynamic PHP port mapping)
- **`core/event_manager.py`** — `EventManager` stub (Phase 3: WebSocket event bus)
- **`shared/utils.py`** — `load_config`, `save_config`, `ensure_krystal_project` helpers
- **`setup.py`** — `pip install -e .` entry-point registering `krystal` globally

---

## [Unreleased]

### Planned — Phase 2: Gateway
- Dynamic port mapper for multi-version PHP CGI runtimes

### Planned — Phase 3: Event Bus
- WebSocket-based inter-widget pub-sub via `EventManager`

### Planned — Phase 4: Lite Mode
- Portable binary bundles (`--bundle` flag on `krystal doctor`)

### Planned — Phase 5: Community
- GitHub sparse-clone widget registry via `krystal install`
