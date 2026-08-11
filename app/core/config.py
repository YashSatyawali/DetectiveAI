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


settings = Settings()
