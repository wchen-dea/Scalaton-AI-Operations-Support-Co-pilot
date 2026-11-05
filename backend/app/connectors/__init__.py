"""External system connectors on the `tech-arch §6` adapter contract."""

from .base import Connector, ConnectorError, ConnectorResult
from .jira import JiraConnector
from .servicenow import ServiceNowConnector
from .skybot import SkybotConnector
from .teams import TeamsConnector

__all__ = [
    "Connector",
    "ConnectorError",
    "ConnectorResult",
    "JiraConnector",
    "ServiceNowConnector",
    "SkybotConnector",
    "TeamsConnector",
]
