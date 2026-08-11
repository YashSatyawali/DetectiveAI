"""Scenario registry for discovering available scenarios dynamically."""

from pathlib import Path
from typing import Any

from app.scenarios.loader import ScenarioLoader
from app.scenarios.schemas import ScenarioDefinition


class ScenarioRegistry:
    """Registry to discover and list available scenarios in the workspace."""

    def __init__(self, base_dir: str | Path = "scenarios") -> None:
        self.base_dir = Path(base_dir)
        self.loader = ScenarioLoader(self.base_dir)

    def list_scenarios(self) -> list[dict[str, Any]]:
        """Scan the scenario base directory and return summaries of valid scenarios.

        Returns a list of dictionaries, each containing:
        - id
        - name
        - version
        - description
        """
        if not self.base_dir.exists() or not self.base_dir.is_dir():
            return []

        scenarios: list[dict[str, Any]] = []

        for entry in sorted(self.base_dir.iterdir()):
            if not entry.is_dir():
                continue

            try:
                scenario_def = self.loader.load(entry.name)
                scenarios.append(
                    {
                        "id": scenario_def.scenario_id,
                        "name": scenario_def.name,
                        "version": scenario_def.version,
                        "description": scenario_def.description,
                    }
                )
            except Exception:
                # Skip invalid or incomplete scenario directories during listing
                continue

        return scenarios

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        """Retrieve and return a validated ScenarioDefinition by ID."""
        return self.loader.load(scenario_id)
