"""Behavioural tests for the versioned-program-rows model.

These drive the public API (and the pure lineage-resolution helpers) and assert
contract/behaviour — "current is the latest edit", "old templates survive
edits", "a lineage deletes whole" — never internal call shapes or private state.
"""

import pytest
import pytest_asyncio
from pymongo.errors import DuplicateKeyError

from app.exercises.models import Exercise
from app.programs.models import Program
from app.programs.service import get_current_program, get_program_version
from app.workouts.models import Workout


@pytest_asyncio.fixture
async def seed_exercises(db):
    """Two distinguishable exercises so template swaps are observable."""
    bench = Exercise(name="Bench Press", muscle_group="Chest", equipment="Barbell", is_custom=False)
    squat = Exercise(name="Squat", muscle_group="Legs", equipment="Barbell", is_custom=False)
    await bench.insert()
    await squat.insert()
    return {"bench": bench, "squat": squat}


def _program_payload(name: str, exercise_id: str, target_reps: int = 8):
    return {
        "name": name,
        "exercises": [
            {
                "exercise_id": exercise_id,
                "order": 1,
                "sets": [{"set_number": 1, "target_reps": target_reps, "target_weight_kg": 60.0}],
            }
        ],
    }


async def _create(client, name, exercise_id):
    resp = await client.post("/api/programs", json=_program_payload(name, exercise_id))
    assert resp.status_code == 201
    return resp.json()


class TestCurrentResolution:
    @pytest.mark.asyncio
    async def test_current_is_the_highest_version(self, client, seed_exercises):
        created = await _create(client, "Prog", seed_exercises["bench"].id)
        lineage = created["id"]

        await client.put(f"/api/programs/{lineage}", json=_program_payload("V2", seed_exercises["bench"].id))
        await client.put(f"/api/programs/{lineage}", json=_program_payload("V3", seed_exercises["squat"].id))

        resp = await client.get(f"/api/programs/{lineage}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["current_version"] == 3
        assert body["name"] == "V3"
        assert body["exercises"][0]["exercise"]["name"] == "Squat"


class TestUpdateInsertsNewRow:
    @pytest.mark.asyncio
    async def test_update_bumps_version_and_keeps_old_row_fetchable(self, client, seed_exercises):
        created = await _create(client, "Original", seed_exercises["bench"].id)
        lineage = created["id"]
        assert created["current_version"] == 1

        updated = (
            await client.put(f"/api/programs/{lineage}", json=_program_payload("Edited", seed_exercises["squat"].id))
        ).json()
        assert updated["current_version"] == 2

        # The original row is untouched history, still resolvable by its version.
        v1 = await get_program_version(lineage, 1)
        assert v1 is not None
        assert v1.name == "Original"
        assert v1.exercises[0].exercise_name == "Bench Press"

        # ...and the lineage now has two distinct rows.
        rows = await Program.find(Program.program_id == lineage).to_list()
        assert sorted(r.version for r in rows) == [1, 2]


class TestListLatestPerLineage:
    @pytest.mark.asyncio
    async def test_list_returns_only_latest_version_of_each_program(self, client, seed_exercises):
        prog_a = await _create(client, "A", seed_exercises["bench"].id)
        prog_b = await _create(client, "B", seed_exercises["squat"].id)
        # Edit A twice; B once. Six rows exist; list must still show two programs.
        await client.put(f"/api/programs/{prog_a['id']}", json=_program_payload("A2", seed_exercises["bench"].id))
        await client.put(f"/api/programs/{prog_a['id']}", json=_program_payload("A3", seed_exercises["bench"].id))
        await client.put(f"/api/programs/{prog_b['id']}", json=_program_payload("B2", seed_exercises["squat"].id))

        listing = (await client.get("/api/programs")).json()
        by_id = {p["id"]: p for p in listing}
        assert len(listing) == 2
        assert by_id[prog_a["id"]]["current_version"] == 3
        assert by_id[prog_a["id"]]["name"] == "A3"
        assert by_id[prog_b["id"]]["current_version"] == 2


class TestDeleteWholeLineage:
    @pytest.mark.asyncio
    async def test_delete_removes_every_version(self, client, seed_exercises):
        created = await _create(client, "Doomed", seed_exercises["bench"].id)
        lineage = created["id"]
        await client.put(f"/api/programs/{lineage}", json=_program_payload("Doomed2", seed_exercises["squat"].id))

        resp = await client.delete(f"/api/programs/{lineage}")
        assert resp.status_code == 204

        # No stale older version may survive to be resurrected as "current".
        remaining = await Program.find(Program.program_id == lineage).to_list()
        assert remaining == []
        assert (await client.get(f"/api/programs/{lineage}")).status_code == 404


class TestWorkoutPinsVersion:
    @pytest.mark.asyncio
    async def test_start_workout_pins_current_version(self, client, seed_exercises):
        created = await _create(client, "Prog", seed_exercises["bench"].id)
        lineage = created["id"]
        await client.put(f"/api/programs/{lineage}", json=_program_payload("Prog2", seed_exercises["squat"].id))

        start = await client.post("/api/workouts", json={"program_id": lineage})
        assert start.status_code == 201
        workout = await Workout.get(start.json()["id"])
        assert workout.program_id == lineage
        assert workout.program_version == 2  # the resolved current version

    @pytest.mark.asyncio
    async def test_pinned_version_resolves_old_template_after_later_edits(self, client, seed_exercises):
        created = await _create(client, "Bench day", seed_exercises["bench"].id)
        lineage = created["id"]

        start = await client.post("/api/workouts", json={"program_id": lineage})
        workout = await Workout.get(start.json()["id"])
        pinned = workout.program_version

        # Program is edited away from Bench after the workout was started.
        await client.put(f"/api/programs/{lineage}", json=_program_payload("Squat day", seed_exercises["squat"].id))

        # Resolving by the workout's pinned version yields the ORIGINAL template,
        # while "current" has moved on — and we never used max() to get history.
        historical = await get_program_version(lineage, pinned)
        assert historical.exercises[0].exercise_name == "Bench Press"
        current = await get_current_program(lineage)
        assert current.exercises[0].exercise_name == "Squat"


class TestOwnership:
    @pytest.mark.asyncio
    async def test_other_users_program_is_not_accessible(self, client, db, test_user, seed_exercises):
        # A lineage owned by someone else, written straight to the collection.
        foreign = Program(
            program_id="foreign-lineage",
            version=1,
            user_id="someone-else",
            name="Not Yours",
            exercises=[],
        )
        await foreign.insert()

        assert (await client.get("/api/programs/foreign-lineage")).status_code == 404
        assert (
            await client.put("/api/programs/foreign-lineage", json=_program_payload("Hack", seed_exercises["bench"].id))
        ).status_code == 404
        assert (await client.delete("/api/programs/foreign-lineage")).status_code == 404
        # The foreign row is untouched by the rejected edit/delete.
        assert await Program.find(Program.program_id == "foreign-lineage").count() == 1


class TestUniqueVersionIndex:
    @pytest.mark.asyncio
    async def test_duplicate_user_program_version_is_rejected(self, db, test_user):
        row = Program(program_id="lin-1", version=1, user_id=test_user.id, name="One", exercises=[])
        await row.insert()

        clash = Program(program_id="lin-1", version=1, user_id=test_user.id, name="Clash", exercises=[])
        with pytest.raises(DuplicateKeyError):
            await clash.insert()
