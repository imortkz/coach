"""Shared test fixtures for backend tests — async MongoDB via mongomock."""

import asyncio

import pytest
import pytest_asyncio
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

from app.auth.models import User
from app.config import DEV_USER_ID
from app.exercises.models import Exercise
from app.programs.models import Program
from app.workouts.models import Setting, Workout


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db():
    """Initialize Beanie with a fresh test database for each test."""
    import app.database as db_module

    mongo_client = AsyncMongoClient("mongodb://localhost:27017")
    database = mongo_client["gymcoach_test"]

    await init_beanie(
        database=database,
        document_models=[User, Exercise, Program, Workout, Setting],
    )

    # Expose client so health check can ping it
    db_module.client = mongo_client

    yield database

    # Clean up all collections after each test
    for name in await database.list_collection_names():
        await database[name].drop()

    db_module.client = None
    await mongo_client.aclose()


@pytest_asyncio.fixture
async def test_user(db) -> User:
    """Create the dev user for tests (matches dev-mode auth bypass)."""
    user = User(
        id=DEV_USER_ID,
        telegram_id=0,
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    await user.insert()
    return user


@pytest_asyncio.fixture
async def client(db, test_user):
    """Async HTTP client for testing FastAPI app.

    DEV_MODE is true by default so no auth header is needed —
    the dev bypass will use the test_user created above.
    """
    from app.main import app

    # Override lifespan — DB already initialized by `db` fixture
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac
