"""Tests for the FastAPI application health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Verify the root endpoint returns a healthy status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "AI Interview Agent" in data["message"]