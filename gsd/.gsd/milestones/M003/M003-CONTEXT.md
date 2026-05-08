# M003: Localization, Expanded Exercise Library & Exercise GIFs — Context

**Gathered:** 2026-03-14
**Status:** Queued — pending auto-mode execution.

## Project Description

GymCoach is a personal gym training companion. Users build programs from a shared exercise library, log workouts, and track progression. The current exercise library is English-only with 50 exercises and no visual guidance.

## Why This Milestone

Three related gaps compound each other:

1. **Language** — The entire UI is English-only. The user wants Russian language support throughout — labels, navigation, exercise names, and muscle group names.
2. **Exercise library size** — 50 exercises across 6 muscle groups (~8 per group) is sparse. Important exercises are missing. The user wants 20–30 exercises per group (~120–180 total).
3. **Exercise visual guidance** — No way to see how to perform an exercise. Free CC-licensed GIFs exist on Wikimedia Commons for most standard gym movements.

These belong in one milestone because they share the Exercise model (adding `name_ru` and `gif_url` fields to the same seed data) and the same slice cadence.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Switch between English and Russian UI from a language toggle in the app (persists across sessions via user settings)
- See Russian names for all exercises and muscle group labels throughout the app
- Browse a significantly expanded exercise library (~20–30 exercises per muscle group)
- Tap an exercise to see a demonstration GIF sourced from Wikimedia Commons (where available)

### Entry point / environment

- Entry point: http://localhost:5173 — Settings/profile area for language toggle; exercise list and workout views for translated names and GIFs
- Environment: browser (mobile-first)
- Live dependencies involved: MongoDB (Exercise documents, Setting document for `language` key), Wikimedia Commons URLs (static, no API calls at runtime)

## Completion Class

- Contract complete means: `GET /api/exercises` returns `name_ru` and `gif_url` for seeded exercises; `PUT /api/settings/language` persists the preference; 59 existing tests still pass
- Integration complete means: switching language in the UI toggles exercise names and muscle group labels throughout all views; GIF appears in exercise detail; new seed exercises visible in the library
- Operational complete means: none

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- User sets language to Russian → exercise names in workout logging view render in Russian; muscle group filter shows Russian labels
- User refreshes the app → language preference is restored (read from settings on startup)
- Exercise list shows ~20–30 entries per muscle group
- Tapping an exercise with a GIF URL shows the Wikimedia Commons GIF inline
- User sets language to English → all labels revert to English
- No regression: `uv run pytest tests/ -q` in `../backend/` still passes (≥59 tests)

## Risks and Unknowns

- **Wikimedia GIF availability** — Not every exercise has a suitable CC-licensed GIF on Wikimedia. Exercises without a GIF must gracefully degrade (no broken image). The `gif_url` field should be nullable.
- **Seed migration** — The existing 50 seed exercises in `seed.py` have no `name_ru` or `gif_url`. The seed is only inserted if the collection is empty (`count == 0`). Re-seeding requires clearing existing exercises (or a one-off migration). In dev this is straightforward; the plan must account for it.
- **Russian exercise naming standard** — Russian gym terminology varies; some exercises have no consensus translation (e.g. "Face Pull"). The plan should prefer standard sports literature terms and note any judgment calls in the seed file comments.
- **vue-i18n scope** — UI strings (navigation, button labels, field labels) need translation keys. Exercise names and muscle groups are data-driven (from the API), not static strings — the translation strategy must cleanly separate these two concerns.
- **Expanded seed idempotency** — If the seed count check uses `count == 0`, adding exercises requires either resetting the collection or a separate "upsert by name" strategy. This needs a deliberate decision in planning.

## Existing Codebase / Prior Art

- `../backend/app/seed.py` — 50 SEED_EXERCISES dicts; `seed_exercises_if_empty()` checks count > 0 to skip; adding `name_ru` and `gif_url` fields means updating all 50 entries plus new ones
- `../backend/app/exercises/models.py` — `Exercise` Beanie Document; `name`, `muscle_group`, `equipment`, `is_custom`, `user_id`; needs `name_ru: str | None` and `gif_url: str | None` fields
- `../backend/app/workouts/routes.py` — `PUT /api/settings/{key}` and `GET /api/settings/{key}` — existing key-value pattern for user preferences; `language` key fits directly
- `../frontend/src/stores/exercises.ts` — fetches exercises, exposes them to views; `Exercise` type needs `name_ru` and `gif_url`
- `../frontend/src/types/index.ts` — `Exercise` interface; needs `name_ru?: string | null` and `gif_url?: string | null`
- `../frontend/src/views/ExercisesView.vue` — grouped exercise list; all group names and exercise names rendered here
- `../frontend/src/components/workout/ExerciseCard.vue` — exercise name displayed during active workout
- `../frontend/src/stores/auth.ts` — user session management; language preference should be loaded after login
- `../frontend/src/main.ts` — app bootstrap; vue-i18n plugin registered here

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

No existing requirements map directly — this is new scope. New capabilities introduced:

- Multi-language UI with user-level preference persistence
- Expanded exercise content library
- Exercise visual guidance via GIF links

## Scope

### In Scope

- Add `name_ru: str | None` and `gif_url: str | None` to `Exercise` Beanie Document model and API responses
- Expand seed data to ~20–30 exercises per muscle group (Chest, Back, Shoulders, Arms, Legs, Core) with standard Russian names and Wikimedia GIF URLs where available
- `PUT /api/settings/language` to persist `"en"` or `"ru"` per user (uses existing settings infrastructure)
- `GET /api/settings/language` on app startup to restore preference
- Frontend: install and configure vue-i18n; English and Russian locale files for all static UI strings
- Frontend: language toggle in settings/profile area; persists to backend
- Frontend: exercise display uses `name_ru` when language is Russian, falling back to `name` if not available
- Frontend: muscle group labels translated via vue-i18n locale file (static mapping, not from API)
- Frontend: exercise GIF display on exercise detail/tap interaction (graceful no-op if `gif_url` is null)
- Seed idempotency strategy: upsert by English name so adding new exercises and fields is non-destructive

### Out of Scope / Non-Goals

- Translating user-created (custom) exercises — `name_ru` is only populated for seeded exercises
- Languages beyond English and Russian
- Downloading or self-hosting GIF files — Wikimedia URLs only
- Video support — GIF only
- Translation of program names, workout notes, or user-entered text
- RTL layout support (Russian is LTR, not needed)
- CI/CD or automated translation workflows

## Technical Constraints

- Frontend only target for language toggle: `../frontend/src/`; backend additions limited to Exercise model + seed + settings route (already exists)
- vue-i18n v9 (compatible with Vue 3 Composition API)
- Language preference stored as `Setting` document with key `"language"` and value `"en"` or `"ru"` — same pattern as progression increment overrides
- GIF URLs must be direct Wikimedia Commons media links (ending in `.gif`) — no JavaScript-rendered pages
- Seed upsert strategy must not clobber user-created exercises (`user_id != None`)
- All 59 existing backend tests must continue to pass after Exercise model changes

## Integration Points

- `Exercise` Beanie Document → API response → `Exercise` TypeScript type → all views that render exercise names — adding optional fields is backward-compatible if nullable
- `PUT/GET /api/settings/language` — existing settings endpoint; no new backend route needed
- vue-i18n locale files → all Vue components rendering static labels — must cover navigation, button labels, workout states, history labels
- Wikimedia Commons — static URL per exercise in seed data; no runtime API dependency

## Open Questions

- None — design questions resolved during discussion.
