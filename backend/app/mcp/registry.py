"""MCP server registry (plan decision D4).

Server definitions are read from configuration — the Databricks-managed MCP servers
(Genie, Vector Search, Unity Catalog functions) plus any external servers — and are
referenced by named resource/secret via `valueFrom`, never inline URLs or tokens
(NFR-001).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..config import Settings

# The Databricks-managed MCP servers this app connects to by default (plan decision D4).
MANAGED_SERVERS = ("genie", "vector_search", "uc_functions")


class MCPServerDef(BaseModel):
    name: str
    kind: str  # "managed" | "external"
    # A resource reference name, not a URL or token (resolved via `valueFrom` at deploy).
    resource_ref: str
    managed: bool = False
    tools: list[str] = Field(default_factory=list)


def build_registry(settings: Settings) -> list[MCPServerDef]:
    """Build the MCP server registry from settings."""

    servers: list[MCPServerDef] = [
        MCPServerDef(
            name="genie",
            kind="managed",
            resource_ref="genie-space",
            managed=True,
            tools=["genie.ask", "genie.explain"],
        ),
        MCPServerDef(
            name="vector_search",
            kind="managed",
            resource_ref="vector-search-index",
            managed=True,
            tools=["vector_search.query"],
        ),
        MCPServerDef(
            name="uc_functions",
            kind="managed",
            resource_ref="uc-functions",
            managed=True,
            tools=["uc.run_function"],
        ),
    ]
    for ref in settings.external_mcp_servers:
        servers.append(
            MCPServerDef(
                name=ref,
                kind="external",
                resource_ref=f"mcp-{ref}",
                managed=False,
                tools=[],
            )
        )
    return servers
