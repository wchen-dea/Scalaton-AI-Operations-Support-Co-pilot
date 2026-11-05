"""Jira connector stub (`design §4.3`)."""

from __future__ import annotations

from .base import Connector, ConnectorResult


class JiraConnector(Connector):
    system = "jira"

    def _do_read(self, *, correlation_id: str, operation: str, **params: object) -> ConnectorResult:
        return ConnectorResult(ok=True, data={"operation": operation})

    def _do_write(self, *, correlation_id: str, action_type: str, idempotency_key: str,
                  **params: object) -> ConnectorResult:
        key = f"DATAENG-{abs(hash(idempotency_key)) % 10000:04d}"
        return ConnectorResult(
            ok=True, external_id=key, data={"url": f"https://jira.example/browse/{key}"}
        )
