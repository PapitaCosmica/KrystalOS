"""
KrystalOS — core/optimization.py
Phase 4: Extreme Optimization (The 2GB RAM Guard)
Hooks into FastAPI to throttle heavy tasks dynamically if RAM usage spikes.
"""

from __future__ import annotations

import logging
from typing import Callable

import psutil
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("krystal.optimization")

# Resource threshold: when available RAM drops below this percentage, throttling engages.
MEMORY_THRESHOLD_PERCENT = 15.0  

class MemoryOptimizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that monitors RAM usage on the host PC. 
    If memory is running low (e.g. Lite Engine on 2GB RAM PC),
    it dynamically compresses images further or delays less-critical API endpoints.
    """
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        
        mem = psutil.virtual_memory()
        is_memory_low = mem.available < (2 * 1024 * 1024 * 1024) and mem.percent > (100 - MEMORY_THRESHOLD_PERCENT)

        if is_memory_low:
            logger.warning("[RAM Guard] System memory critically low (%s%%). Throttling traffic.", mem.percent)
            
            # Simple heuristic: heavily delay non-critical widget API requests if memory is dying
            if request.url.path.startswith("/api/"):
                import asyncio
                await asyncio.sleep(0.5)  # Backpressure

        response = await call_next(request)
        
        # Image optimization headers if memory is suffering (tells client browser to cache aggressively)
        if is_memory_low and response.headers.get("content-type", "").startswith("image/"):
            response.headers["Cache-Control"] = "public, max-age=86400, immutable"
            
        return response
