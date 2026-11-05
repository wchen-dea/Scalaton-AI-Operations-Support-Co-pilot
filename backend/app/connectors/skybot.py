"""Skybot connector stub (`design §4.1`).

Skybot is an inbound incident source; the connector models read-only acknowledgement.
"""

from __future__ import annotations

from .base import Connector, ConnectorResult


class SkybotConnector(Connector):
    system = "skybot"

    def _do_read(self, *, correlation_id: str, operation: str, **params: object) -> ConnectorResult:
        return ConnectorResult(ok=True, data={"operation": operation})

    def _do_write(self, *, correlation_id: str, action_type: str, idempotency_key: str,
                  **params: object) -> ConnectorResult:
        return ConnectorResult(ok=True, external_id=None)
