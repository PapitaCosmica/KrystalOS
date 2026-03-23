"""
KrystalOS — core/gateway.py
Phase 2: FastAPI Smart Proxy & Widget Bridge

Routes:
  GET/POST /api/{widget_name}/{path:path}
    → PHP    : spawn php-cgi subprocess, pipe FCGIlike over HTTP
    → Python : dynamically import routes.py and mount its APIRouter
    → JS/Node: spawn node subprocess, proxy via httpx

Resource management:
  - Lazy Loading: processes start on first request
  - Zombie Prevention: idle sweeper kills processes after IDLE_TIMEOUT seconds
  - GZip middleware applied at the app level (see main.py)
  - Path Traversal: all sub-paths validated via discovery.validate_proxy_path
"""

from __future__ import annotations

import asyncio
import importlib.util
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import Response, FileResponse

from core.discovery import WidgetRegistry, WidgetEntry, validate_proxy_path
from core.schema import SupportedLanguage
from shared.utils import get_php_executable, get_node_executable

logger = logging.getLogger("krystal.gateway")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IDLE_TIMEOUT = 30       # seconds before an idle subprocess is killed
SWEEP_INTERVAL = 10     # seconds between zombie sweeper runs
PHP_BASE_PORT = 9100    # first port allocated to php-cgi instances
NODE_BASE_PORT = 9200   # first port allocated to node instances

# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------

def build_gateway_router(registry: WidgetRegistry) -> APIRouter:
    """
    Build and return the FastAPI APIRouter for the gateway.
    Called once at startup after discovery.
    """
    router = APIRouter(prefix="/api", tags=["gateway"])

    # Mount Python widget routers dynamically
    _mount_python_widgets(router, registry)

    # Generic catch-all proxy for PHP and Node
    @router.api_route(
        "/{widget_name}/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    )
    async def proxy(widget_name: str, path: str, request: Request) -> Response:
        entry = registry.get(widget_name)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"Widget '{widget_name}' not found.")

        language = entry.manifest.runtime.language

        # Path traversal guard
        try:
            resolved_path = validate_proxy_path(entry, path)
        except ValueError as exc:
            logger.warning("Path traversal blocked for [%s]: %s", widget_name, exc)
            raise HTTPException(status_code=400, detail=str(exc))

        entry.last_used = time.time()

        # If it's an existing static asset (e.g. ui.html, css, js), serve it directly
        if resolved_path.is_file():
            return FileResponse(resolved_path)

        if language == SupportedLanguage.PHP:
            return await _proxy_php(entry, path, request)
        elif language in (SupportedLanguage.JAVASCRIPT, SupportedLanguage.NODE):
            return await _proxy_node(entry, path, request)
        else:
            raise HTTPException(
                status_code=501,
                detail=f"Language '{language}' has no proxy handler for dynamic requests to /{path}.",
            )

    return router


# ---------------------------------------------------------------------------
# Python — Dynamic Router Mount
# ---------------------------------------------------------------------------

def _mount_python_widgets(router: APIRouter, registry: WidgetRegistry) -> None:
    """
    For each Python widget that ships a routes.py, import it and include
    its FastAPI APIRouter under /api/<name>/.
    """
    for entry in registry.all():
        if entry.manifest.runtime.language != SupportedLanguage.PYTHON:
            continue

        routes_file = entry.widget_dir / "routes.py"
        if not routes_file.exists():
            logger.debug("[%s] No routes.py found — skipping Python mount.", entry.manifest.name)
            continue

        try:
            widget_router = _import_widget_router(entry.manifest.name, routes_file)
            router.include_router(
                widget_router,
                prefix=f"/{entry.manifest.name}",
            )
            entry.last_used = time.time()
            logger.info("[%s] ✓ Python routes mounted at /api/%s/", entry.manifest.name, entry.manifest.name)
        except Exception as exc:
            logger.error("[%s] Failed to mount Python routes: %s", entry.manifest.name, exc)


def _import_widget_router(widget_name: str, routes_file: Path) -> APIRouter:
    """
    Dynamically import routes.py from a widget folder and return its `router`
    (expected to be an `APIRouter` instance).
    """
    module_name = f"widget_{widget_name}_routes"
    spec = importlib.util.spec_from_file_location(module_name, str(routes_file))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec from {routes_file}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    if not hasattr(module, "router"):
        raise AttributeError(
            f"routes.py in widget '{widget_name}' must define a FastAPI `router` (APIRouter)."
        )
    return module.router


# ---------------------------------------------------------------------------
# PHP — Lazy subprocess via php-cgi
# ---------------------------------------------------------------------------

