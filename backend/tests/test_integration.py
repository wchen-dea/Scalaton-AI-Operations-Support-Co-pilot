"""Integration tests (mocked): connectors, MCP registry/client, Genie, AI functions."""

from __future__ import annotations

from app.audit.store import AuditStore
from app.adapters import StubAIFunctionsAdapter, StubVectorSearchAdapter
from app.connectors import JiraConnector
from app.mcp import MCPClient, StubGenieClient, build_registry
from app.mcp.registry import MANAGED_SERVERS

from .conftest import make_settings


def test_connector_write_blocked_when_external_writes_disabled():
    settings = make_settings(enable_external_writes=False)
    jira = JiraConnector(settings, AuditStore())
    result = jira.write(
        correlation_id="c1", source_event_id="e1", target_record="INC1", action_type="create_bug"
    )
    assert result.ok is False
    assert "disabled" in (result.blocked_reason or "")


def test_connector_write_succeeds_and_is_idempotent_when_enabled():
    settings = make_settings(enable_external_writes=True)
    audit = AuditStore()
    jira = JiraConnector(settings, audit)
    r1 = jira.write(
        correlation_id="c1", source_event_id="e1", target_record="INC1", action_type="create_bug"
    )
    r2 = jira.write(
        correlation_id="c1", source_event_id="e1", target_record="INC1", action_type="create_bug"
    )
    assert r1.ok and r2.ok
    assert r1.external_id == r2.external_id  # idempotent reuse
    assert len(audit.find(correlation_id="c1", event_type="jira.write.ok")) == 1


def test_mcp_registry_includes_managed_servers_and_externals():
    settings = make_settings(external_mcp_servers=("custom-ops",))
    registry = build_registry(settings)
    names = {s.name for s in registry}
    assert set(MANAGED_SERVERS) <= names
    assert "custom-ops" in names
    # Managed servers are referenced by resource name, never inline URLs/tokens.
    for server in registry:
        assert "http" not in server.resource_ref


def test_mcp_client_loads_tools():
    client = MCPClient(build_registry(make_settings()))
    tools = client.load_tools()
    tool_names = {t.name for t in tools}
    assert "genie.ask" in tool_names
    assert "vector_search.query" in tool_names


def test_genie_returns_answer_with_provenance():
    answer = StubGenieClient().ask(question="why did it fail?")
    assert answer.answer
    assert answer.generated_sql  # retained internally for audit (PC-007)
    assert answer.source_references


def test_ai_functions_adapter_stub():
    ai = StubAIFunctionsAdapter()
    assert ai.classify(text="disk full", labels=["infra", "data"]) == "infra"
    assert ai.summarize(text="a b c d e", max_words=3) == "a b c"


def test_vector_search_returns_sources():
    result = StubVectorSearchAdapter().retrieve(query="orders", k=2)
    assert result.runbook_references
    assert result.source_references
