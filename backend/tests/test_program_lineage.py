"""Tests for versioned-rows groundwork: lineage backfill + index safety.

Regression coverage for #48, which took prod down: the new Program model
declared a UNIQUE compound index on (user_id, program_id, version) and
init_beanie auto-built it against legacy rows missing those fields — every
such row keyed to (user, null, null), so a user with 2+ programs hit a
DuplicateKeyError and the app never started (nginx 502). PR-A1 makes the
index non-unique and backfills the fields instead.
"""

import pytest
from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.auth.models import User
from app.database import backfill_program_lineage
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
        await db["programs"].insert_many([
            _legacy_program("leg-1", test_user.id, "День 1"),
            _legacy_program("leg-2", test_user.id, "День 2"),
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
    async def test_index_builds_over_multiple_legacy_rows_no_crash(self, db, test_user):
        """The #48 crash repro: two same-user programs missing program_id must
        not collide on index creation. Non-unique index → init_beanie succeeds."""
        await db["programs"].insert_many([
            _legacy_program("leg-a", test_user.id, "A"),
            _legacy_program("leg-b", test_user.id, "B"),
        ])

        # Rebuild indexes against the dirty rows; with the old UNIQUE index this
        # raised DuplicateKeyError. It must not raise now.
        client = AsyncMongoClient("mongodb://localhost:27017")
        try:
            await init_beanie(
                database=client["gymcoach_test"],
                document_models=[User, Exercise, Program, Workout, Setting],
            )
        finally:
            await client.aclose()
