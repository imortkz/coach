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

    await backfill_program_lineage()
    await sync_program_version_field()


async def backfill_program_lineage() -> int:
    """Stamp lineage fields onto legacy program rows. Idempotent.

    Programs created before the versioned-rows groundwork have no ``program_id``
    / ``version``. Set ``program_id = _id`` (the row becomes its own lineage
    root) and ``version = 1`` for any such row. Only matches rows missing the
    field, so it is safe to run on every startup and a no-op once migrated.

    Runs AFTER init_beanie (the new index is non-unique, so it builds fine over
    the not-yet-stamped rows; this just fills them in). Returns rows modified.
    """
    from app.programs.models import Program

    result = await Program.get_pymongo_collection().update_many(
        {"program_id": {"$exists": False}},
        [{"$set": {"program_id": "$_id", "version": 1}}],
    )
    return result.modified_count


async def sync_program_version_field() -> int:
    """Sync version = current_version for rows where they drifted.

    Between PR-A1 (non-unique index + backfill) and PR-A2 (unique index +
    version wired into routes) there is a window where a program edit bumps
    current_version but not version. This one-shot pass closes that gap so
    the unique index sees consistent state. Idempotent and a no-op once in sync.
    """
    from app.programs.models import Program

    result = await Program.get_pymongo_collection().update_many(
        {"$expr": {"$ne": ["$version", "$current_version"]}},
        [{"$set": {"version": "$current_version"}}],
    )
    return result.modified_count


async def close_db() -> None:
    """Close the MongoDB client."""
    global client
    if client:
        client.close()
        client = None
