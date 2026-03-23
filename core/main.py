"""
KrystalOS — core/main.py
Phase 2: FastAPI Entry Point (The Orchestrator)

Runs autodiscovery on startup, applies GZip compression, and serves:
  - GET /              -> Bento Grid Dashboard
  - GET /health        -> JSON Registry
  - /api/{widget}/*    -> Dynamic Proxy (PHP/Python/Node)
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from core.discovery import WidgetScanner, WidgetRegistry
from core.gateway import build_gateway_router, zombie_sweeper
from core.event_manager import router as event_router
from shared.utils import ensure_krystal_project

# ---------------------------------------------------------------------------
# Setup Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("krystal.core")

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
registry = WidgetRegistry()

# Assume we run inside a Krystal project during `krystal serve`
try:
    PROJECT_ROOT = ensure_krystal_project()
except FileNotFoundError:
    PROJECT_ROOT = Path.cwd()

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="KrystalOS",
    version="0.3.0",
    description="Modular orchestrator with realtime event bus.",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Serve Phase 3 Frontend bridge script
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")

@app.on_event("startup")
async def on_startup() -> None:
    """Startup routine: Discovery + route mounting + zombie sweeper."""
    logger.info("Initializing KrystalOS Orchestrator 🔷")
    
    # Run discovery engine
    scanner = WidgetScanner(PROJECT_ROOT / "widgets")
    fetched = scanner.scan()
    for w in fetched.all():
        registry.register(w)
        
    # Mount dynamic gateway routes
    gateway = build_gateway_router(registry)
    app.include_router(gateway)
    
    # Mount Phase 3 Event Bus
    app.include_router(event_router)

    # Start zombie sweeper task to kill idle processes
    asyncio.create_task(zombie_sweeper(registry))
    logger.info("Gateway router mounted. Zombie sweeper active. Event Bus online ⚡.")

@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Gracefully terminate background tasks and SQLite connections."""
    logger.info("KrystalOS Orchestrator shutting down...")
    try:
        from core.db import get_engine
        get_engine().dispose()
        logger.info("[DB] Database connections closed.")
    except Exception as e:
        logger.error(f"[DB] Error closing database: {e}")

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse, tags=["dashboard"])
async def dashboard(request: Request):
    """Render the Bento Grid dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "widgets": registry.summary()}
    )

@app.get("/health", tags=["system"])
async def health():
    """System heartbeat and discovered widgets."""
    return {
        "status": "ok",
        "registered_widgets": len(registry.names()),
        "registry": registry.summary()
    }
