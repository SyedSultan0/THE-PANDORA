"""AI Interview Agent - FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="AI Interview Agent",
    description="Backend API for the AI Interview Agent hackathon project.",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint to verify the server is running."""
    return {"status": "ok", "message": "AI Interview Agent API is running"}