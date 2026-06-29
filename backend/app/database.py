"""MongoDB connection via Beanie ODM."""

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import MONGODB_DB_NAME, MONGODB_URL

client: AsyncMongoClient | None = None


async def init_db(
    mongodb_url: str | None = None,
    db_name: str | None = None,
) -> None:
    """Initialize Beanie with all document models.

    Program-collection migrations run on the RAW pymongo collection BEFORE
    init_beanie so that when Beanie auto-builds the unique
    ``user_program_version`` index it sees clean, fully-stamped data and no
    name-conflicting index. Doing this after init_beanie is unsafe: the unique
    index would be built first, crashing on either legacy null rows
    (DuplicateKeyError) or a pre-existing non-unique index of the same name
    (IndexKeySpecsConflict — what took the PR-A2 deploy down).
    """
    global client

    from app.auth.models import User
    from app.exercises.models import Exercise
    from app.programs.models import Program
    from app.workouts.models import Setting, Workout

    client = AsyncMongoClient(mongodb_url or MONGODB_URL)
    db = client[db_name or MONGODB_DB_NAME]

    programs = db["programs"]
    await drop_conflicting_program_index(programs)
    await backfill_program_lineage(programs)
    await sync_program_version_field(programs)

    await init_beanie(
        database=db,
        document_models=[User, Exercise, Program, Workout, Setting],
    )


def _programs_collection(collection=None):
    """Resolve the programs collection: an explicit raw one (pre-init) or the
    Beanie-managed one (post-init, used by tests)."""
    if collection is not None:
        return collection
    from app.programs.models import Program

    return Program.get_pymongo_collection()


async def drop_conflicting_program_index(collection=None) -> bool:
    """Drop ``user_program_version`` if it exists without ``unique=True``.

    init_beanie rebuilds the index from the model's Settings (now unique).
    Mongo's createIndex cannot change the options of an existing same-named
    index — it raises IndexKeySpecsConflict (code 86). That is exactly what
    crashed the PR-A2 deploy: PR-A1 had created this index non-unique, so when
    A2 tried to recreate it unique the app never started. Dropping the stale
    non-unique index first lets init_beanie build the unique version cleanly.

    No-op when the index is absent or already unique. Returns True if dropped.
    """
    collection = _programs_collection(collection)
    info = await collection.index_information()
    existing = info.get("user_program_version")
    if existing is not None and not existing.get("unique", False):
        await collection.drop_index("user_program_version")
        return True
    return False


async def backfill_program_lineage(collection=None) -> int:
    """Stamp lineage fields onto legacy program rows. Idempotent.

    Programs created before the versioned-rows groundwork have no ``program_id``
    / ``version``. Set ``program_id = _id`` (the row becomes its own lineage
    root) and ``version = 1`` for any such row. Only matches rows missing the
    field, so it is safe to run on every startup and a no-op once migrated.

    Runs BEFORE init_beanie builds the unique index, so the index is built over
    already-stamped rows and never collides on null keys. Returns rows modified.
    """
    collection = _programs_collection(collection)
    result = await collection.update_many(
        {"program_id": {"$exists": False}},
        [{"$set": {"program_id": "$_id", "version": 1}}],
    )
    return result.modified_count


async def sync_program_version_field(collection=None) -> int:
    """Sync version = current_version for rows where they drifted.

    Between PR-A1 (non-unique index + backfill) and PR-A2 (unique index +
    version wired into routes) there is a window where a program edit bumps
    current_version but not version. This one-shot pass closes that gap so
    the unique index sees consistent state. Idempotent and a no-op once in sync.
    """
    collection = _programs_collection(collection)
    result = await collection.update_many(
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
