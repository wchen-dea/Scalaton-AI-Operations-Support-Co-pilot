"""Specialized agents with typed boundaries (`tech-arch §4.3`).

Each agent is a thin, testable unit that consumes the intelligence/MCP adapters and
communicates through the typed internal models. Read-only agents (Log, Knowledge,
Research) never write production data; their boundaries are enforced at the adapter
interface. The Change agent drafts only and stops at the approval boundary.
"""

from .change_agent import ChangeAgent
from .communication_agent import CommunicationAgent
from .diagnosis_agent import DiagnosisAgent
from .escalation_agent import EscalationAgent
from .knowledge_agent import KnowledgeAgent
from .log_agent import LogAgent
from .research_agent import ResearchAgent

__all__ = [
    "LogAgent",
    "KnowledgeAgent",
    "ResearchAgent",
    "DiagnosisAgent",
    "CommunicationAgent",
    "EscalationAgent",
    "ChangeAgent",
]
