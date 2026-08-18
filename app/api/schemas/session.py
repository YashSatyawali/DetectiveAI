"""Pydantic schemas for session management, status, actions, and history."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """Request payload to create/start a new game session."""

    scenario: str = Field(
        ...,
        description="Scenario identifier or display name",
    )


class SessionStageResponse(BaseModel):
    """Current stage details in a session."""

    id: str
    order: int
    name: str


class SessionLocationResponse(BaseModel):
    """Current location details in a session."""

    id: str | None = None
    name: str | None = None
    description: str | None = None


class SessionCreatedResponse(BaseModel):
    """Response returned upon successful game session creation."""

    session_id: str
    scenario_id: str
    case_title: str
    stage: SessionStageResponse
    status: str
    score: int = 0
    current_location: SessionLocationResponse | None = None


class ActionItem(BaseModel):
    """Generic action item with id and display name."""

    id: str
    name: str


class AvailabilityFlag(BaseModel):
    """Boolean flag indicating whether a composite action is available."""

    available: bool


class AvailableActionsResponse(BaseModel):
    """Player-friendly available actions currently permitted in the session."""

    move: list[ActionItem] = Field(default_factory=list)
    inspect: bool = Field(default=False)
    interrogate: list[ActionItem] = Field(default_factory=list)
    examine: list[ActionItem] = Field(default_factory=list)
    advance: AvailabilityFlag
    solve: AvailabilityFlag


class GameEventResponse(BaseModel):
    """Player-visible chronological game event record."""

    id: str
    session_id: str
    event_type: str
    target_type: str | None = None
    target_id: str | None = None
    timestamp: datetime | None = None
    result_data: dict[str, Any] | None = None
