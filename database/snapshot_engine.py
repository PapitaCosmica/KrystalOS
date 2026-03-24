"""
KrystalOS — database/snapshot_engine.py
Phase 7.5: Snapshot Archiver — Zero Data-Loss Backup Before Remove

Before any destructive Mod operation (uninstall, schema drop), this engine
exports all associated database rows to a compressed `.kss` archive.

A `.kss` file is a standard ZIP archive containing:
  - manifest.json  → metadata (mod_name, timestamp, tables, row counts)
  - [table_name].json → all rows of each associated table as a JSON array

Usage:
    engine = SnapshotEngine("mod-usuarios", db_path="database/krystal.db")
    snapshot_path = engine.run()
    # → "backups/archive/mod-usuarios_20260324_112627.kss"

─────────────────────────────────────────────────────────────
FUTURE RESTORATION PATH: krystal restore <snapshot_file>
─────────────────────────────────────────────────────────────
A future `krystal restore <file.kss>` command would:
    1. Open the .kss ZIP and read manifest.json.
    2. For each table entry, read [table].json and deserialize rows.
    3. Reconnect to the SQLite database.
    4. For each table, run:
           CREATE TABLE IF NOT EXISTS [table] (...)
           INSERT OR REPLACE INTO [table] VALUES (...)
    5. Confirm restoration row counts to the user.
    6. Emit krystal:mod-restored event for the frontend to re-register widgets.
─────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import json
import os
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

BACKUP_DIR = Path("backups") / "archive"


class SnapshotEngine:
    """
    Exports all rows associated with a named Mod from the SQLite database
    into a compressed .kss snapshot archive before remove operations.

    :param mod_name: The slug name of the Mod (e.g. "mod-usuarios").
    :param db_path:  Path to the KrystalOS sqlite database file.
    """

    def __init__(self, mod_name: str, db_path: str | Path = "database/krystal.db"):
        self.mod_name = mod_name.lower().replace(" ", "-")
        self.db_path  = Path(db_path)

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self) -> Path:
        """
        Execute snapshot: detect tables → export rows → write .kss archive.
        Returns the path to the created .kss file.
        Raises RuntimeError if the database is not found.
        """
        if not self.db_path.exists():
            raise RuntimeError(
                f"[SnapshotEngine] Database not found at: {self.db_path}\n"
                "Run `krystal init` or `krystal serve start` to initialize the database first."
            )

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        kss_filename = f"{self.mod_name}_{timestamp}.kss"
        kss_path     = BACKUP_DIR / kss_filename

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Creando snapshot de '{self.mod_name}'...", total=None)
            tables = self._detect_tables()
            snapshot_data = self._export_tables(tables)
            self._write_kss(kss_path, snapshot_data, timestamp, tables)
            progress.update(task, description="Snapshot completado.")

        total_rows = sum(len(rows) for rows in snapshot_data.values())
        console.print(
            f"\n[bold green]📦 Snapshot creado:[/] {kss_path}\n"
            f"   Tablas: [cyan]{len(tables)}[/]  |  Filas exportadas: [cyan]{total_rows}[/]"
        )
        return kss_path

    # ── Internal Helpers ──────────────────────────────────────────────────────

    def _detect_tables(self) -> list[str]:
        """
        Returns database tables associated with this Mod.
        Heuristic: tables named after the mod slug, or with a column `_mod_owner`.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in cursor.fetchall()]

        slug = self.mod_name.replace("-", "_")
        associated = []

        for table in all_tables:
            # Direct name match (e.g. "mod_usuarios_sessions")
            if slug in table.lower():
                associated.append(table)
                continue
            # Check for _mod_owner column tag
            try:
                cursor.execute(f"PRAGMA table_info(\"{table}\")")
                cols = [col[1] for col in cursor.fetchall()]
                if "_mod_owner" in cols:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM \"{table}\" WHERE _mod_owner=?",
                        (self.mod_name,)
                    )
                    count = cursor.fetchone()[0]
                    if count > 0:
                        associated.append(table)
            except sqlite3.OperationalError:
                pass

        conn.close()

        if not associated:
            console.print(f"[dim]No se encontraron tablas asociadas a '{self.mod_name}'. El snapshot estará vacío.[/]")

        return associated

    def _export_tables(self, tables: list[str]) -> dict[str, list]:
        """Reads all rows from each table and returns them as a dict of JSON-safe lists."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        result = {}

        for table in tables:
            try:
                cursor.execute(f"SELECT * FROM \"{table}\"")
                result[table] = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError as e:
                console.print(f"[yellow]⚠ No se pudo exportar '{table}': {e}[/]")
                result[table] = []

        conn.close()
        return result

    def _write_kss(
        self,
        kss_path: Path,
        snapshot_data: dict[str, list],
        timestamp: str,
        tables: list[str],
    ) -> None:
        """Writes the .kss archive (ZIP containing JSON files + manifest)."""
        manifest = {
            "kss_version": "1.0",
            "mod_name":    self.mod_name,
            "timestamp":   timestamp,
            "db_path":     str(self.db_path),
            "tables":      {
                table: len(rows)
                for table, rows in snapshot_data.items()
            },
        }

        with zipfile.ZipFile(kss_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # manifest.json
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            # One JSON file per table
            for table, rows in snapshot_data.items():
                zf.writestr(f"{table}.json", json.dumps(rows, indent=2, ensure_ascii=False, default=str))
