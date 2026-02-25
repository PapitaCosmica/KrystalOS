import os
import json
import importlib
import sys
from fastapi import FastAPI, APIRouter
import importlib.util

WIDGETS_DIR = os.path.join(os.getcwd(), "widgets")

def discover_and_mount_widgets(app: FastAPI):
    """
    Scans the widgets directory for valid KrystalOS widgets and mounts
    their FastAPI routers dynamically based on config.json.
    Also exposes a global /api/widgets/configs endpoint for the frontend.
    """
    if not os.path.exists(WIDGETS_DIR):
        print(f"[Autodiscovery] Directory {WIDGETS_DIR} not found. Skipping.")
        return

    print("[Autodiscovery] Scanning for widgets...")
    loaded_configs = {}
    
    for item in os.listdir(WIDGETS_DIR):
        widget_path = os.path.join(WIDGETS_DIR, item)
        if os.path.isdir(widget_path):
            config_path = os.path.join(widget_path, "config.json")
            if os.path.exists(config_path):
                # Valid widget found
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    
                    widget_name = config.get("name", item)
                    api_prefix = config.get("api_prefix", f"/api/widget/{item}")
                    
                    # Store config for the frontend
                    loaded_configs[item] = config
                    
                    print(f"  -> Discovered widget: {widget_name} (Prefix: {api_prefix})")
                    
                    # Mount routes
                    routes_path = os.path.join(widget_path, "routes.py")
                    if os.path.exists(routes_path):
                        # Safely import the module dynamically
                        module_name = f"widgets.{item}.routes"
                        spec = importlib.util.spec_from_file_location(module_name, routes_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = module
                            spec.loader.exec_module(module)
                            
                            # Expecting a router attribute in routes.py
                            if hasattr(module, "router"):
                                app.include_router(module.router, prefix=api_prefix, tags=[widget_name])
                                print(f"     Mounted router for {widget_name}")
                            else:
                                print(f"     Warning: {routes_path} has no 'router' attribute.")
                except Exception as e:
                    print(f"[Autodiscovery] Error loading widget {item}: {e}")

    # Mount a global router to expose all configs to the frontend OS
    meta_router = APIRouter()
    @meta_router.get("/configs")
    def get_all_widget_configs():
        """Returns all discovered widget configurations"""
        return loaded_configs
    
    app.include_router(meta_router, prefix="/api/widgets", tags=["system"])
    print(f"[Autodiscovery] Exposed {len(loaded_configs)} widget configs at /api/widgets/configs")

