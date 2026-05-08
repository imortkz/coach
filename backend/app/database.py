"""MongoDB connection via Beanie ODM."""

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import MONGODB_DB_NAME, MONGODB_URL

client: AsyncMongoClient | None = None


async def init_db(
    mongodb_url: str | None = None,
    db_name: str | None = None,
) -> None:
    """Initialize Beanie with all document models."""
    global client

    from app.auth.models import User
    from app.exercises.models import Exercise
    from app.programs.models import Program
    from app.workouts.models import Setting, Workout

    client = AsyncMongoClient(mongodb_url or MONGODB_URL)
    db = client[db_name or MONGODB_DB_NAME]

    await init_beanie(
        database=db,
        document_models=[User, Exercise, Program, Workout, Setting],
    )


async def close_db() -> None:
    """Close the MongoDB client."""
    global client
    if client:
        client.close()
        client = None
