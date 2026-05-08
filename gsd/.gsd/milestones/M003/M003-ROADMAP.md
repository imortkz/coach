# M003: Localization, Expanded Exercise Library & Exercise GIFs

**Vision:** Users can switch between English and Russian UI, browse an expanded exercise library (~20–30 per muscle group), and see demonstration GIFs for exercises.

## Success Criteria

- User sets language to Russian → exercise names and muscle group labels render in Russian throughout all views
- User refreshes the app → language preference is restored from backend settings
- Exercise list shows ~20–30 entries per muscle group (up from ~8)
- Tapping an exercise with a GIF URL shows the Wikimedia Commons GIF inline; exercises without GIF show no broken image
- User sets language to English → all labels revert to English
- `uv run pytest tests/ -q` in `../backend/` passes (≥59 tests)

## Key Risks / Unknowns

- Seed upsert strategy change — moving from `count == 0` guard to upsert-by-name changes the idempotency contract; must not clobber custom exercises or break existing IDs
- vue-i18n reactivity — `legacy: false` mode with reactive locale switching must be wired correctly or locale changes silently fail
- No Settings UI surface exists — the 4-tab nav has no place for a language toggle; need a clean UI solution for mobile

## Proof Strategy

- Seed upsert safety → retire in S01 by proving existing tests pass after model + seed changes, and by verifying upsert doesn't touch custom exercises
- vue-i18n reactivity → retire in S02 by proving language toggle switches static UI strings reactively in the browser
- Settings UI → retire in S02 by shipping a working Settings view with language toggle accessible from nav

## Verification Classes

- Contract verification: `uv run pytest tests/ -q` (backend, ≥59 tests); `npm run build` (frontend, no errors)
- Integration verification: browser walkthrough — language toggle → exercise names switch → GIF displays → refresh preserves language
- Operational verification: none
- UAT / human verification: visual check of Russian translations and GIF rendering quality

## Milestone Definition of Done

This milestone is complete only when all are true:

- All three slices are complete and verified
- `GET /api/exercises` returns `name_ru` and `gif_url` for seeded exercises
- `PUT /api/settings/language` persists preference; `GET /api/settings/language` returns it
- vue-i18n is registered and all static UI strings have English and Russian translations
- Language toggle in Settings view persists to backend and updates all views reactively
- Exercise names use `name_ru` when language is Russian in ExercisesView, ExerciseCard, ExerciseHistoryView, and WorkoutCard
- Exercise GIF displays inline with graceful null handling (no broken images)
- ~120–180 exercises seeded across 6 muscle groups
- `Exercise.id` TypeScript type fixed from `number` to `string`
- Backend tests pass (≥59); frontend builds clean

## Requirement Coverage

- Covers: LOC-01, LOC-02, LOC-03, LOC-04, LOC-05, LOC-06, LOC-07, FIX-01 (all candidate requirements from research)
- Partially covers: none
- Leaves for later: none
- Orphan risks: none — no Active requirements in REQUIREMENTS.md map to this milestone (all are new capabilities)

## Slices

- [x] **S01: Backend model + expanded seed with upsert** `risk:high` `depends:[]`
  > After this: `GET /api/exercises` returns `name_ru` and `gif_url` fields; ~150 exercises seeded via upsert-by-name strategy; all 59+ backend tests pass
- [x] **S02: vue-i18n infrastructure + Settings view with language toggle** `risk:medium` `depends:[S01]`
  > After this: user can navigate to Settings, toggle language between English and Russian, see all static UI strings (nav labels, button text, muscle group names) switch language reactively, and preference persists across refresh
- [x] **S03: Exercise name localization + GIF display + type fix** `risk:low` `depends:[S01,S02]`
  > After this: exercise names display in Russian when language is set to Russian across all four views (ExercisesView, ExerciseCard, ExerciseHistoryView, WorkoutCard); exercise detail shows GIF when available; `Exercise.id` TypeScript type is `string`

## Boundary Map

### S01 → S02

Produces:
- `Exercise` Beanie document with `name_ru: str | None` and `gif_url: str | None` fields
- `ExerciseRead` Pydantic schema with `name_ru` and `gif_url` in API response
- `_exercise_to_read()` passes new fields through
- Upsert-based `seed_exercises()` function (replaces `seed_exercises_if_empty()`)
- ~150 seed exercises with Russian names and Wikimedia GIF URLs where available

Consumes:
- nothing (first slice)

### S02 → S03

Produces:
- vue-i18n v9 plugin registered in `main.ts` with `legacy: false`
- English and Russian locale files with all static UI strings including `muscle_groups.*` namespace
- `useSettingsStore` Pinia store with reactive `language` state synced to backend
- Settings view with language toggle accessible from navigation
- `Exercise` TypeScript type with `name_ru?: string | null` and `gif_url?: string | null`

Consumes:
- `GET /api/exercises` returns `name_ru` and `gif_url` (from S01)
- `PUT/GET /api/settings/language` works (existing endpoint, no S01 dependency)

### S03 consumes from S01 + S02

Consumes:
- `name_ru` and `gif_url` in API response (S01)
- vue-i18n locale, `useSettingsStore.language`, `t()` function (S02)
- `Exercise` TypeScript type with new optional fields (S02)
