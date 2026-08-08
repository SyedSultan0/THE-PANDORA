"""AI Interview Agent - FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes import create_router
from app.llm import GeminiProvider

app = FastAPI(
    title="AI Interview Agent",
    description="Backend API for the AI Interview Agent hackathon project.",
    version="0.1.0",
)

app.include_router(create_router(llm=GeminiProvider()))


@app.get(
    "/",
    summary="Root",
    description="Basic service information.",
    response_description="Service status and message.",
)
async def root() -> dict[str, str]:
    """Basic service information."""
    return {"status": "ok", "message": "AI Interview Agent API is running"}


@app.get(
    "/health",
    summary="Health Check",
    description=(
        "Liveness probe for deployment health checks. Does not require "
        "authentication, does not call the LLM, and does not create an "
        "interview session."
    ),
    response_description="Service health status.",
)
async def health() -> dict[str, str]:
    """Liveness health check endpoint."""
    return {"status": "ok"}