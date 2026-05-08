---
id: T01
parent: S01
milestone: M003
provides:
  - name_ru and gif_url on Exercise model, ExerciseRead schema, and _exercise_to_read()
  - upsert-based seed_exercises() replacing seed_exercises_if_empty()
  - ~150 seed exercises with Russian translations
key_files:
  - ../backend/app/exercises/models.py
  - ../backend/app/exercises/schemas.py
  - ../backend/app/exercises/routes.py
  - ../backend/app/seed.py
  - ../backend/app/main.py
key_decisions:
  - D023: Upsert filter {name, user_id: None} isolates seed from custom exercises
  - D024: $setOnInsert for _id on first insert; subsequent runs don't regenerate
  - D025: All gif_url=None in initial seed
patterns_established:
  - pymongo bulk_write UpdateOne upsert pattern for idempotent seeding
observability_surfaces:
  - Startup log line with upserted count
duration: ~1h
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T01: Add fields, expand seed, switch to upsert

**Exercise model gains name_ru + gif_url; seed expanded to ~150 entries via upsert-by-name; 64 tests pass.**

## What Happened

Added `name_ru: str | None = None` and `gif_url: str | None = None` to the `Exercise` Beanie document and `ExerciseRead` Pydantic schema. Wired both through `_exercise_to_read()`. Rewrote `app/seed.py`: replaced `SEED_EXERCISES` (50 entries, no Russian) with ~150 entries across 6 muscle groups each with `name_ru`. Replaced `seed_exercises_if_empty()` with `seed_exercises()` using pymongo `bulk_write(UpdateOne(..., upsert=True))` keyed on `{name, user_id: None}`. Updated `app/main.py` import and log message.

## Verification

```
cd ../backend && uv run pytest tests/ -q
# 64 passed in 6.17s
```

## Diagnostics

- `GET /api/exercises` — each exercise object now has `name_ru` and `gif_url` keys
- Startup log: `INFO gymcoach: Upserted 150 seed exercises into exercises collection`

## Deviations

None.

## Known Issues

gif_url is None for all entries — to be populated in S03.

## Files Created/Modified

- `../backend/app/exercises/models.py` — added name_ru, gif_url fields
- `../backend/app/exercises/schemas.py` — added name_ru, gif_url to ExerciseRead
- `../backend/app/exercises/routes.py` — _exercise_to_read() passes new fields through
- `../backend/app/seed.py` — full rewrite: upsert strategy + ~150 exercises with Russian translations
- `../backend/app/main.py` — import renamed seed_exercises, updated log message
