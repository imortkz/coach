"""Tests for Workout logging API endpoints — async MongoDB."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from app.auth.models import User
from app.config import DEV_USER_ID
from app.exercises.models import Exercise
from app.programs.models import Program, ProgramExercise, ProgramSet
from app.workouts.models import Workout, WorkoutSet


@pytest_asyncio.fixture
async def seed_exercises(db):
    """Insert seed exercises for workout tests."""
    exercises = [
        Exercise(name="Bench Press", muscle_group="Chest", equipment="Barbell", is_custom=False),
        Exercise(name="Squat", muscle_group="Legs", equipment="Barbell", is_custom=False),
    ]
    for ex in exercises:
        await ex.insert()
    return exercises


@pytest_asyncio.fixture
async def seed_program(db, test_user, seed_exercises):
    """Create a program with 2 exercises, each with 2 sets."""
    exercises = []
    for i, ex in enumerate(seed_exercises):
        exercises.append(ProgramExercise(
            exercise_id=ex.id,
            exercise_name=ex.name,
            exercise_muscle_group=ex.muscle_group,
            exercise_equipment=ex.equipment,
            order=i + 1,
            sets=[
                ProgramSet(set_number=1, target_reps=8, target_weight_kg=60.0 + i * 20, is_warmup=True),
                ProgramSet(set_number=2, target_reps=8, target_weight_kg=60.0 + i * 20, is_warmup=False),
            ],
        ))

    program = Program(user_id=test_user.id, name="Test Program", exercises=exercises)
    await program.insert()
    return program


class TestStartWorkout:
    @pytest.mark.asyncio
    async def test_start_workout(self, client, seed_program):
        resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        assert resp.status_code == 201
        data = resp.json()
        assert data["started_at"] is not None
        assert data["completed_at"] is None
        assert "pre_fill" in data
        assert len(data["pre_fill"]) > 0

    @pytest.mark.asyncio
    async def test_start_workout_invalid_program(self, client, db):
        resp = await client.post("/api/workouts", json={"program_id": "nonexistent"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_start_workout_with_another_users_program_returns_404(self, client, db):
        """A program owned by someone else is indistinguishable from a missing one."""
        others_program = Program(user_id="some-other-user", name="Their Split", exercises=[])
        await others_program.insert()

        resp = await client.post("/api/workouts", json={"program_id": others_program.program_id})

        assert resp.status_code == 404
        # Nothing was started for the requesting user.
        assert await Workout.find(Workout.user_id == DEV_USER_ID).to_list() == []


class TestActiveWorkout:
    @pytest.mark.asyncio
    async def test_active_workout(self, client, seed_program):
        await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        resp = await client.get("/api/workouts/active")
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed_at"] is None
        assert "sets" in data

    @pytest.mark.asyncio
    async def test_active_workout_none(self, client, db):
        resp = await client.get("/api/workouts/active")
        assert resp.status_code == 404


class TestLogSet:
    @pytest.mark.asyncio
    async def test_log_set(self, client, seed_program, seed_exercises):
        create_resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        workout_id = create_resp.json()["id"]

        resp = await client.post(f"/api/workouts/{workout_id}/sets", json={
            "exercise_id": seed_exercises[0].id,
            "set_number": 1,
            "weight_kg": 60.0,
            "reps": 8,
            "is_warmup": False,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["exercise_id"] == seed_exercises[0].id
        assert data["weight_kg"] == 60.0
        assert data["reps"] == 8
        assert data["exercise"] is not None
        assert data["exercise"]["name"] == "Bench Press"


class TestUpdateSet:
    @pytest.mark.asyncio
    async def test_update_set(self, client, seed_program, seed_exercises):
        create_resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        workout_id = create_resp.json()["id"]

        set_resp = await client.post(f"/api/workouts/{workout_id}/sets", json={
            "exercise_id": seed_exercises[0].id,
            "set_number": 1,
            "weight_kg": 60.0,
            "reps": 8,
        })
        set_id = set_resp.json()["id"]

        resp = await client.put(f"/api/workouts/{workout_id}/sets/{set_id}", json={
            "weight_kg": 65.0,
            "reps": 6,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["weight_kg"] == 65.0
        assert data["reps"] == 6


    @pytest.mark.asyncio
    async def test_update_set_not_found_returns_404(self, client, seed_program):
        create_resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        workout_id = create_resp.json()["id"]

        resp = await client.put(f"/api/workouts/{workout_id}/sets/nonexistent-set", json={
            "weight_kg": 65.0,
        })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_set_partial_leaves_weight_unchanged(self, client, seed_program, seed_exercises):
        create_resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        workout_id = create_resp.json()["id"]

        set_resp = await client.post(f"/api/workouts/{workout_id}/sets", json={
            "exercise_id": seed_exercises[0].id,
            "set_number": 1,
            "weight_kg": 60.0,
            "reps": 8,
        })
        set_id = set_resp.json()["id"]

        resp = await client.put(f"/api/workouts/{workout_id}/sets/{set_id}", json={
            "reps": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["reps"] == 5
        assert data["weight_kg"] == 60.0  # unchanged


class TestDeleteSet:
    @pytest.mark.asyncio
    async def test_delete_set(self, client, seed_program, seed_exercises):
        create_resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        workout_id = create_resp.json()["id"]

        set_resp = await client.post(f"/api/workouts/{workout_id}/sets", json={
            "exercise_id": seed_exercises[0].id,
            "set_number": 1,
            "weight_kg": 60.0,
            "reps": 8,
        })
        set_id = set_resp.json()["id"]

        resp = await client.delete(f"/api/workouts/{workout_id}/sets/{set_id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_set_not_found_returns_404(self, client, seed_program):
        create_resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        workout_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/workouts/{workout_id}/sets/nonexistent-set")
        assert resp.status_code == 404


class TestDeleteExerciseSets:
    @pytest.mark.asyncio
    async def test_delete_exercise_sets(self, client, seed_program, seed_exercises):
        create_resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        workout_id = create_resp.json()["id"]

        for s in range(1, 3):
            await client.post(f"/api/workouts/{workout_id}/sets", json={
                "exercise_id": seed_exercises[0].id,
                "set_number": s,
                "weight_kg": 60.0,
                "reps": 8,
            })

        resp = await client.delete(f"/api/workouts/{workout_id}/exercises/{seed_exercises[0].id}")
        assert resp.status_code == 204

        workout_resp = await client.get(f"/api/workouts/{workout_id}")
        assert workout_resp.status_code == 200
        remaining = [s for s in workout_resp.json()["sets"]
                     if s["exercise_id"] == seed_exercises[0].id]
        assert len(remaining) == 0


class TestDiscardWorkout:
    @pytest.mark.asyncio
    async def test_discard_workout(self, client, seed_program):
        create_resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        workout_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/workouts/{workout_id}")
        assert resp.status_code == 204

        get_resp = await client.get(f"/api/workouts/{workout_id}")
        assert get_resp.status_code == 404


class TestCompleteWorkout:
    @pytest.mark.asyncio
    async def test_complete_workout(self, client, seed_program):
        create_resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        workout_id = create_resp.json()["id"]

        resp = await client.patch(f"/api/workouts/{workout_id}/complete")
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed_at"] is not None


class TestPreFill:
    @pytest.mark.asyncio
    async def test_prefill_last_session(self, client, seed_program, seed_exercises):
        w1 = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        w1_id = w1.json()["id"]

        await client.post(f"/api/workouts/{w1_id}/sets", json={
            "exercise_id": seed_exercises[0].id,
            "set_number": 1,
            "weight_kg": 65.0,
            "reps": 10,
            "is_warmup": True,
        })
        await client.post(f"/api/workouts/{w1_id}/sets", json={
            "exercise_id": seed_exercises[0].id,
            "set_number": 2,
            "weight_kg": 70.0,
            "reps": 8,
            "is_warmup": False,
        })

        await client.patch(f"/api/workouts/{w1_id}/complete")

        w2 = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        assert w2.status_code == 201
        pre_fill = w2.json()["pre_fill"]

        ex_id = seed_exercises[0].id
        assert ex_id in pre_fill
        fills = pre_fill[ex_id]
        assert len(fills) == 2
        assert fills[0]["weight_kg"] == 65.0
        assert fills[0]["reps"] == 10
        assert fills[1]["weight_kg"] == 70.0
        assert fills[1]["reps"] == 8

    @pytest.mark.asyncio
    async def test_prefill_fallback_to_program(self, client, seed_program, seed_exercises):
        resp = await client.post("/api/workouts", json={"program_id": seed_program.program_id})
        assert resp.status_code == 201
        pre_fill = resp.json()["pre_fill"]

        ex_id = seed_exercises[0].id
        assert ex_id in pre_fill
        fills = pre_fill[ex_id]
        assert len(fills) == 2
        assert fills[0]["weight_kg"] == 60.0
        assert fills[0]["reps"] == 8


class TestSettings:
    @pytest.mark.asyncio
    async def test_settings_crud(self, client, db):
        resp = await client.get("/api/settings/rest_timer_seconds")
        assert resp.status_code == 404

        resp = await client.put("/api/settings/rest_timer_seconds", json={"value": "90"})
        assert resp.status_code == 200
        assert resp.json()["key"] == "rest_timer_seconds"
        assert resp.json()["value"] == "90"

        resp = await client.get("/api/settings/rest_timer_seconds")
        assert resp.status_code == 200
        assert resp.json()["value"] == "90"


class TestProgramRestTimerDisabled:
    @pytest.mark.asyncio
    async def test_program_rest_timer_disabled(self, client, seed_program):
        resp = await client.get(f"/api/programs/{seed_program.program_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "rest_timer_disabled" in data
        assert data["rest_timer_disabled"] is False


class TestListWorkouts:
    @pytest.mark.asyncio
    async def test_list_completed_workouts(self, client, db, test_user, seed_exercises):
        """Create completed workouts directly and list them."""
        base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(3):
            w = Workout(
                user_id=test_user.id,
                started_at=base_time + timedelta(days=i),
                completed_at=base_time + timedelta(days=i, hours=1),
                sets=[WorkoutSet(
                    exercise_id=seed_exercises[0].id,
                    exercise_name=seed_exercises[0].name,
                    set_number=1,
                    weight_kg=60.0,
                    reps=8,
                )],
            )
            await w.insert()

        resp = await client.get("/api/workouts")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 3
        dates = [w["completed_at"] for w in items]
        assert dates == sorted(dates, reverse=True)
        assert len(items[0]["sets"]) > 0
        assert items[0]["sets"][0]["exercise"] is not None

    @pytest.mark.asyncio
    async def test_excludes_active_workouts(self, client, db, test_user, seed_exercises):
        # Completed
        w1 = Workout(
            user_id=test_user.id,
            completed_at=datetime.now(timezone.utc),
            sets=[],
        )
        await w1.insert()
        # Active (no completed_at)
        w2 = Workout(user_id=test_user.id, sets=[])
        await w2.insert()

        resp = await client.get("/api/workouts")
        items = resp.json()["items"]
        ids = [w["id"] for w in items]
        assert w2.id not in ids
        assert w1.id in ids

    @pytest.mark.asyncio
    async def test_filter_by_program_id(self, client, db, test_user, seed_exercises):
        now = datetime.now(timezone.utc)
        w_prog_a = Workout(
            user_id=test_user.id, program_id="prog-a",
            completed_at=now, sets=[],
        )
        await w_prog_a.insert()
        w_prog_b = Workout(
            user_id=test_user.id, program_id="prog-b",
            completed_at=now, sets=[],
        )
        await w_prog_b.insert()

        resp = await client.get("/api/workouts?program_id=prog-a")
        assert resp.status_code == 200
        ids = [w["id"] for w in resp.json()["items"]]
        assert ids == [w_prog_a.id]

    @pytest.mark.asyncio
    async def test_limit_capped_at_100(self, client, db, test_user, seed_exercises):
        base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(105):
            w = Workout(
                user_id=test_user.id,
                completed_at=base_time + timedelta(minutes=i),
                sets=[],
            )
            await w.insert()

        resp = await client.get("/api/workouts?limit=500")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 100


class TestExerciseHistory:
    @pytest.mark.asyncio
    async def test_returns_sessions(self, client, db, test_user, seed_exercises):
        base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(3):
            w = Workout(
                user_id=test_user.id,
                started_at=base_time + timedelta(days=i),
                completed_at=base_time + timedelta(days=i, hours=1),
                sets=[
                    WorkoutSet(
                        exercise_id=seed_exercises[0].id,
                        exercise_name="Bench Press",
                        exercise_equipment="Barbell",
                        set_number=s,
                        weight_kg=60.0 + i * 2.5,
                        reps=8,
                        is_warmup=(s == 1),
                    )
                    for s in range(1, 4)
                ],
            )
            await w.insert()

        ex_id = seed_exercises[0].id
        resp = await client.get(f"/api/exercises/{ex_id}/history")
        assert resp.status_code == 200
        data = resp.json()
        sessions = data["sessions"]
        assert len(sessions) == 3
        s = sessions[0]  # Most recent
        assert s["best_weight"] == 65.0
        assert s["total_volume"] == 1040.0


class TestProgression:
    @pytest.mark.asyncio
    async def test_suggest_increase(self, client, db, test_user, seed_exercises, seed_program):
        w = Workout(
            user_id=test_user.id,
            program_id=seed_program.program_id,
            started_at=datetime(2026, 3, 5, tzinfo=timezone.utc),
            completed_at=datetime(2026, 3, 5, 1, tzinfo=timezone.utc),
            sets=[
                WorkoutSet(
                    exercise_id=seed_exercises[0].id,
                    exercise_name="Bench Press",
                    exercise_equipment="Barbell",
                    set_number=1, weight_kg=40.0, reps=10, is_warmup=True,
                ),
                WorkoutSet(
                    exercise_id=seed_exercises[0].id,
                    exercise_name="Bench Press",
                    exercise_equipment="Barbell",
                    set_number=2, weight_kg=60.0, reps=8, is_warmup=False,
                ),
                WorkoutSet(
                    exercise_id=seed_exercises[0].id,
                    exercise_name="Bench Press",
                    exercise_equipment="Barbell",
                    set_number=3, weight_kg=60.0, reps=8, is_warmup=False,
                ),
            ],
        )
        await w.insert()

        resp = await client.get(
            f"/api/exercises/{seed_exercises[0].id}/history?program_id={seed_program.program_id}"
        )
        assert resp.status_code == 200
        suggestion = resp.json()["suggestion"]
        assert suggestion is not None
        assert suggestion["type"] == "weight"
        assert suggestion["suggested_weight_kg"] == 62.5
        assert suggestion["reason"] == "hit_target"

    @pytest.mark.asyncio
    async def test_keep_weight(self, client, db, test_user, seed_exercises, seed_program):
        w = Workout(
            user_id=test_user.id,
            program_id=seed_program.program_id,
            started_at=datetime(2026, 3, 5, tzinfo=timezone.utc),
            completed_at=datetime(2026, 3, 5, 1, tzinfo=timezone.utc),
            sets=[
                WorkoutSet(
                    exercise_id=seed_exercises[0].id,
                    exercise_name="Bench Press",
                    exercise_equipment="Barbell",
                    set_number=1, weight_kg=60.0, reps=8, is_warmup=False,
                ),
                WorkoutSet(
                    exercise_id=seed_exercises[0].id,
                    exercise_name="Bench Press",
                    exercise_equipment="Barbell",
                    set_number=2, weight_kg=60.0, reps=6, is_warmup=False,
                ),
            ],
        )
        await w.insert()

        resp = await client.get(
            f"/api/exercises/{seed_exercises[0].id}/history?program_id={seed_program.program_id}"
        )
        suggestion = resp.json()["suggestion"]
        assert suggestion["type"] == "keep"
        assert suggestion["suggested_weight_kg"] == 60.0
        assert suggestion["reason"] == "missed_reps"

    @pytest.mark.asyncio
    async def test_bodyweight_rep_increase(self, client, db, test_user, seed_program):
        bw_ex = Exercise(name="Pull-up", muscle_group="Back", equipment="Bodyweight", is_custom=False)
        await bw_ex.insert()

        # Add to program
        seed_program.exercises.append(ProgramExercise(
            exercise_id=bw_ex.id,
            exercise_name=bw_ex.name,
            exercise_equipment=bw_ex.equipment,
            order=3,
            sets=[ProgramSet(set_number=1, target_reps=8, target_weight_kg=None, is_warmup=False)],
        ))
        await seed_program.save()

        w = Workout(
            user_id=test_user.id,
            program_id=seed_program.program_id,
            started_at=datetime(2026, 3, 5, tzinfo=timezone.utc),
            completed_at=datetime(2026, 3, 5, 1, tzinfo=timezone.utc),
            sets=[
                WorkoutSet(
                    exercise_id=bw_ex.id,
                    exercise_name="Pull-up",
                    exercise_equipment="Bodyweight",
                    set_number=1, weight_kg=None, reps=8, is_warmup=False,
                ),
            ],
        )
        await w.insert()

        resp = await client.get(f"/api/exercises/{bw_ex.id}/history?program_id={seed_program.program_id}")
        suggestion = resp.json()["suggestion"]
        assert suggestion["type"] == "reps"
        assert suggestion["suggested_reps"] == 9
        assert suggestion["reason"] == "hit_target"

    @pytest.mark.asyncio
    async def test_user_increment_override(self, client, db, test_user, seed_exercises, seed_program):
        """A per-user progression_increment_<equipment> Setting overrides the default."""
        from app.workouts.models import Setting

        # Bench Press is Barbell (default increment 2.5). Override it to 5.0 for this user.
        await Setting(
            user_id=test_user.id, key="progression_increment_barbell", value="5.0"
        ).insert()

        w = Workout(
            user_id=test_user.id,
            program_id=seed_program.program_id,
            started_at=datetime(2026, 3, 5, tzinfo=timezone.utc),
            completed_at=datetime(2026, 3, 5, 1, tzinfo=timezone.utc),
            sets=[
                WorkoutSet(
                    exercise_id=seed_exercises[0].id,
                    exercise_name="Bench Press",
                    exercise_equipment="Barbell",
                    set_number=1, weight_kg=60.0, reps=8, is_warmup=False,
                ),
            ],
        )
        await w.insert()

        resp = await client.get(
            f"/api/exercises/{seed_exercises[0].id}/history?program_id={seed_program.program_id}"
        )
        suggestion = resp.json()["suggestion"]
        assert suggestion["type"] == "weight"
        assert suggestion["increment"] == 5.0
        assert suggestion["suggested_weight_kg"] == 65.0  # 60 + 5.0 override, not + 2.5 default
        assert suggestion["reason"] == "hit_target"

    @pytest.mark.asyncio
    async def test_mixed_weights_no_suggestion(self, client, db, test_user, seed_exercises, seed_program):
        w = Workout(
            user_id=test_user.id,
            program_id=seed_program.program_id,
            started_at=datetime(2026, 3, 5, tzinfo=timezone.utc),
            completed_at=datetime(2026, 3, 5, 1, tzinfo=timezone.utc),
            sets=[
                WorkoutSet(
                    exercise_id=seed_exercises[0].id,
                    exercise_name="Bench Press",
                    exercise_equipment="Barbell",
                    set_number=1, weight_kg=60.0, reps=8, is_warmup=False,
                ),
                WorkoutSet(
                    exercise_id=seed_exercises[0].id,
                    exercise_name="Bench Press",
                    exercise_equipment="Barbell",
                    set_number=2, weight_kg=65.0, reps=8, is_warmup=False,
                ),
            ],
        )
        await w.insert()

        resp = await client.get(
            f"/api/exercises/{seed_exercises[0].id}/history?program_id={seed_program.program_id}"
        )
        assert resp.json()["suggestion"] is None
