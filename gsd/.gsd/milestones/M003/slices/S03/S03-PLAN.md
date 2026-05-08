# S03: Exercise name localization + GIF display + type fix

**Goal:** Exercise names display in the user's chosen language across all four views; exercise detail shows GIF when available; WorkoutCard type bugs fixed.
**Demo:** Set language to Russian in Settings → navigate to Exercises → names and muscle groups show in Russian → tap an exercise → ExerciseHistoryView shows Russian name and GIF (for Bench Press) → go to History → WorkoutCard shows Russian exercise names → switch back to English → everything reverts.

## Must-Haves

- `useDisplayName(exercise)` composable returns reactive display name based on `useSettingsStore().language`
- ExercisesView, ExerciseCard, ExerciseHistoryView, WorkoutCard all use the composable for exercise names
- Muscle group labels use `t('muscle_groups.' + group)` in ExercisesView and ExerciseCard
- ExerciseHistoryView shows `<img>` for `gif_url` with `v-if` guard and `@error` fallback
- At least one seed exercise (Bench Press) has a real `gif_url` in `seed.py`
- WorkoutCard `ExerciseGroup.exerciseId` type fixed to `string`; Map typed as `Map<string, ExerciseGroup>`
- ExerciseCard emit types fixed from `number` to `string` where they use `exercise.id`
- `npm run build` produces zero errors

## Verification

- `cd ../frontend && npm run build` — zero errors
- `cd ../backend && uv run pytest tests/ -q` — all tests pass (≥59)
- Browser walkthrough: language toggle → exercise names switch in all four views → GIF displays on Bench Press detail → refresh preserves language

## Observability / Diagnostics

**Runtime signals:**
- Language switch: Vue reactivity via `useSettingsStore().language` ref — watchers in composable fire immediately on store change; no page reload needed
- GIF load failure: `@error` handler on `<img>` sets `display:none`; inspect element to confirm hidden state
- Missing translation key: vue-i18n emits a console warning `[intlify] Not found 'muscle_groups.X'` for unknown muscle group keys

**Inspection surfaces:**
- Vue DevTools → Pinia → settings store → `language` field shows current locale
- Vue DevTools → Components → ExercisesView → inspect `groupedExercises` computed for display name values
- `npm run build` TypeScript errors surface all emit type mismatches and Map<number> → Map<string> drift

**Failure visibility:**
- If `useDisplayName` isn't reactive: toggling language in Settings won't update already-rendered exercise names; Vue DevTools will show stale computed values
- If emit types remain `number`: TypeScript build error `Argument of type 'string' is not assignable to parameter of type 'number'`
- If GIF img has no null guard: runtime error in ExerciseHistoryView for exercises with `gif_url: null`

**Redaction:** No secrets in this slice. GIF URLs are public Wikimedia Commons links.

## Integration Closure

- Upstream surfaces consumed: `useSettingsStore().language` (S02), `t()` with muscle_groups keys (S02), `name_ru`/`gif_url` in Exercise type (S02) and API (S01)
- New wiring introduced in this slice: `useDisplayName` composable, GIF `<img>` in ExerciseHistoryView, exercises store cross-reference in WorkoutCard
- What remains before the milestone is truly usable end-to-end: nothing — this is the final slice

## Tasks

- [x] **T01: Wire exercise name localization, GIF display, and type fixes across all views** `est:40m`
  - Why: This is the entire slice — composable creation, four-view wiring, GIF display, type fixes, and one seed URL are all tightly coupled and small enough for one task
  - Files: `../frontend/src/composables/useDisplayName.ts`, `../frontend/src/views/ExercisesView.vue`, `../frontend/src/components/workout/ExerciseCard.vue`, `../frontend/src/views/ExerciseHistoryView.vue`, `../frontend/src/components/history/WorkoutCard.vue`, `../backend/app/seed.py`
  - Do: (1) Create `useDisplayName` composable returning `computed` that reads `settingsStore.language`. (2) Wire it in all four views for exercise name display. (3) Wire `t('muscle_groups.' + group)` in ExercisesView and ExerciseCard. (4) Add GIF `<img>` block with `v-if` and `@error` handler in ExerciseHistoryView. (5) Fix WorkoutCard local types (`exerciseId: string`, `Map<string, ...>`), import exercises store for name_ru cross-reference. (6) Fix ExerciseCard emit types to `string`. (7) Add real gif_url for Bench Press in seed.py.
  - Verify: `npm run build` zero errors; `uv run pytest tests/ -q` passes; browser shows Russian names when language is Russian and GIF on Bench Press detail
  - Done when: all four views display localized exercise names; GIF renders for Bench Press; build clean; backend tests pass

## Files Likely Touched

- `../frontend/src/composables/useDisplayName.ts`
- `../frontend/src/views/ExercisesView.vue`
- `../frontend/src/components/workout/ExerciseCard.vue`
- `../frontend/src/views/ExerciseHistoryView.vue`
- `../frontend/src/components/history/WorkoutCard.vue`
- `../backend/app/seed.py`
