"""ServiceNow connector stub (`design §4.1`, `§4.4`)."""

from __future__ import annotations

from .base import Connector, ConnectorResult


class ServiceNowConnector(Connector):
    system = "servicenow"

    def _do_read(self, *, correlation_id: str, operation: str, **params: object) -> ConnectorResult:
        return ConnectorResult(ok=True, data={"operation": operation, "status": "ok"})

    def _do_write(self, *, correlation_id: str, action_type: str, idempotency_key: str,
                  **params: object) -> ConnectorResult:
        # e.g. write work notes or submit a change request
        external_id = f"CHG00{abs(hash(idempotency_key)) % 100000:05d}"
        return ConnectorResult(ok=True, external_id=external_id, data={"action_type": action_type})
