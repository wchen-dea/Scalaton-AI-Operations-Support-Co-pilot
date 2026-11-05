"""Log Agent — reads permitted workflow/Spark execution metadata (read-only)."""

from __future__ import annotations

from ..adapters.diagnostics import DiagnosticsAdapter
from ..schemas.events import IncidentEvent


class LogAgent:
    """Reads governed diagnostics; it cannot write production data (`tech-arch §4.3`)."""

    def __init__(self, diagnostics: DiagnosticsAdapter) -> None:
        self._diagnostics = diagnostics

    def collect(self, incident: IncidentEvent) -> list[str]:
        return self._diagnostics.fetch(incident=incident)
