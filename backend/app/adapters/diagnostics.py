"""Unity Catalog system-table diagnostics adapter (`tech-arch §4.3`, `design §6`).

Reads permitted workflow/execution metadata read-only (the Log Agent boundary). The
stub returns fixed diagnostics so no live Unity Catalog access is required.
"""

from __future__ import annotations

from typing import Protocol

from ..schemas.events import IncidentEvent


class DiagnosticsAdapter(Protocol):
    def fetch(self, *, incident: IncidentEvent) -> list[str]: ...


class StubDiagnosticsAdapter:
    def fetch(self, *, incident: IncidentEvent) -> list[str]:
        return [
            f"system.workflows: last run of {incident.service} failed with non-zero exit",
            "system.compute: executor OOM warning observed near failure time",
            "spark: AnalysisException — cannot resolve column 'order_ts'",
        ]
