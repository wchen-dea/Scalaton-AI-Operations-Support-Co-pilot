"""MCP connection layer and Genie integration (plan decision D4).

Registers the Databricks-managed MCP servers (Genie, Vector Search, Unity Catalog
functions) and a config-driven set of external MCP servers, loads their tools for the
LangGraph agents, and exposes a Genie integration. All stubbed locally so no live MCP
endpoint is required (NFR-007).
"""

from .client import MCPClient, MCPTool
from .genie import GenieAnswer, GenieClient, StubGenieClient
from .registry import MCPServerDef, build_registry

__all__ = [
    "MCPClient",
    "MCPTool",
    "MCPServerDef",
    "build_registry",
    "GenieClient",
    "StubGenieClient",
    "GenieAnswer",
]
