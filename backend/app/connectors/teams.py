"""Microsoft Teams connector stub (`design §4.2`, `§4.4`).

Outbound only: posts Adaptive Cards. Inbound Teams actions arrive through the route
surface with a backend role re-check; Teams remains the authoritative approval surface
(plan decision D6).
"""

from __future__ import annotations

from .base import Connector, ConnectorResult


class TeamsConnector(Connector):
    system = "teams"

    def _do_read(self, *, correlation_id: str, operation: str, **params: object) -> ConnectorResult:
        return ConnectorResult(ok=True, data={"operation": operation})

    def _do_write(self, *, correlation_id: str, action_type: str, idempotency_key: str,
                  **params: object) -> ConnectorResult:
        return ConnectorResult(
            ok=True, external_id=f"card-{abs(hash(idempotency_key)) % 100000:05d}"
        )
