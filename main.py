from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from internal.orchestrator.autodiscovery import discover_and_mount_widgets
from core.intelligence.routes import router as intelligence_router
from core.events.routes import router as events_router
from core.auth.routes import router as auth_router

app = FastAPI(
    title="KrystalOS API",
    description="Sistema Operativo Empresarial Basado en Widgets",
    version="0.1.0"
)

# Static files and Templates
app.mount("/public", StaticFiles(directory="public"), name="public")
templates = Jinja2Templates(directory="templates/layouts")

@app.get("/")
def serve_bento_desktop(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

# Mount Core Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(intelligence_router, prefix="/api/intelligence", tags=["Intelligence"])
app.include_router(events_router, prefix="", tags=["Events"])

# Discovery and mount process
discover_and_mount_widgets(app)

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "KrystalOS"}
