"""Shared dependency container for the orchestrator and agents.

Builds the adapter/connector/MCP/Genie/audit/dead-letter instances once. In the
scaffold these are the local stubs; live implementations replace them behind the same
interfaces when `USE_LIVE_INTEGRATIONS` is enabled (deferred — plan decision D3).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..adapters import (
    StubAIFunctionsAdapter,
    StubDiagnosticsAdapter,
    StubModelAdapter,
    StubVectorSearchAdapter,
)
from ..adapters.ai_functions import AIFunctionsAdapter
from ..adapters.diagnostics import DiagnosticsAdapter
from ..adapters.model import ModelAdapter
from ..adapters.vector_search import VectorSearchAdapter
from ..audit.store import AuditStore
from ..config import Settings
from ..connectors import (
    JiraConnector,
    ServiceNowConnector,
    SkybotConnector,
    TeamsConnector,
)
from ..mcp import GenieClient, MCPClient, StubGenieClient, build_registry
from ..observability.logging import get_logger
from ..reliability.deadletter import DeadLetterStore
from ..storage import Repositories

_log = get_logger("deps")


@dataclass
class Deps:
    settings: Settings
    repos: Repositories
    audit: AuditStore
    dead_letter: DeadLetterStore
    model: ModelAdapter
    vector_search: VectorSearchAdapter
    diagnostics: DiagnosticsAdapter
    ai_functions: AIFunctionsAdapter
    mcp: MCPClient
    genie: GenieClient
    servicenow: ServiceNowConnector
    jira: JiraConnector
    teams: TeamsConnector
    skybot: SkybotConnector

    @classmethod
    def build(cls, settings: Settings) -> "Deps":
        if settings.use_live_integrations:
            # Live Databricks/MCP/connector implementations are deferred (D3); the
            # scaffold always uses stubs so it runs with no live dependency.
            _log.warning(
                "USE_LIVE_INTEGRATIONS is set but live adapters are not implemented; "
                "using local stubs (plan decision D3)."
            )
        repos = Repositories.build()
        audit = repos.audit
        dead_letter = repos.dead_letter
        return cls(
            settings=settings,
            repos=repos,
            audit=audit,
            dead_letter=dead_letter,
            model=StubModelAdapter(),
            vector_search=StubVectorSearchAdapter(),
            diagnostics=StubDiagnosticsAdapter(),
            ai_functions=StubAIFunctionsAdapter(),
            mcp=MCPClient(build_registry(settings)),
            genie=StubGenieClient(),
            servicenow=ServiceNowConnector(settings, audit),
            jira=JiraConnector(settings, audit),
            teams=TeamsConnector(settings, audit),
            skybot=SkybotConnector(settings, audit),
        )
