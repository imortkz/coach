"""Tests for Program CRUD API endpoints — async MongoDB."""

import pytest
import pytest_asyncio

from app.exercises.models import Exercise


@pytest_asyncio.fixture
async def seed_exercises(db):
    """Insert seed exercises for program tests."""
    exercises = [
        Exercise(name="Bench Press", muscle_group="Chest", equipment="Barbell", is_custom=False),
        Exercise(name="Squat", muscle_group="Legs", equipment="Barbell", is_custom=False),
        Exercise(name="Overhead Press", muscle_group="Shoulders", equipment="Barbell", is_custom=False),
        Exercise(name="Barbell Row", muscle_group="Back", equipment="Barbell", is_custom=False),
    ]
    for ex in exercises:
        await ex.insert()
    return exercises


class TestCreateProgram:
    @pytest.mark.asyncio
    async def test_create_program_with_nested_exercises_and_sets(self, client, seed_exercises):
        payload = {
            "name": "Upper Body A",
            "exercises": [
                {
                    "exercise_id": seed_exercises[0].id,
                    "order": 1,
                    "sets": [
                        {"set_number": 1, "target_reps": 10, "target_weight_kg": 20.0, "is_warmup": True},
                        {"set_number": 2, "target_reps": 8, "target_weight_kg": 60.0, "is_warmup": False},
                        {"set_number": 3, "target_reps": 8, "target_weight_kg": 60.0, "is_warmup": False},
                    ],
                },
                {
                    "exercise_id": seed_exercises[2].id,
                    "order": 2,
                    "sets": [
                        {"set_number": 1, "target_reps": 10, "target_weight_kg": 30.0},
                        {"set_number": 2, "target_reps": 8, "target_weight_kg": 40.0},
                    ],
                },
            ],
        }
        response = await client.post("/api/programs", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Upper Body A"
        assert len(data["exercises"]) == 2
        assert len(data["exercises"][0]["sets"]) == 3
        assert len(data["exercises"][1]["sets"]) == 2
        assert data["exercises"][0]["exercise"]["name"] == "Bench Press"
        assert data["exercises"][0]["sets"][0]["is_warmup"] is True
        assert data["exercises"][0]["sets"][1]["is_warmup"] is False

    @pytest.mark.asyncio
    async def test_create_program_empty_name_returns_422(self, client, seed_exercises):
        payload = {"name": "", "exercises": []}
        response = await client.post("/api/programs", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_program_missing_name_returns_422(self, client, db):
        payload = {"exercises": []}
        response = await client.post("/api/programs", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_program_same_exercise_multiple_times(self, client, seed_exercises):
        payload = {
            "name": "Double Bench",
            "exercises": [
                {
                    "exercise_id": seed_exercises[0].id,
                    "order": 1,
                    "sets": [{"set_number": 1, "target_reps": 8, "target_weight_kg": 60.0}],
                },
                {
                    "exercise_id": seed_exercises[0].id,
                    "order": 2,
                    "sets": [{"set_number": 1, "target_reps": 12, "target_weight_kg": 40.0}],
                },
            ],
        }
        response = await client.post("/api/programs", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert len(data["exercises"]) == 2
        assert data["exercises"][0]["exercise_id"] == data["exercises"][1]["exercise_id"]


class TestListPrograms:
    @pytest.mark.asyncio
    async def test_list_programs_empty(self, client, db):
        response = await client.get("/api/programs")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_programs_with_nested_data(self, client, seed_exercises):
        payload = {
            "name": "Test Program",
            "exercises": [
                {
                    "exercise_id": seed_exercises[0].id,
                    "order": 1,
                    "sets": [{"set_number": 1, "target_reps": 8, "target_weight_kg": 60.0}],
                },
            ],
        }
        await client.post("/api/programs", json=payload)

        response = await client.get("/api/programs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Program"
        assert len(data[0]["exercises"]) == 1
        assert len(data[0]["exercises"][0]["sets"]) == 1
        assert data[0]["exercises"][0]["exercise"]["name"] == "Bench Press"


class TestGetProgram:
    @pytest.mark.asyncio
    async def test_get_program_detail(self, client, seed_exercises):
        payload = {
            "name": "Detail Test",
            "exercises": [
                {
                    "exercise_id": seed_exercises[1].id,
                    "order": 1,
                    "sets": [
                        {"set_number": 1, "target_reps": 5, "target_weight_kg": 100.0},
                        {"set_number": 2, "target_reps": 5, "target_weight_kg": 100.0},
                    ],
                },
            ],
        }
        create_resp = await client.post("/api/programs", json=payload)
        program_id = create_resp.json()["id"]

        response = await client.get(f"/api/programs/{program_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Detail Test"
        assert len(data["exercises"]) == 1
        assert data["exercises"][0]["exercise"]["name"] == "Squat"

    @pytest.mark.asyncio
    async def test_get_nonexistent_program_returns_404(self, client, db):
        response = await client.get("/api/programs/nonexistent-id")
        assert response.status_code == 404


class TestUpdateProgram:
    @pytest.mark.asyncio
    async def test_update_program_replaces_exercises_and_versions(self, client, seed_exercises):
        create_payload = {
            "name": "Original",
            "exercises": [
                {
                    "exercise_id": seed_exercises[0].id,
                    "order": 1,
                    "sets": [{"set_number": 1, "target_reps": 8, "target_weight_kg": 60.0}],
                },
            ],
        }
        create_resp = await client.post("/api/programs", json=create_payload)
        program_id = create_resp.json()["id"]
        assert create_resp.json()["current_version"] == 1

        update_payload = {
            "name": "Updated",
            "exercises": [
                {
                    "exercise_id": seed_exercises[1].id,
                    "order": 1,
                    "sets": [
                        {"set_number": 1, "target_reps": 5, "target_weight_kg": 100.0},
                        {"set_number": 2, "target_reps": 5, "target_weight_kg": 100.0},
                    ],
                },
                {
                    "exercise_id": seed_exercises[2].id,
                    "order": 2,
                    "sets": [{"set_number": 1, "target_reps": 10, "target_weight_kg": 40.0}],
                },
            ],
        }
        response = await client.put(f"/api/programs/{program_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["current_version"] == 2
        assert len(data["exercises"]) == 2
        assert data["exercises"][0]["exercise"]["name"] == "Squat"
        assert len(data["exercises"][0]["sets"]) == 2

    @pytest.mark.asyncio
    async def test_update_nonexistent_program_returns_404(self, client, seed_exercises):
        payload = {"name": "Ghost", "exercises": []}
        response = await client.put("/api/programs/nonexistent-id", json=payload)
        assert response.status_code == 404


class TestDeleteProgram:
    @pytest.mark.asyncio
    async def test_delete_program(self, client, seed_exercises):
        payload = {
            "name": "To Delete",
            "exercises": [
                {
                    "exercise_id": seed_exercises[0].id,
                    "order": 1,
                    "sets": [{"set_number": 1, "target_reps": 8, "target_weight_kg": 60.0}],
                },
            ],
        }
        create_resp = await client.post("/api/programs", json=payload)
        program_id = create_resp.json()["id"]

        response = await client.delete(f"/api/programs/{program_id}")
        assert response.status_code == 204

        get_resp = await client.get(f"/api/programs/{program_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_program_returns_404(self, client, db):
        response = await client.delete("/api/programs/nonexistent-id")
        assert response.status_code == 404


class TestProgramRoundTrip:
    @pytest.mark.asyncio
    async def test_full_roundtrip_complex_program(self, client, seed_exercises):
        payload = {
            "name": "Full Body Workout",
            "exercises": [
                {
                    "exercise_id": seed_exercises[0].id,
                    "order": 1,
                    "sets": [
                        {"set_number": 1, "target_reps": 10, "target_weight_kg": 20.0, "is_warmup": True},
                        {"set_number": 2, "target_reps": 8, "target_weight_kg": 60.0, "is_warmup": False},
                        {"set_number": 3, "target_reps": 8, "target_weight_kg": 60.0, "is_warmup": False},
                        {"set_number": 4, "target_reps": 6, "target_weight_kg": 65.0, "is_warmup": False},
                    ],
                },
                {
                    "exercise_id": seed_exercises[1].id,
                    "order": 2,
                    "sets": [
                        {"set_number": 1, "target_reps": 10, "target_weight_kg": 40.0, "is_warmup": True},
                        {"set_number": 2, "target_reps": 5, "target_weight_kg": 100.0},
                        {"set_number": 3, "target_reps": 5, "target_weight_kg": 100.0},
                    ],
                },
                {
                    "exercise_id": seed_exercises[3].id,
                    "order": 3,
                    "sets": [
                        {"set_number": 1, "target_reps": 10, "target_weight_kg": 40.0},
                        {"set_number": 2, "target_reps": 8, "target_weight_kg": 60.0},
                        {"set_number": 3, "target_reps": 8, "target_weight_kg": 60.0},
                    ],
                },
            ],
        }
        create_resp = await client.post("/api/programs", json=payload)
        assert create_resp.status_code == 201
        created = create_resp.json()

        get_resp = await client.get(f"/api/programs/{created['id']}")
        assert get_resp.status_code == 200
        fetched = get_resp.json()

        assert fetched["name"] == "Full Body Workout"
        assert len(fetched["exercises"]) == 3

        ex1 = fetched["exercises"][0]
        assert ex1["exercise"]["name"] == "Bench Press"
        assert ex1["order"] == 1
        assert len(ex1["sets"]) == 4
        assert ex1["sets"][0]["is_warmup"] is True
        assert ex1["sets"][1]["is_warmup"] is False

        ex2 = fetched["exercises"][1]
        assert ex2["exercise"]["name"] == "Squat"
        assert len(ex2["sets"]) == 3

        ex3 = fetched["exercises"][2]
        assert ex3["exercise"]["name"] == "Barbell Row"
        assert len(ex3["sets"]) == 3
