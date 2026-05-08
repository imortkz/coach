# M003: Localization, Expanded Exercise Library & Exercise GIFs — Research

**Date:** 2026-03-14

---

## Summary

M003 has three interlocking changes that share the Exercise document: new fields (`name_ru`, `gif_url`), expanded seed data (~120–180 exercises), and a frontend language toggle backed by the existing Settings key-value store. The backend changes are low-risk — adding nullable fields to Beanie documents is backward-compatible and the Settings endpoint (`PUT/GET /api/settings/{key}`) already exists and handles `language` without modification. The 59 existing tests will continue to pass as long as `ExerciseRead` schema additions are nullable and existing test fixtures don't assert on exact field sets.

The highest-complexity piece is **frontend i18n**. No vue-i18n is installed today. Static UI strings (nav labels, button text, state messages) need translation keys; exercise names and muscle group labels are data-driven and must be handled separately — exercise names come from the API (`name` vs `name_ru`) while muscle group labels are a small finite set that map cleanly to a static locale file. The key architectural decision is: a single `useDisplayName(exercise)` composable that reads the active language from a Pinia store and returns the right name, used consistently across all four touch-points (`ExercisesView`, `ExerciseCard`, `ExerciseHistoryView`, `WorkoutCard`).

**Primary recommendation:** Sequence as three slices — (1) backend model + seed upsert strategy, (2) i18n infrastructure + settings store + language toggle UI, (3) exercise name/GIF display wiring. Prove slice 1 first with a passing test for `name_ru`/`gif_url` fields in the API response, then layer i18n on top. The seed expansion is the most time-consuming authoring task but has zero code risk; do it in slice 1 alongside the model changes.

---

## Recommendation

**Use vue-i18n v9 (latest 9.x) for static strings; a `useDisplayName` composable for data-driven exercise names; upsert-by-name strategy for seed idempotency.**

- Don't use a custom reactive locale object — vue-i18n's `useI18n()` composable integrates with Vue reactivity cleanly and handles edge cases (pluralization, fallback locale) out of the box.
- Muscle group labels are NOT from the API — they're English strings stored in MongoDB. Translate them in a static lookup map in the locale file, keyed on the English value (e.g. `muscle_groups.Chest = "Грудь"`). This avoids any backend changes for muscle group translation.
- Language preference flows: `GET /api/settings/language` on app startup → stored in a `useLanguageStore` (or `useSettingsStore`) Pinia store → `useI18n().locale` set reactively → all `$t()` calls and `useDisplayName()` calls update automatically.
- The seed upsert must use `update_one({ name, user_id: None }, $set {...}, upsert=True)` via Beanie's Motor client, NOT a bulk replace — this preserves existing `_id` values in case any workout documents have denormalized exercise names from seed exercises.

---

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Vue 3 i18n with locale switching | `vue-i18n@9.x` (`useI18n()`, `$t()`) | Reactively updates all `$t()` calls on locale change; handles fallback; used by >2M Vue 3 projects |
| Language persistence to backend | Existing `PUT /api/settings/{key}` + `GET /api/settings/{key}` | Already handles upsert, user scoping, and test coverage; `language` key fits directly with no code changes |
| MongoDB upsert-by-name | `Collection.update_one(filter, $set, upsert=True)` via Beanie's underlying Motor client | Avoids delete-all-and-reinsert; preserves existing document IDs; safe for partial field additions |

---

## Existing Code and Patterns

