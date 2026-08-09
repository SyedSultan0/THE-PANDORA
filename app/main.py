"""AI Interview Agent - FastAPI application entry point."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import create_router
from app.llm import (
    FailoverLLMProvider,
    GeminiProvider,
    NvidiaProvider,
    OpenRouterProvider,
)
from app.llm.base import LLMProvider

# Load environment variables from the root .env file (e.g. GEMINI_API_KEY,
# OPENROUTER_API_KEY). Existing environment variables take precedence; the
# .env file is local and is excluded from version control via .gitignore.
load_dotenv()


def build_llm_provider() -> LLMProvider:
    """Build the failover LLM provider chain.

    Preferred order:
      1. NVIDIA (primary)
      2. OpenRouter (multi-key/model failover)
      3. Gemini (legacy fallback)

    Providers that are not configured (missing API key) are skipped by the
    failover wrapper, so the chain works with any subset of credentials.
    """
    providers: list[LLMProvider] = []
    if os.getenv("NVIDIA_API_KEY"):
        providers.append(NvidiaProvider())
    if os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY_1"):
        providers.append(OpenRouterProvider())
    if os.getenv("GEMINI_API_KEY"):
        providers.append(GeminiProvider())
    return FailoverLLMProvider(providers)


app = FastAPI(
    title="AI Interview Agent",
    description="Backend API for the AI Interview Agent hackathon project.",
    version="0.1.0",
)

app.include_router(create_router(llm=build_llm_provider()))


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