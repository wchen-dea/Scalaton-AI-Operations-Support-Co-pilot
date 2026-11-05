"""Application configuration.

The single settings surface for the backend. Values come from the environment and
secret references (`tech-arch §10`); no secrets are committed here. External writes
and live integrations are disabled by default so the scaffold runs with no live
dependencies (plan decisions D3, NFR-007).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from importlib.resources import files
from pathlib import Path


def _flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _default_frontend_dist() -> str:
    packaged_assets = Path(str(files("app") / "static"))
    if packaged_assets.is_dir():
        return str(packaged_assets)

    # Local source checkout fallback: backend/app/config.py -> repository root.
    return str(Path(__file__).resolve().parents[2] / "frontend" / "dist")


@dataclass(frozen=True)
class Settings:
    """Resolved backend configuration (`tech-arch §10` categories)."""

    # Runtime
    app_port: int
    frontend_dist: str

    # Integration toggles
    enable_external_writes: bool
    use_live_integrations: bool

    # Model / retrieval / data (names and timeouts only; never secrets)
    model_endpoint: str
    model_timeout_s: float
    vector_search_index: str
    uc_catalog: str
    uc_schema: str
    sql_warehouse_id: str

    # Reliability / rate limiting
    retry_max_attempts: int
    retry_base_delay_s: float
    request_timeout_s: float
    webhook_rate_limit_per_minute: int

    # Teams / approval policy
    teams_channel: str
    approval_policy: str

    # Webhook security
    webhook_allowed_sources: tuple[str, ...]
    webhook_timestamp_skew_s: int

    # MCP / Genie
    genie_space: str
    external_mcp_servers: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_env(cls) -> "Settings":
        external = os.environ.get("EXTERNAL_MCP_SERVERS", "")
        external_servers = tuple(s.strip() for s in external.split(",") if s.strip())
        allowed = os.environ.get("WEBHOOK_ALLOWED_SOURCES", "skybot,servicenow,jira")
        return cls(
            app_port=_int("DATABRICKS_APP_PORT", 8000),
            frontend_dist=os.environ.get("FRONTEND_DIST", _default_frontend_dist()),
            enable_external_writes=_flag("ENABLE_EXTERNAL_WRITES", False),
            use_live_integrations=_flag("USE_LIVE_INTEGRATIONS", False),
            model_endpoint=os.environ.get("MODEL_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct"),
            model_timeout_s=_float("MODEL_TIMEOUT_S", 30.0),
            vector_search_index=os.environ.get("VECTOR_SEARCH_INDEX", "ops.support.runbook_index"),
            uc_catalog=os.environ.get("UC_CATALOG", "system"),
            uc_schema=os.environ.get("UC_SCHEMA", "workflow"),
            sql_warehouse_id=os.environ.get("SQL_WAREHOUSE_ID", ""),
            retry_max_attempts=_int("RETRY_MAX_ATTEMPTS", 3),
            retry_base_delay_s=_float("RETRY_BASE_DELAY_S", 0.2),
            request_timeout_s=_float("REQUEST_TIMEOUT_S", 15.0),
            webhook_rate_limit_per_minute=_int("WEBHOOK_RATE_LIMIT_PER_MINUTE", 60),
            teams_channel=os.environ.get("TEAMS_CHANNEL", "ops-warroom"),
            approval_policy=os.environ.get("APPROVAL_POLICY", "teams"),
            webhook_allowed_sources=tuple(s.strip() for s in allowed.split(",") if s.strip()),
            webhook_timestamp_skew_s=_int("WEBHOOK_TIMESTAMP_SKEW_S", 300),
            genie_space=os.environ.get("GENIE_SPACE", "ops-support-genie"),
            external_mcp_servers=external_servers,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings, read once from the environment."""
    return Settings.from_env()
