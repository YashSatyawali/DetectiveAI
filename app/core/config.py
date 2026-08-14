"""Application core configuration."""

import os

from pydantic import BaseModel


class Settings(BaseModel):
    """Core settings for DetectiveAI engine."""

    app_name: str = os.getenv("APP_NAME", "DetectiveAI")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    api_v1_prefix: str = "/api/v1"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./detective_ai.db")

    # Lamatic AgentKit Settings
    lamatic_endpoint: str | None = os.getenv("LAMATIC_ENDPOINT")
    lamatic_project_id: str | None = os.getenv("LAMATIC_PROJECT_ID")
    lamatic_api_key: str | None = os.getenv("LAMATIC_API_KEY")
    lamatic_flow_id: str | None = os.getenv("LAMATIC_FLOW_ID")
    lamatic_suspect_flow_id: str | None = os.getenv("LAMATIC_SUSPECT_FLOW_ID")
    lamatic_evidence_flow_id: str | None = os.getenv("LAMATIC_EVIDENCE_FLOW_ID")
    lamatic_solution_flow_id: str | None = os.getenv("LAMATIC_SOLUTION_FLOW_ID")


settings = Settings()
