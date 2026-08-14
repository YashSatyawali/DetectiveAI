"""Player-safe EvidenceKnowledge model and builder for AI forensic analysis."""

from typing import Any

from pydantic import BaseModel, Field

from app.core.exceptions import EvidenceNotFoundError
from app.scenarios.loader import ScenarioLoader


class EvidenceKnowledge(BaseModel):
    """Player-safe representation of evidence information for AI forensic analysis."""

    evidence_id: str = Field(..., description="Unique ID of the evidence item")
    name: str = Field(..., description="Name of the evidence item")
    description: str = Field(
        ..., description="Detailed description of the evidence item"
    )
    evidence_type: str = Field(
        ..., description="Type/category of evidence (e.g., physical, digital)"
    )
    location_id: str | None = Field(
        None, description="Location ID where evidence was found"
    )
    location_name: str | None = Field(
        None, description="Name of location where evidence was found"
    )
    discovery_metadata: dict[str, Any] | None = Field(
        default=None, description="Player-visible discovery metadata attributes"
    )


class EvidenceKnowledgeBuilder:
    """Builder for constructing explicit, player-safe EvidenceKnowledge objects."""

    def __init__(self, loader: ScenarioLoader | None = None) -> None:
        self.loader = loader or ScenarioLoader()

    def build_knowledge(self, scenario_id: str, evidence_id: str) -> EvidenceKnowledge:
        """Construct player-safe EvidenceKnowledge for an evidence item."""
        scenario_def = self.loader.load(scenario_id)
        public_scenario = scenario_def.to_player_view()

        # Locate requested evidence from public scenario view (ground truth stripped)
        evidence = next(
            (ev for ev in public_scenario.evidence if ev.id == evidence_id), None
        )
        if not evidence:
            raise EvidenceNotFoundError(
                f"Evidence '{evidence_id}' does not exist in scenario '{scenario_id}'."
            )

        # Determine location name if location_id is present
        loc_name = None
        if evidence.location_id:
            found_loc = next(
                (
                    loc
                    for loc in public_scenario.locations
                    if loc.id == evidence.location_id
                ),
                None,
            )
            if found_loc:
                loc_name = found_loc.name

        return EvidenceKnowledge(
            evidence_id=evidence.id,
            name=evidence.name,
            description=evidence.description,
            evidence_type=evidence.evidence_type,
            location_id=evidence.location_id,
            location_name=loc_name,
            discovery_metadata=evidence.discovery_metadata,
        )
