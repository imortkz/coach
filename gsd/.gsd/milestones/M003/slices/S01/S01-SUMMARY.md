---
id: S01
parent: M003
milestone: M003
provides:
  - Exercise Beanie document with name_ru and gif_url optional fields
  - ExerciseRead Pydantic schema exposes name_ru and gif_url in API responses
  - _exercise_to_read() passes new fields through
  - Upsert-based seed_exercises() via pymongo bulk_write UpdateOne keyed on {name, user_id=None}
  - ~150 seed exercises across 6 muscle groups with Russian translations (gif_url=None for all)
  - app/main.py wired to call seed_exercises() at startup
requires: []
affects:
  - S02
  - S03
key_files:
  - ../backend/app/exercises/models.py
  - ../backend/app/exercises/schemas.py
  - ../backend/app/exercises/routes.py
  - ../backend/app/seed.py
  - ../backend/app/main.py
key_decisions:
  - D023: Upsert-by-name uses {name, user_id: None} filter to avoid clobbering custom user exercises
  - D024: $setOnInsert generates _id via uuid4 on first insert; re-runs don't change _id
  - D025: gif_url=None for all entries in initial seed — real GIF URLs deferred to S03
patterns_established:
  - Seed upsert pattern: bulk_write UpdateOne with upsert=True, filter on {name, user_id: None}, $set all fields, $setOnInsert for _id
observability_surfaces:
  - Startup log: "Upserted {n} seed exercises into exercises collection"
  - GET /api/exercises — each item now includes name_ru and gif_url fields
drill_down_paths:
  - .gsd/milestones/M003/slices/S01/tasks/T01-SUMMARY.md
duration: ~1h
verification_result: passed
completed_at: 2026-03-14
---

# S01: Backend model + expanded seed with upsert

**`name_ru` and `gif_url` added to Exercise model + API; ~150 exercises seeded via upsert-by-name; 64 backend tests pass.**

## What Happened

Single task. Added `name_ru: str | None` and `gif_url: str | None` to `Exercise` (Beanie document) and `ExerciseRead` (Pydantic schema). Wired both through `_exercise_to_read()`. Replaced the count-gated `seed_exercises_if_empty()` with a pymongo bulk_write upsert strategy keyed on `{name, user_id: None}` — idempotent re-runs update fields in place without changing `_id` or touching custom exercises. Expanded seed from 50 to ~150 exercises across 6 muscle groups, each with a Russian translation. All `gif_url` entries are `None` — real URLs are S03 work.

## Verification

`uv run pytest tests/ -q` → 64 passed.

## Requirements Advanced

- LOC-01 — name_ru field now in model and API response
- LOC-05 — expanded exercise library (~25 per muscle group)

## Deviations

None — executed as planned.

## Known Limitations

- gif_url is None for all seed entries. Wikimedia Commons URLs to be added in S03.

## Follow-ups

- S02 consumes: GET /api/exercises now returns name_ru (use it for locale-aware display)
- S03 populates: gif_url fields in seed data

## Files Created/Modified

- `../backend/app/exercises/models.py` — added name_ru, gif_url fields
- `../backend/app/exercises/schemas.py` — added name_ru, gif_url to ExerciseRead
- `../backend/app/exercises/routes.py` — _exercise_to_read() passes new fields through
- `../backend/app/seed.py` — full rewrite: upsert strategy + ~150 exercises with Russian translations
- `../backend/app/main.py` — imports seed_exercises (renamed from seed_exercises_if_empty)

## Forward Intelligence

### What the next slice should know
- The Exercise TypeScript type in frontend still lacks name_ru and gif_url — S02 must add them to the type before S03 can use them
- PUT/GET /api/settings/language already exists from M001/S08 — S02 just needs to wire it to vue-i18n

### What's fragile
- gif_url=None everywhere — S03 must populate this before GIF display is meaningful

### Authoritative diagnostics
- `uv run pytest tests/ -q` — source of truth for backend health
- `GET /api/exercises` response — verify name_ru and gif_url are present

### What assumptions changed
- Original plan assumed gif_url would have some real values in S01 — all deferred to S03 for quality
