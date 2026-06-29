"""Tests for versioned-rows groundwork: lineage backfill + index safety.

Regression coverage for #48, which took prod down: the new Program model
declared a UNIQUE compound index on (user_id, program_id, version) and
init_beanie auto-built it against legacy rows missing those fields — every
such row keyed to (user, null, null), so a user with 2+ programs hit a
DuplicateKeyError and the app never started (nginx 502). PR-A1 makes the
index non-unique and backfills the fields instead. PR-A2 flips to unique
(safe after backfill) and wires version increment into the update route.

PR-A2 hotfix: flipping the existing non-unique index to unique crashed the
deploy with IndexKeySpecsConflict (code 86) — Mongo's createIndex cannot
change the options of an existing same-named index. init_db now drops the
stale non-unique index and stamps the data BEFORE init_beanie rebuilds it
unique. TestIndexTransition covers exactly this prod-shaped path.
"""

import pytest
from beanie import init_beanie
from pymongo import ASCENDING, DESCENDING, AsyncMongoClient, IndexModel
from pymongo.errors import BulkWriteError

from app.auth.models import User
from app.database import (
    backfill_program_lineage,
    drop_conflicting_program_index,
    sync_program_version_field,
)
from app.exercises.models import Exercise
from app.programs.models import Program
from app.workouts.models import Setting, Workout


def _legacy_program(pid: str, user_id: str, name: str) -> dict:
    """A program row in the pre-versioning shape (no program_id / version)."""
    return {
        "_id": pid,
        "user_id": user_id,
        "name": name,
        "rest_timer_disabled": False,
        "current_version": 1,
        "exercises": [],
        "versions": [],
    }


class TestProgramLineageBackfill:
    @pytest.mark.asyncio
    async def test_backfill_stamps_legacy_rows_idempotently(self, db, test_user):
        """Each row gets a distinct user_id so no unique-index collision on null
        program_id — the backfill function itself is what's under test here."""
        await db["programs"].insert_many([
            _legacy_program("leg-1", "legacy-user-1", "День 1"),
            _legacy_program("leg-2", "legacy-user-2", "День 2"),
        ])

        assert await backfill_program_lineage() == 2

        docs = {d["_id"]: d async for d in db["programs"].find()}
        assert docs["leg-1"]["program_id"] == "leg-1"
        assert docs["leg-1"]["version"] == 1
        assert docs["leg-2"]["program_id"] == "leg-2"
        assert docs["leg-2"]["version"] == 1

        # Idempotent: a second pass matches nothing.
        assert await backfill_program_lineage() == 0

    @pytest.mark.asyncio
    async def test_unique_index_rejects_two_naked_rows_same_user(self, db, test_user):
        """PR-A2 contract: unique index now correctly prevents inserting two legacy
        (no program_id) rows for the same user — confirming the constraint is live."""
        with pytest.raises(BulkWriteError):
            await db["programs"].insert_many([
                _legacy_program("leg-a", test_user.id, "A"),
                _legacy_program("leg-b", test_user.id, "B"),
            ])


class TestIndexTransition:
    """Reproduce the prod-shaped A1→A2 path the original tests missed: the
    non-unique index already exists (built by A1) AND legacy rows are present,
    then the A2 startup sequence runs. Must not crash; index ends up unique."""

    @pytest.mark.asyncio
    async def test_drop_conflicting_index_then_init_beanie_builds_unique(self):
        client = AsyncMongoClient("mongodb://localhost:27017")
        db = client["gymcoach_idx_transition_test"]
        programs = db["programs"]
        try:
            # Clean slate, then recreate the *A1 prod state*: a non-unique
            # user_program_version index over two same-user legacy rows that
            # still carry null program_id/version.
            await programs.drop()
            await programs.create_indexes([
                IndexModel(
                    [("user_id", ASCENDING), ("program_id", ASCENDING), ("version", DESCENDING)],
                    name="user_program_version",  # non-unique, as A1 created it
                )
            ])
            await programs.insert_many([
                _legacy_program("leg-x", "same-user", "X"),
                _legacy_program("leg-y", "same-user", "Y"),
            ])

            # The A2 startup sequence (mirrors init_db ordering).
            assert await drop_conflicting_program_index(programs) is True
            assert await backfill_program_lineage(programs) == 2
            await sync_program_version_field(programs)

            # init_beanie now rebuilds the index as unique over clean data —
            # this raised IndexKeySpecsConflict before the hotfix.
            await init_beanie(
                database=db,
                document_models=[User, Exercise, Program, Workout, Setting],
            )

            info = await programs.index_information()
            assert info["user_program_version"].get("unique") is True

            # drop is now a no-op (index already unique).
            assert await drop_conflicting_program_index(programs) is False
        finally:
            await programs.drop()
            await client.aclose()


class TestSyncProgramVersionField:
    @pytest.mark.asyncio
    async def test_sync_closes_drift_between_a1_and_a2(self, db, test_user):
        """Rows where current_version > version (edited between A1 and A2) get synced."""
        await db["programs"].insert_one({
            "_id": "drifted-1",
            "user_id": test_user.id,
            "name": "Дрейф",
            "rest_timer_disabled": False,
            "current_version": 3,
            "exercises": [],
            "versions": [],
            "program_id": "some-lineage-id",
            "version": 1,  # stale — diverged during the A1→A2 window
        })

        assert await sync_program_version_field() == 1

        doc = await db["programs"].find_one({"_id": "drifted-1"})
        assert doc["version"] == 3

        # Idempotent
        assert await sync_program_version_field() == 0

    @pytest.mark.asyncio
    async def test_sync_leaves_already_synced_rows_untouched(self, db, test_user):
        await db["programs"].insert_one({
            "_id": "synced-1",
            "user_id": test_user.id,
            "name": "В порядке",
            "rest_timer_disabled": False,
            "current_version": 2,
            "exercises": [],
            "versions": [],
            "program_id": "another-lineage-id",
            "version": 2,
        })

        assert await sync_program_version_field() == 0


class TestUniqueIndexOnEditedPrograms:
    @pytest.mark.asyncio
    async def test_update_program_increments_version_field(self, client, db, test_user):
        """Editing a program via the API bumps program.version alongside current_version."""
        r = await client.post("/api/programs/", json={
            "name": "Программа А",
            "rest_timer_disabled": False,
            "exercises": [],
        })
        assert r.status_code == 201
        pid = r.json()["id"]

        doc_before = await db["programs"].find_one({"_id": pid})
        assert doc_before["version"] == 1
        assert doc_before["current_version"] == 1

        r2 = await client.put(f"/api/programs/{pid}", json={
            "name": "Программа А (v2)",
            "rest_timer_disabled": False,
            "exercises": [],
        })
        assert r2.status_code == 200

        doc_after = await db["programs"].find_one({"_id": pid})
        assert doc_after["version"] == 2
        assert doc_after["current_version"] == 2

    @pytest.mark.asyncio
    async def test_two_edits_no_unique_index_collision(self, client, db, test_user):
        """Two consecutive edits must not raise DuplicateKeyError (each increments version)."""
        r = await client.post("/api/programs/", json={
            "name": "Коллизия",
            "rest_timer_disabled": False,
            "exercises": [],
        })
        assert r.status_code == 201
        pid = r.json()["id"]

        for i in range(2, 4):
            r = await client.put(f"/api/programs/{pid}", json={
                "name": f"Коллизия v{i}",
                "rest_timer_disabled": False,
                "exercises": [],
            })
            assert r.status_code == 200

        doc = await db["programs"].find_one({"_id": pid})
        assert doc["version"] == 3
