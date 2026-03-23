"""
KrystalOS — core/db.py
Phase 2: Persistencia Dual (Lite / Pro)

Configures SQLModel dynamically based on the project's krystal.config.json:
  Lite Mode -> SQLite (local file)
  Pro Mode  -> PostgreSQL (via KRYSTAL_DB_* env vars)
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from sqlmodel import Field, Session, SQLModel, create_engine
from shared.utils import ensure_krystal_project, load_config

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class WidgetEvent(SQLModel, table=True):
    """Base table for persisting KrystalOS events."""
    id: int | None = Field(default=None, primary_key=True)
    widget_name: str = Field(index=True)
    event_name: str = Field(index=True)
    payload: str = Field(default="{}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ---------------------------------------------------------------------------
# Engine Configuration
# ---------------------------------------------------------------------------

_engine = None

def get_engine() -> Any:
    """Return the configured SQLAlchemy engine, initializing it if necessary."""
    global _engine
    if _engine is not None:
        return _engine

    try:
        project_root = ensure_krystal_project()
        config = load_config(project_root / "krystal.config.json")
    except FileNotFoundError:
        config = {"default_mode": "native"}
        project_root = Path.cwd()

    mode = config.get("default_mode", "native")

    if mode == "docker":
        # Pro Mode - PostgreSQL
        db_user = os.getenv("KRYSTAL_DB_USER", "postgres")
        db_pass = os.getenv("KRYSTAL_DB_PASS", "postgres")
        db_host = os.getenv("KRYSTAL_DB_HOST", "localhost")
        db_name = os.getenv("KRYSTAL_DB_NAME", "krystal")
        
        database_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        _engine = create_engine(database_url, echo=False)
    else:
        # Lite Mode - SQLite
        db_path = project_root / ".krystal" / "krystal.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{db_path}"
        
        # connect_args essential for SQLite in multi-thread (FastAPI)
        _engine = create_engine(
            database_url, echo=False, connect_args={"check_same_thread": False}
        )

    # Automatically create tables if they don't exist
    SQLModel.metadata.create_all(_engine)
    
    return _engine

def get_session() -> Session:
    """Dependency provider for FastAPI routes to get a database session."""
    engine = get_engine()
    with Session(engine) as session:
        yield session