- `../backend/app/exercises/models.py` — `Exercise` Beanie document; add `name_ru: str | None = None` and `gif_url: str | None = None` directly; Beanie treats unknown fields as optional automatically
- `../backend/app/exercises/schemas.py` — `ExerciseRead` Pydantic schema; add `name_ru: str | None = None` and `gif_url: str | None = None`; existing tests only assert on specific fields, not exhaustive shape, so addition is safe
- `../backend/app/exercises/routes.py` — `_exercise_to_read()` helper converts `Exercise → ExerciseRead`; must pass `name_ru` and `gif_url` through; single change point
- `../backend/app/seed.py` — `seed_exercises_if_empty()` uses `count == 0` guard; **must change** to upsert-by-English-name strategy to support field additions and new exercises without manual collection clear; `user_id=None` filter on existing check is correct (doesn't touch custom exercises)
- `../backend/app/workouts/routes.py` — `PUT/GET /api/settings/{key}` fully implemented; `language` key works with zero backend changes
- `../frontend/src/types/index.ts` — `Exercise` interface; add `name_ru?: string | null` and `gif_url?: string | null`; all existing code uses `exercise.name` so new optional fields are backward-compatible
- `../frontend/src/stores/exercises.ts` — fetches and caches exercises; no changes needed except type flows through automatically after `types/index.ts` update
- `../frontend/src/main.ts` — app bootstrap; register `createI18n` plugin here; language is loaded async post-auth, so set initial locale to `'en'` and update reactively when settings load
- `../frontend/src/App.vue` — bottom nav has exactly 4 items (`Exercises`, `Programs`, `Workout`, `History`); **no Settings tab exists**; need to add a 5th tab or place language toggle in a different location
- `../frontend/src/stores/auth.ts` — `fetchMe()` called from router guard after auth; language loading should happen here or in a post-auth hook to ensure it's available before first view renders
- `../frontend/src/views/ExercisesView.vue` — renders `group.name` (English muscle group string) as section headers and `exercise.name` in list items; both need localization
- `../frontend/src/components/workout/ExerciseCard.vue:176` — `{{ exercise.name }}` (line 176) and `{{ exercise.muscle_group }}` (line 177); both need the display-name composable
- `../frontend/src/views/ExerciseHistoryView.vue:71` — `{{ exercise?.name ?? 'Exercise' }}`; needs display-name composable
- `../frontend/src/components/history/WorkoutCard.vue:65` — `s.exercise?.name || 'Exercise #...'`; needs update for Russian names
- `../frontend/src/router/index.ts` — no `/settings` route exists; need to add one if a dedicated Settings view is created

---

## Constraints

- **Seed upsert must not touch custom exercises** — filter on `user_id: None` before upserting; D016 decision: `user_id=None` means shared/seeded
- **59 existing backend tests must pass** — `test_exercises.py` fixtures create exercises without `name_ru`/`gif_url`; since new fields have defaults of `None`, no fixture changes needed
- **vue-i18n v9 only** (constraint from context) — v10 targets Vue 3.5+ and changes the composition API shape; v9.14.x is the stable target
- **Wikimedia Commons URLs must end in `.gif`** and be direct media file URLs (e.g. `https://upload.wikimedia.org/wikipedia/commons/...gif`), not redirect or page URLs
- **`gif_url` must be nullable** — many exercises won't have a usable GIF; frontend must render gracefully with no image element or a placeholder
- **No new backend routes needed** — settings endpoint already handles `language`; exercise model changes are additive only
- **Vite + Tailwind v4** — no special i18n build config needed; vue-i18n v9 is an ES module and Vite handles it natively
- **`id` type mismatch** — `types/index.ts` declares `Exercise.id: number` but backend returns UUID strings; `ExerciseHistoryView.vue` casts with `Number(route.params.id)` which will produce `NaN` for UUIDs — **this is an existing bug**, not introduced by M003, but the `exercisesStore.exercises.find((e) => e.id === exerciseId)` lookup is broken for seeded exercises. Should be fixed in M003 as part of the type touch.

---

## Common Pitfalls

- **`count == 0` seed guard** — The current `seed_exercises_if_empty()` returns early if any seeded exercise exists. After M003, you need to upsert all seed exercises so existing DBs get `name_ru`/`gif_url` populated. Use `bulk_write` with `UpdateOne(filter={'name': name, 'user_id': None}, update={'$set': {...}}, upsert=True)` via the underlying Motor collection.
- **vue-i18n locale reactivity** — Setting `i18n.global.locale` as a `ref` and changing it works, but only if the instance is created with `legacy: false` (Composition API mode). Legacy mode uses `i18n.global.locale = 'ru'` (string assign); Composition API mode uses `.value`. Mixing the two silently fails to update.
- **Muscle group translation via locale file vs. API** — Muscle groups are English strings in MongoDB. Translating them in a static `muscle_groups` namespace in the locale file (`t('muscle_groups.' + group.name)`) with a fallback to the raw string keeps this frontend-only and doesn't require backend changes.
- **Language loading race** — If `GET /api/settings/language` is called before auth is complete, it returns 401 and silently falls back to English. The load must happen after `devLogin()`/`telegramLogin()` resolves. Hook into the router guard's post-auth step (after `auth.fetchMe()`).
- **`gif_url` broken images** — Use `<img v-if="exercise.gif_url" :src="exercise.gif_url" @error="onGifError">` pattern with an `onerror` handler that hides the element if the Wikimedia URL is unreachable. Don't show a broken image placeholder.
- **Seed data authoring** — Russian gym terminology for compound movements is largely standardized (жим лёжа, приседания, становая тяга) but isolation exercises vary. "Face Pull" has no consensus Russian name — "Тяга к лицу" is acceptable. Document judgment calls in seed file comments.
- **Tailwind v4 + vue-i18n** — No conflict, but if using `@apply` directives in scoped styles, Tailwind v4's CSS-first config doesn't need `tailwind.config.js`; vue-i18n is JS-side only.
- **`id: number` in `Exercise` TypeScript type** — Must fix to `id: string` as part of this milestone's type touches. Check `ExerciseHistoryView.vue`'s `Number(route.params.id)` cast — it must change to string comparison.

---

## Open Risks

- **Wikimedia GIF availability** — A manual audit of ~150 exercises is needed to find valid `.gif` URLs. Expect ~50–70% coverage. The remaining exercises get `gif_url: null`. Time risk: authoring the seed file is the slowest task in this milestone.
- **No Settings view exists** — Adding a language toggle requires either a dedicated `/settings` route (new view + nav tab) or embedding the toggle in an existing view. The bottom nav already has 4 tabs; a 5th makes it crowded on mobile. Consider adding Settings as a gear icon in the desktop navbar only, or as a footer link in the mobile nav.
- **Seed volume** — Going from 50 → ~150 exercises is a large authoring task. Research shows standard strength training exercise taxonomies (ExRx.net, Strength Level) cover 20–30 exercises per major group reliably. The upsert approach means this can be done incrementally if time is tight.
- **Test isolation for new seed fields** — If any test asserts `assert "name_ru" not in data[0]` (unlikely but possible), it would fail. Scan test files before submitting — the current test suite does not make this assertion.

---

## Candidate Requirements (advisory — not auto-binding)

| Candidate | Priority | Rationale |
|-----------|----------|-----------|
| **LOC-01** — `Exercise.name_ru` and `gif_url` returned in API responses | Table stakes | Core M003 contract |
| **LOC-02** — `PUT/GET /api/settings/language` persists `"en"` or `"ru"` | Table stakes | Durable preference |
| **LOC-03** — Language toggle in UI restores on refresh | Table stakes | Stated acceptance criterion |
| **LOC-04** — Exercise names in workout logging view use `name_ru` when language is Russian | Table stakes | Core user value |
| **LOC-05** — Muscle group filter labels translated | Table stakes | Stated acceptance criterion |
| **LOC-06** — Exercise GIF displayed inline with graceful null handling | Table stakes | Core M003 contract |
| **LOC-07** — Seed upsert strategy (no manual DB clear required) | Table stakes | Operational safety |
| **FIX-01** — `Exercise.id: string` type fix in TypeScript | Strongly advisory | Existing bug exposed by M003 type touches; low effort to fix while touching the file |

---

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| vue-i18n | (checked via `npx skills find`) | Not checked — standard library, docs sufficient |

---

## Sources

- Beanie ODM docs: bulk write / upsert pattern via Motor (internal knowledge; Beanie exposes `get_motor_collection()` for bulk ops)
- vue-i18n v9 Composition API setup: `createI18n({ legacy: false, locale: 'en', messages: { en, ru } })` — standard v9 pattern
- Wikimedia Commons direct media URLs: `https://upload.wikimedia.org/wikipedia/commons/[path].gif` — verified pattern from Commons file pages
- Existing codebase: `../backend/app/workouts/routes.py` — `PUT/GET /api/settings/{key}` pattern confirmed
- Existing codebase: `../backend/app/seed.py` — `count == 0` guard confirmed; upsert strategy needed
- Existing codebase: `../frontend/src/types/index.ts` — `id: number` bug confirmed (MongoDB uses UUID strings)
