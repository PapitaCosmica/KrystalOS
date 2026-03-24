"""
KrystalOS — cli/system_profiler.py
v1.1.0-beta (The Scout) Sprint
Detects system hardware resources, RAM, CPU cores, and classifies 
the environment automatically as LITE or PRO.
"""

from __future__ import annotations

import json
import os
import psutil
from pathlib import Path
from pydantic import BaseModel
from shared.utils import ensure_krystal_project


class EnvState(BaseModel):
    environment: str
    ram_gb: float
    cores: int


def profile_system() -> EnvState:
    """
    Profiles the host machine and writes `.krystal/env_state.json`.
    Returns an EnvState object with 'LITE' or 'PRO' classifications.
    Support for KRYSTAL_FORCE_LITE=1 mockup testing.
    """
    try:
        project_root = ensure_krystal_project()
    except FileNotFoundError:
        # Fallback if executing outside a project folder
        project_root = Path.cwd()

    krystal_dir = project_root / ".krystal"
    krystal_dir.mkdir(parents=True, exist_ok=True)
    state_file = krystal_dir / "env_state.json"

    # Hardware Detection
    mem = psutil.virtual_memory()
    total_ram_gb = round(mem.total / (1024**3), 2)
    cores = psutil.cpu_count(logical=True) or 1

    # Logic LITE vs PRO
    # If forced by environment variable or naturally below 4.0 GB
    force_lite = os.environ.get("KRYSTAL_FORCE_LITE") == "1"
    
    if force_lite or total_ram_gb < 4.0:
        environment = "LITE"
    else:
        environment = "PRO"

    state = EnvState(
        environment=environment,
        ram_gb=total_ram_gb,
        cores=cores
    )

    # Persist File
    state_file.write_text(json.dumps(state.model_dump(), indent=2), encoding="utf-8")
    return state


def get_cached_env_state() -> EnvState:
    """
    Loads `.krystal/env_state.json` without re-profiling immediately,
    or profiles the system if the file doesn't exist yet.
    """
    try:
        project_root = ensure_krystal_project()
        state_file = project_root / ".krystal" / "env_state.json"
        
        if state_file.exists():
            data = json.loads(state_file.read_text("utf-8"))
            return EnvState(**data)
            
        return profile_system()
        
    except Exception:
        # Failsafe fallback
        return profile_system()
