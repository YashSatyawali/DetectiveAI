import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
logger.info(
    "Initializing %s FastAPI application (env=%s)",
    settings.app_name,
    settings.environment,
)

app = FastAPI(
    title=settings.app_name,
    description="Authoritative game engine and API server for DetectiveAI.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health_router)
