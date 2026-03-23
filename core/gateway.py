"""
KrystalOS — core/gateway.py
PHASE 2 STUB: Dynamic port mapper for multi-version PHP CGI runtimes.

This module will be fully implemented in Phase 2 (Gateway).
It exposes the PortMapper interface so dependent code can be written
against the contract today.
"""

from __future__ import annotations

# Future Phase 2 imports (uncomment when implementing):
# import socket
# from dataclasses import dataclass, field

_BASE_PORT = 9000  # PHP-FPM base port; each version gets an offset


class PortMapper:
    """
    Maps (language, version) pairs to deterministic local ports.

    Phase 2 will:
      - Allocate ephemeral ports from the OS.
      - Manage a process registry keyed by port.
      - Expose a REST micro-gateway on a fixed control port.

    Current behaviour: raises NotImplementedError to signal stub status.
    """

    def __init__(self) -> None:
        # TODO (Phase 2): initialise a persistent registry (SQLite / JSON)
        self._registry: dict[str, int] = {}

    def map_port(self, language: str, version: str) -> int:
        """
        Return a stable port number for the given runtime.

        Args:
            language: e.g. "php"
            version:  e.g. "8.2", "5.6"

        Returns:
            int: allocated port number

        Raises:
            NotImplementedError: until Phase 2 is implemented.
        """
        raise NotImplementedError(
            "PortMapper.map_port() — Phase 2 not yet implemented. "
            f"Requested: {language}@{version}"
        )

    def release_port(self, port: int) -> None:
        """Free a previously allocated port. Phase 2 stub."""
        raise NotImplementedError("PortMapper.release_port() — Phase 2 stub.")

    def list_active(self) -> dict[str, int]:
        """Return all active (runtime → port) mappings. Phase 2 stub."""
        return dict(self._registry)