async def _proxy_php(entry: WidgetEntry, path: str, request: Request) -> Response:
    """
    Proxy a request to a PHP widget via php-cgi.
    Starts the php-cgi process on demand and caches it in the entry.
    """
    if entry.process is None or entry.process.returncode is not None:
        port = _next_available_port(PHP_BASE_PORT)
        entry.port = port
        
        php_path = get_php_executable()
        php_cgi = php_path if os.path.isabs(php_path) else (shutil.which(php_path) or shutil.which("php"))
        
        if not php_cgi:
            raise HTTPException(status_code=503, detail="php-cgi binary not found in PATH or portable /bin.")

        env = {
            **os.environ,
            "PHP_FCGI_CHILDREN": "1",
            "PHP_FCGI_MAX_REQUESTS": "500",
        }

        logger.info("[%s] Starting php-cgi on port %d", entry.manifest.name, port)
        entry.process = await asyncio.create_subprocess_exec(
            php_cgi, "-b", f"127.0.0.1:{port}",
            cwd=str(entry.widget_dir),
            env=env,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.sleep(0.3)  # Brief wait for process to bind

    # Build CGI environment and forward via httpx
    body = await request.body()
    index_php = entry.widget_dir / "index.php"

    cgi_env = {
        "REQUEST_METHOD": request.method,
        "SCRIPT_FILENAME": str(index_php),
        "SCRIPT_NAME": f"/{path}",
        "REQUEST_URI": f"/{path}",
        "QUERY_STRING": str(request.url.query),
        "CONTENT_TYPE": request.headers.get("content-type", ""),
        "CONTENT_LENGTH": str(len(body)),
        "SERVER_SOFTWARE": "KrystalOS/2.0",
        "GATEWAY_INTERFACE": "CGI/1.1",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "HTTP_HOST": "localhost",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method=request.method,
                url=f"http://127.0.0.1:{entry.port}/{path}",
                headers={**dict(request.headers), **cgi_env},
                content=body,
            )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
            media_type=resp.headers.get("content-type", "text/html"),
        )
    except Exception as exc:
        logger.error("[%s] PHP proxy error: %s", entry.manifest.name, exc)
        raise HTTPException(status_code=502, detail=f"PHP widget error: {exc}")


# ---------------------------------------------------------------------------
# Node — Lazy subprocess proxy
# ---------------------------------------------------------------------------

async def _proxy_node(entry: WidgetEntry, path: str, request: Request) -> Response:
    """
    Proxy a request to a Node.js widget.
    Starts `node index.js` on demand on a dynamic port.
    """
    if entry.process is None or entry.process.returncode is not None:
        port = _next_available_port(NODE_BASE_PORT)
        entry.port = port
        
        node_path = get_node_executable()
        node_bin = node_path if os.path.isabs(node_path) else shutil.which(node_path)
        
        if not node_bin:
            raise HTTPException(status_code=503, detail="node binary not found in PATH or portable /bin.")

        logger.info("[%s] Starting node on port %d", entry.manifest.name, port)
        entry.process = await asyncio.create_subprocess_exec(
            node_bin, "index.js",
            cwd=str(entry.widget_dir),
            env={**os.environ, "PORT": str(port)},
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.sleep(0.5)

    body = await request.body()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method=request.method,
                url=f"http://127.0.0.1:{entry.port}/{path}",
                headers=dict(request.headers),
                content=body,
            )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
    except Exception as exc:
        logger.error("[%s] Node proxy error: %s", entry.manifest.name, exc)
        raise HTTPException(status_code=502, detail=f"Node widget error: {exc}")


# ---------------------------------------------------------------------------
# Zombie Sweeper
# ---------------------------------------------------------------------------

async def zombie_sweeper(registry: WidgetRegistry) -> None:
    """
    Background asyncio task — kills idle widget processes after IDLE_TIMEOUT.
    Runs every SWEEP_INTERVAL seconds.
    """
    while True:
        await asyncio.sleep(SWEEP_INTERVAL)
        now = time.time()
        for entry in registry.all():
            if entry.process is None:
                continue
            if entry.process.returncode is not None:
                entry.process = None
                continue
            if entry.last_used and (now - entry.last_used) > IDLE_TIMEOUT:
                logger.info(
                    "[%s] Idle timeout — terminating process (pid=%s)",
                    entry.manifest.name,
                    entry.process.pid,
                )
                try:
                    entry.process.terminate()
                    await asyncio.wait_for(entry.process.wait(), timeout=3.0)
                except Exception:
                    entry.process.kill()
                finally:
                    entry.process = None
                    entry.port = None


# ---------------------------------------------------------------------------
# Port helpers
# ---------------------------------------------------------------------------

_used_ports: set[int] = set()

def _next_available_port(base: int) -> int:
    """Return the next unused port starting from *base*."""
    port = base
    while port in _used_ports:
        port += 1
    _used_ports.add(port)
    return port
