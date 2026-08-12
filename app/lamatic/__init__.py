"""Lamatic AgentKit integration package."""

from app.lamatic.agent import DetectiveAgent
from app.lamatic.client import LamaticClient
from app.lamatic.exceptions import (
    LamaticConfigurationError,
    LamaticConnectionError,
    LamaticError,
    LamaticInvocationError,
)
from app.lamatic.schemas import AgentRequest, AgentResponse

__all__ = [
    "AgentRequest",
    "AgentResponse",
    "DetectiveAgent",
    "LamaticClient",
    "LamaticConfigurationError",
    "LamaticConnectionError",
    "LamaticError",
    "LamaticInvocationError",
]
