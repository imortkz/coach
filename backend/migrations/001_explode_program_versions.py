"""Migration 001 — explode embedded program versions into versioned rows.

Converts the OLD single-document Program model (doc ``_id`` == program id, with
an embedded ``versions: [ProgramVersion]`` archive + a live ``current_version``
+ live ``exercises``) into the NEW model: one ``programs`` collection holding
one ROW per version.

For each legacy program document it writes:
  - ``program_id`` = the OLD doc's ``_id`` (preserves lineage, so existing
    ``Workout.program_id`` keeps matching).
  - one row per ``versions[i]`` using ``versions[i].version`` + its exercises.
  - one row for the live state using ``current_version`` + the live exercises.
  - ``version`` ints are copied VERBATIM so any ``Workout.program_version``
    still resolves to the right historical template.

Each new row gets its own fresh ``_id``.

IDEMPOTENT: a row is "new model" iff it has a ``program_id`` field. The script
only touches legacy docs (those WITHOUT ``program_id``); re-running after a
successful pass is a no-op.

SAFETY: this ships as a script only. It is NOT run by CI or the app. Run it
by hand against a database you have backed up. It writes a JSON backup of every
legacy doc it removes, which the ``--rollback`` mode consumes.

Usage (run from the backend/ directory so the app package resolves):
    # dry run — report what would change, write nothing
    uv run python migrations/001_explode_program_versions.py --dry-run

    # migrate (writes migrations/001_backup.json before removing legacy docs)
    uv run python migrations/001_explode_program_versions.py

    # roll back using the backup written by a prior migrate run
    uv run python migrations/001_explode_program_versions.py --rollback migrations/001_backup.json

Environment: reads MONGODB_URL / MONGODB_DB_NAME exactly like the app config.
"""

import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path

from bson import json_util
from pymongo import AsyncMongoClient

# Read the same connection env vars the app uses (with the same defaults), but
# WITHOUT importing app.config — that module hard-requires JWT_SECRET at import
# time, which is irrelevant to a data migration.
MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "gymcoach")

BACKUP_DIR = Path(__file__).resolve().parent


def _explode(doc: dict) -> list[dict]:
    """Build the new versioned rows for one legacy program document."""
    lineage = doc["_id"]
    user_id = doc["user_id"]

    # Keyed by version so malformed data with a duplicate version can't violate
    # the unique index; the live state wins a tie over an archived snapshot.
    by_version: dict[int, dict] = {}

    for v in doc.get("versions", []) or []:
        by_version[v["version"]] = {
            "_id": str(uuid.uuid4()),
            "program_id": lineage,
            "version": v["version"],
            "user_id": user_id,
            "name": v.get("name", doc.get("name", "")),
            "rest_timer_disabled": v.get("rest_timer_disabled", False),
            "created_at": v.get("created_at", doc.get("created_at")),
            "exercises": v.get("exercises", []),
        }

    # Live state — overwrites any archived row sharing the version number.
    by_version[doc["current_version"]] = {
        "_id": str(uuid.uuid4()),
        "program_id": lineage,
        "version": doc["current_version"],
        "user_id": user_id,
        "name": doc.get("name", ""),
        "rest_timer_disabled": doc.get("rest_timer_disabled", False),
        "created_at": doc.get("created_at"),
        "exercises": doc.get("exercises", []),
    }

    return [by_version[v] for v in sorted(by_version)]


async def migrate(dry_run: bool) -> int:
    client = AsyncMongoClient(MONGODB_URL)
    coll = client[MONGODB_DB_NAME]["programs"]
    try:
        # Legacy docs are exactly those lacking the new lineage field.
        legacy = await coll.find({"program_id": {"$exists": False}}).to_list(length=None)
        if not legacy:
            print("Nothing to migrate: no legacy program documents found.")
            return 0

        total_rows = 0
        new_rows: list[dict] = []
        for doc in legacy:
            rows = _explode(doc)
            total_rows += len(rows)
            new_rows.extend(rows)
            print(
                f"  program {doc['_id']} ({doc.get('name', '')!r}): "
                f"current_version={doc.get('current_version')}, "
                f"archived={len(doc.get('versions', []) or [])} "
                f"-> {len(rows)} rows"
            )

        print(
            f"\n{len(legacy)} legacy program(s) -> {total_rows} versioned row(s)."
        )

        if dry_run:
            print("Dry run: no writes performed.")
            return 0

        # Back up the legacy docs BEFORE removing them, so --rollback can restore.
        backup_path = BACKUP_DIR / "001_backup.json"
        backup_path.write_text(json_util.dumps(legacy, indent=2))
        print(f"Backed up {len(legacy)} legacy doc(s) to {backup_path}")

        await coll.insert_many(new_rows)
        delete = await coll.delete_many(
            {"_id": {"$in": [d["_id"] for d in legacy]}}
        )
        print(
            f"Inserted {len(new_rows)} new row(s); removed "
            f"{delete.deleted_count} legacy doc(s). Migration complete."
        )
        return 0
    finally:
        await client.aclose()


async def rollback(backup_file: str) -> int:
    path = Path(backup_file)
    if not path.exists():
        print(f"Backup file not found: {path}", file=sys.stderr)
        return 1

    legacy = json_util.loads(path.read_text())
    client = AsyncMongoClient(MONGODB_URL)
    coll = client[MONGODB_DB_NAME]["programs"]
    try:
        for doc in legacy:
            lineage = doc["_id"]
            # Drop the exploded rows of this lineage, then restore the original.
            await coll.delete_many({"program_id": lineage})
            await coll.replace_one({"_id": lineage}, doc, upsert=True)
        print(f"Rolled back {len(legacy)} program lineage(s) from {path}.")
        return 0
    finally:
        await client.aclose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    parser.add_argument("--rollback", metavar="BACKUP_JSON", help="restore from a backup file")
    args = parser.parse_args()

    if args.rollback:
        return asyncio.run(rollback(args.rollback))
    return asyncio.run(migrate(dry_run=args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
