# S01: Backend model + expanded seed with upsert

**Goal:** Add `name_ru` and `gif_url` to the `Exercise` model and seed ~150 exercises via upsert-by-name strategy.
**Demo:** `GET /api/exercises` returns `name_ru` and `gif_url` fields; ~150 exercises present after seeding; all backend tests pass.

## Must-Haves

- `Exercise` Beanie document has `name_ru: str | None` and `gif_url: str | None`
- `ExerciseRead` Pydantic schema exposes both fields
- `_exercise_to_read()` passes new fields through
- `seed_exercises()` uses bulk_write upsert-by-name (replaces `seed_exercises_if_empty()`)
- `app/main.py` calls `seed_exercises()` at startup
- ~150 exercises across 6 muscle groups with Russian names
- All backend tests pass (≥59)

## Verification

- `uv run pytest tests/ -q` → all tests pass

## Tasks

- [x] **T01: Add fields, expand seed, switch to upsert** `est:1h`
  - Why: Core deliverable of this slice
  - Files: `app/exercises/models.py`, `app/exercises/schemas.py`, `app/exercises/routes.py`, `app/seed.py`, `app/main.py`
  - Do: Add name_ru/gif_url to model+schema, expand SEED_EXERCISES to ~150 entries with Russian names, replace seed_exercises_if_empty with upsert-based seed_exercises using pymongo bulk_write UpdateOne
  - Verify: `uv run pytest tests/ -q` passes
  - Done when: 64+ tests pass, `GET /api/exercises` response includes name_ru and gif_url

## Files Likely Touched

- `../backend/app/exercises/models.py`
- `../backend/app/exercises/schemas.py`
- `../backend/app/exercises/routes.py`
- `../backend/app/seed.py`
- `../backend/app/main.py`
