"""Player and agent-safe SuspectKnowledge model and builder."""

from typing import Any

from pydantic import BaseModel, Field

from app.core.exceptions import SuspectNotAvailableError
from app.scenarios.loader import ScenarioLoader


class SuspectKnowledge(BaseModel):
    """Player and agent-safe representation of knowledge known to a suspect."""

    suspect_id: str = Field(..., description="Unique ID of the suspect")
    name: str = Field(..., description="Full name of the suspect")
    public_description: str = Field(..., description="Public profile description")
    alibi: str | None = Field(None, description="Suspect's stated alibi")
    relationship_to_victim: str | None = Field(
        None, description="Suspect's relationship to the victim"
    )
    profile_metadata: dict[str, Any] | None = Field(
        default=None, description="Additional public metadata attributes"
    )
    known_timeline_events: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Non-secret timeline events known to or involving this suspect",
    )
    known_evidence_names: list[str] = Field(
        default_factory=list,
        description="Names of public/discovered evidence items in the case",
    )


class SuspectKnowledgeBuilder:
    """Builder for constructing explicit, player-safe SuspectKnowledge objects."""

    def __init__(self, loader: ScenarioLoader | None = None) -> None:
        self.loader = loader or ScenarioLoader()

    def build_knowledge(self, scenario_id: str, suspect_id: str) -> SuspectKnowledge:
        """Construct player/agent-safe SuspectKnowledge for a suspect in a scenario."""
        scenario_def = self.loader.load(scenario_id)
        public_scenario = scenario_def.to_player_view()

        # Locate requested suspect from public scenario view (ground truth stripped)
        suspect = next(
            (s for s in public_scenario.suspects if s.id == suspect_id), None
        )
        if not suspect:
            raise SuspectNotAvailableError(
                f"Suspect '{suspect_id}' is not available in scenario '{scenario_id}'."
            )

        # Non-secret timeline events involving or relevant to this suspect
        known_events = [
            {
                "order": event.event_order,
                "description": event.description,
                "timestamp": event.timestamp_str,
            }
            for event in public_scenario.timeline
            if event.suspect_id == suspect_id or event.suspect_id is None
        ]

        # Public evidence names (excluding secret discovery metadata)
        known_evidence = [ev.name for ev in public_scenario.evidence]

        return SuspectKnowledge(
            suspect_id=suspect.id,
            name=suspect.name,
            public_description=suspect.description,
            alibi=suspect.alibi,
            relationship_to_victim=suspect.relationship_to_victim,
            profile_metadata=suspect.profile_metadata,
            known_timeline_events=known_events,
            known_evidence_names=known_evidence,
        )
