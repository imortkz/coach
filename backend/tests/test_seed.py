"""Tests for seed_exercises() upsert behavior."""

import pytest
import pytest_asyncio

from app.exercises.models import Exercise
from app.seed import SEED_EXERCISES, seed_exercises


@pytest.mark.asyncio
async def test_seed_inserts_on_empty_db(db):
    """seed_exercises() populates exercises collection when empty."""
    count_before = await Exercise.find({"user_id": None}).count()
    assert count_before == 0

    result = await seed_exercises()
    assert result == len(SEED_EXERCISES)

    count_after = await Exercise.find({"user_id": None}).count()
    assert count_after == len(SEED_EXERCISES)


@pytest.mark.asyncio
async def test_seed_is_idempotent(db):
    """Running seed_exercises() twice does not increase the count."""
    await seed_exercises()
    count_first = await Exercise.find({"user_id": None}).count()

    await seed_exercises()
    count_second = await Exercise.find({"user_id": None}).count()

    assert count_first == count_second == len(SEED_EXERCISES)


@pytest.mark.asyncio
async def test_seed_does_not_touch_custom_exercises(db):
    """Custom exercises (user_id != None) are untouched by seed."""
    # Insert a custom exercise that has the same name as a seed entry
    custom = Exercise(
        user_id="user-123",
        name="Barbell Bench Press",
        muscle_group="Chest",
        equipment="Barbell",
        is_custom=True,
    )
    await custom.insert()

    await seed_exercises()

    # Custom exercise still exists unchanged
    custom_after = await Exercise.get(custom.id)
    assert custom_after is not None
    assert custom_after.user_id == "user-123"
    assert custom_after.is_custom is True

    # Seeded variant (user_id=None) also exists separately
    seeded_variant = await Exercise.find_one({"name": "Barbell Bench Press", "user_id": None})
    assert seeded_variant is not None


@pytest.mark.asyncio
async def test_seed_fields_present_in_api(client, db):
    """Seeded exercises expose name_ru and gif_url fields via the API."""
    await seed_exercises()

    resp = await client.get("/api/exercises/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0

    # All items must have name_ru and gif_url keys (may be None)
    for item in data:
        assert "name_ru" in item
        assert "gif_url" in item

    # At least one seeded entry should have a non-null name_ru (e.g. Barbell Bench Press)
    names_with_ru = [e["name_ru"] for e in data if e["name"] == "Barbell Bench Press"]
    assert names_with_ru and names_with_ru[0] == "Жим штанги лёжа"


@pytest.mark.asyncio
async def test_seed_upsert_updates_existing_doc(db):
    """Re-running seed updates fields on existing seeded docs without changing _id."""
    await seed_exercises()

    # Grab a seeded doc and manually clear name_ru
    doc = await Exercise.find_one({"name": "Deadlift", "user_id": None})
    assert doc is not None
    original_id = doc.id

    # Manually blank name_ru
    collection = Exercise.get_pymongo_collection()
    await collection.update_one({"_id": doc.id}, {"$set": {"name_ru": None}})

    # Re-run seed
    await seed_exercises()

    # name_ru should be restored, _id unchanged
    doc_after = await Exercise.find_one({"name": "Deadlift", "user_id": None})
    assert doc_after is not None
    assert doc_after.id == original_id
    assert doc_after.name_ru == "Становая тяга"
