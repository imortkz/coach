"""Tests for Exercise CRUD API endpoints — async MongoDB."""

import pytest
import pytest_asyncio

from app.exercises.models import Exercise
from app.programs.models import Program, ProgramExercise


@pytest_asyncio.fixture
async def seed_exercises(db):
    """Insert seed exercises into the database."""
    exercises = [
        Exercise(name="Bench Press", muscle_group="Chest", equipment="Barbell", is_custom=False),
        Exercise(name="Squat", muscle_group="Legs", equipment="Barbell", is_custom=False),
        Exercise(name="Bicep Curl", muscle_group="Arms", equipment="Dumbbell", is_custom=False),
    ]
    for ex in exercises:
        await ex.insert()
    return exercises


@pytest_asyncio.fixture
async def custom_exercise(db, test_user):
    """Insert a custom exercise owned by test_user."""
    from app.config import DEV_USER_ID
    ex = Exercise(user_id=DEV_USER_ID, name="My Custom Press", muscle_group="Chest", equipment="Machine", is_custom=True)
    await ex.insert()
    return ex


class TestListExercises:
    @pytest.mark.asyncio
    async def test_list_all_exercises(self, client, seed_exercises):
        response = await client.get("/api/exercises")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be ordered by muscle_group, then name
        names = [e["name"] for e in data]
        assert names == ["Bicep Curl", "Bench Press", "Squat"]

    @pytest.mark.asyncio
    async def test_filter_by_muscle_group(self, client, seed_exercises):
        response = await client.get("/api/exercises?muscle_group=Chest")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Bench Press"

    @pytest.mark.asyncio
    async def test_filter_by_equipment(self, client, seed_exercises):
        response = await client.get("/api/exercises?equipment=Barbell")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = {e["name"] for e in data}
        assert names == {"Bench Press", "Squat"}

    @pytest.mark.asyncio
    async def test_filter_by_search(self, client, seed_exercises):
        response = await client.get("/api/exercises?search=bench")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Bench Press"

    @pytest.mark.asyncio
    async def test_filter_multiple(self, client, seed_exercises):
        response = await client.get("/api/exercises?muscle_group=Legs&equipment=Barbell")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Squat"


class TestCreateExercise:
    @pytest.mark.asyncio
    async def test_create_exercise(self, client, db):
        response = await client.post("/api/exercises", json={
            "name": "Cable Fly",
            "muscle_group": "Chest",
            "equipment": "Cable",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Cable Fly"
        assert data["is_custom"] is True

    @pytest.mark.asyncio
    async def test_create_exercise_missing_name(self, client, db):
        response = await client.post("/api/exercises", json={
            "muscle_group": "Chest",
            "equipment": "Cable",
        })
        assert response.status_code == 422


class TestUpdateExercise:
    @pytest.mark.asyncio
    async def test_update_custom_exercise(self, client, custom_exercise):
        response = await client.put(f"/api/exercises/{custom_exercise.id}", json={
            "name": "Updated Press",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Press"
        assert data["muscle_group"] == "Chest"  # unchanged

    @pytest.mark.asyncio
    async def test_update_seeded_exercise_returns_403(self, client, seed_exercises):
        ex = seed_exercises[0]
        response = await client.put(f"/api/exercises/{ex.id}", json={
            "name": "Renamed",
        })
        assert response.status_code == 403


class TestDeleteExercise:
    @pytest.mark.asyncio
    async def test_delete_custom_exercise(self, client, custom_exercise):
        response = await client.delete(f"/api/exercises/{custom_exercise.id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_seeded_exercise_returns_403(self, client, seed_exercises):
        ex = seed_exercises[0]
        response = await client.delete(f"/api/exercises/{ex.id}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_exercise_in_use_returns_409(self, client, db, test_user, custom_exercise):
        # Create a program that uses this exercise
        program = Program(
            user_id=test_user.id,
            name="Test Program",
            exercises=[ProgramExercise(
                exercise_id=custom_exercise.id,
                exercise_name=custom_exercise.name,
                order=1,
            )],
        )
        await program.insert()

        response = await client.delete(f"/api/exercises/{custom_exercise.id}")
        assert response.status_code == 409
        assert "used in" in response.json()["detail"].lower()


@pytest_asyncio.fixture
async def other_users_exercise(db):
    """Insert a custom exercise owned by a DIFFERENT user."""
    ex = Exercise(
        user_id="some-other-user",
        name="Their Secret Press",
        muscle_group="Chest",
        equipment="Machine",
        is_custom=True,
    )
    await ex.insert()
    return ex


class TestGetExercise:
    @pytest.mark.asyncio
    async def test_get_nonexistent_exercise_returns_404(self, client, db):
        response = await client.get("/api/exercises/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_other_users_exercise_returns_404(self, client, other_users_exercise):
        response = await client.get(f"/api/exercises/{other_users_exercise.id}")
        assert response.status_code == 404


class TestExerciseHistory:
    @pytest.mark.asyncio
    async def test_history_nonexistent_exercise_returns_404(self, client, db):
        response = await client.get("/api/exercises/nonexistent-id/history")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_history_other_users_exercise_returns_404(self, client, other_users_exercise):
        response = await client.get(f"/api/exercises/{other_users_exercise.id}/history")
        assert response.status_code == 404
