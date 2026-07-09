"""Tests for M010 — program version-history consumer (the READER).

The versioning groundwork (PR-A1..A3) writes `Program.versions[]` snapshots and
`Workout.program_version`, but nothing read them. M010 adds:

1. `program_version` exposed on WorkoutRead so history can show a "done on vN" badge.
2. GET /programs/{program_id}/versions/{version} — a read-only snapshot of how the
   program looked at that version (live `exercises` when version == current_version,
   else the matching entry in `versions[]`).
"""

import pytest
import pytest_asyncio

from app.auth.models import User
from app.exercises.models import Exercise


@pytest_asyncio.fixture
async def seed_exercises(db):
    exercises = [
        Exercise(name="Bench Press", muscle_group="Chest", equipment="Barbell", is_custom=False),
        Exercise(name="Squat", muscle_group="Legs", equipment="Barbell", is_custom=False),
        Exercise(name="Deadlift", muscle_group="Back", equipment="Barbell", is_custom=False),
    ]
    for ex in exercises:
        await ex.insert()
    return exercises


async def _create_program(client, name, exercises_payload):
    r = await client.post("/api/programs/", json={
        "name": name,
        "rest_timer_disabled": False,
        "exercises": exercises_payload,
    })
    assert r.status_code == 201, r.text
    return r.json()


def _one_exercise(ex, order=1, reps=8, weight=60.0):
    return {
        "exercise_id": ex.id,
        "order": order,
        "sets": [
            {"set_number": 1, "target_reps": reps, "target_weight_kg": weight, "is_warmup": False},
        ],
    }


class TestWorkoutExposesProgramVersion:
    @pytest.mark.asyncio
    async def test_start_and_get_workout_carries_program_version(self, client, seed_exercises):
        program = await _create_program(client, "День 1", [_one_exercise(seed_exercises[0])])

        start = await client.post("/api/workouts", json={"program_id": program["id"]})
        assert start.status_code == 201
        workout_id = start.json()["id"]

        got = await client.get(f"/api/workouts/{workout_id}")
        assert got.status_code == 200
        assert got.json()["program_version"] == 1

    @pytest.mark.asyncio
    async def test_workout_list_carries_program_version(self, client, seed_exercises):
        program = await _create_program(client, "День 1", [_one_exercise(seed_exercises[0])])
        start = await client.post("/api/workouts", json={"program_id": program["id"]})
        workout_id = start.json()["id"]
        await client.patch(f"/api/workouts/{workout_id}/complete")

        listed = await client.get("/api/workouts")
        assert listed.status_code == 200
        items = listed.json()["items"]
        assert len(items) == 1
        assert items[0]["program_version"] == 1


class TestProgramVersionSnapshot:
    @pytest.mark.asyncio
    async def test_current_version_returns_live_program(self, client, seed_exercises):
        program = await _create_program(
            client, "День 1", [_one_exercise(seed_exercises[0], reps=8, weight=60.0)]
        )
        pid = program["id"]

        r = await client.get(f"/api/programs/{pid}/versions/1")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["version"] == 1
        assert body["is_current"] is True
        assert body["name"] == "День 1"
        assert len(body["exercises"]) == 1
        assert body["exercises"][0]["exercise_id"] == seed_exercises[0].id
        assert body["exercises"][0]["sets"][0]["target_reps"] == 8

    @pytest.mark.asyncio
    async def test_old_version_returns_archived_snapshot(self, client, seed_exercises):
        # v1: one exercise, 8 reps.
        program = await _create_program(
            client, "День 1", [_one_exercise(seed_exercises[0], reps=8, weight=60.0)]
        )
        pid = program["id"]

        # Edit → v2: different exercise + reps.
        r2 = await client.put(f"/api/programs/{pid}", json={
            "name": "День 1 (обновлён)",
            "rest_timer_disabled": False,
            "exercises": [_one_exercise(seed_exercises[1], reps=5, weight=100.0)],
        })
        assert r2.status_code == 200

        # v1 snapshot = the archived original.
        v1 = await client.get(f"/api/programs/{pid}/versions/1")
        assert v1.status_code == 200, v1.text
        b1 = v1.json()
        assert b1["is_current"] is False
        assert b1["name"] == "День 1"
        assert b1["exercises"][0]["exercise_id"] == seed_exercises[0].id
        assert b1["exercises"][0]["sets"][0]["target_reps"] == 8

        # v2 snapshot = the live current program.
        v2 = await client.get(f"/api/programs/{pid}/versions/2")
        assert v2.status_code == 200
        b2 = v2.json()
        assert b2["is_current"] is True
        assert b2["name"] == "День 1 (обновлён)"
        assert b2["exercises"][0]["exercise_id"] == seed_exercises[1].id
        assert b2["exercises"][0]["sets"][0]["target_reps"] == 5

    @pytest.mark.asyncio
    async def test_unknown_version_returns_404(self, client, seed_exercises):
        program = await _create_program(client, "День 1", [_one_exercise(seed_exercises[0])])
        r = await client.get(f"/api/programs/{program['id']}/versions/99")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_unknown_program_returns_404(self, client, seed_exercises):
        r = await client.get("/api/programs/does-not-exist/versions/1")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_other_users_program_returns_404(self, client, db, seed_exercises):
        from app.programs.models import Program
        other = User(id="other-user", telegram_id=999, username="other", first_name="O", last_name="U")
        await other.insert()
        prog = Program(user_id=other.id, name="Чужая", exercises=[])
        await prog.insert()

        r = await client.get(f"/api/programs/{prog.id}/versions/1")
        assert r.status_code == 404
