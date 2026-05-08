"""Tests for the health check endpoint."""

import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client):
    """GET /api/health should return 200 OK."""
    response = await client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_reports_database_connected(client):
    """Health endpoint should confirm database connectivity."""
    response = await client.get("/api/health")
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
