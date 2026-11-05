"""Databricks intelligence adapters behind typed interfaces (`tech-arch §4.3`, `§5`).

Each capability (model inference, Vector Search retrieval, Unity Catalog diagnostics,
Databricks AI Functions) is a `Protocol` with a local stub. Live implementations drop
in behind the same signature; the stubs return deterministic data so agents run with no
live dependency (plan decision D3, NFR-007).
"""

from .ai_functions import AIFunctionsAdapter, StubAIFunctionsAdapter
from .diagnostics import DiagnosticsAdapter, StubDiagnosticsAdapter
from .model import ModelAdapter, StubModelAdapter
from .vector_search import StubVectorSearchAdapter, VectorSearchAdapter

__all__ = [
    "ModelAdapter",
    "StubModelAdapter",
    "VectorSearchAdapter",
    "StubVectorSearchAdapter",
    "DiagnosticsAdapter",
    "StubDiagnosticsAdapter",
    "AIFunctionsAdapter",
    "StubAIFunctionsAdapter",
]
