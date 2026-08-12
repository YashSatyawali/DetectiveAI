"""Application-level agent service for interacting with Lamatic AgentKit."""

from typing import Any

from app.lamatic.client import LamaticClient
from app.lamatic.schemas import AgentRequest, AgentResponse


class DetectiveAgent:
    """Minimal prototype detective assistant agent service using Lamatic AgentKit."""

    DEFAULT_INSTRUCTION = (
        "You are a detective assistant participating in an investigation game. "
        "For this prototype, answer the user's question clearly and concisely."
    )

    def __init__(self, client: LamaticClient | None = None) -> None:
        self.client = client or LamaticClient()

    def ask(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Invoke the detective assistant agent with a message."""
        request = AgentRequest(message=message, context=context)

        payload = {
            "message": request.message,
            "system_instruction": self.DEFAULT_INSTRUCTION,
        }
        if request.context:
            payload["context"] = request.context

        return self.client.execute(payload=payload)
