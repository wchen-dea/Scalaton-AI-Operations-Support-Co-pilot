"""MCP client that loads tools from registered servers for the LangGraph agents.

The scaffold exposes a small fixed tool set behind this interface so agents run offline
(NFR-007). A live client (for example `langchain-mcp-adapters`, the `live` extra) binds
real MCP tools in its place. Tool results are treated as untrusted data (NFR-002).
"""

from __future__ import annotations

from pydantic import BaseModel

from .registry import MCPServerDef


class MCPTool(BaseModel):
    server: str
    name: str


class MCPClient:
    def __init__(self, servers: list[MCPServerDef]) -> None:
        self._servers = servers

    def servers(self) -> list[MCPServerDef]:
        return list(self._servers)

    def load_tools(self) -> list[MCPTool]:
        """Return the tools exposed by every registered server."""

        tools: list[MCPTool] = []
        for server in self._servers:
            for tool in server.tools:
                tools.append(MCPTool(server=server.name, name=tool))
        return tools

    def has_server(self, name: str) -> bool:
        return any(s.name == name for s in self._servers)
