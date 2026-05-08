# S03: Exercise name localization + GIF display + type fix — Research

**Date:** 2026-03-14

## Summary

S03 is a pure frontend wiring slice. All infrastructure exists: vue-i18n is registered, locale keys are ready (`muscle_groups.*` namespace in `en.ts`/`ru.ts`), `useSettingsStore().language` is a reactive ref, `Exercise.id` is already `string`, and `name_ru`/`gif_url` are already in the `Exercise` TypeScript type. The slice has four touchpoints to wire and one GIF display to add.

The central implementation decision is whether to use a `useDisplayName(exercise)` composable or inline `language === 'ru' ? exercise.name_ru || exercise.name : exercise.name` at each site. The composable approach (recommended in M003-RESEARCH.md) is the right call: it centralizes the fallback logic (`name_ru || name`), stays reactive to `language` changes without explicit watching, and is DRY across four files.

**WorkoutCard has a compounding issue**: the component's local `ExerciseGroup` interface uses `exerciseId: number` and the RouterLink to exercise history uses that number, but backend `exercise_id` is a UUID string. Additionally, `WorkoutCard` only has access to the denormalized `exercise_name` (English), not `name_ru`, because `_set_to_read()` in the backend constructs `ExerciseRead` without name_ru (it's not stored in the `WorkoutSet` embedded document). The cleanest fix: import `useExercisesStore()` in WorkoutCard, cross-reference by `exercise_id` to get the full `Exercise` (with `name_ru`), fix the local `exerciseId: string` type, and fix the RouterLink. This avoids any backend changes.

The one real GIF URL in the seed data (Bench Press) validates the display path. ExerciseHistoryView is the correct display surface — it's the exercise "detail" view. The pattern is `<img v-if="exercise.gif_url" :src="exercise.gif_url" @error="handleGifError">` where the error handler hides the element.

**Broader type mismatch (do not over-fix):** `WorkoutSet`, `ProgramSet`, `ProgramExercise`, `Program`, and `Workout` interfaces in `types/index.ts` still have `id: number` and `exercise_id: number`, while the backend uses UUID strings. This is a pre-existing bug beyond M003 scope. S03 should fix only the fields it directly touches: `ExerciseGroup.exerciseId` in WorkoutCard (local type) and `WorkoutSet.exercise_id` usage in WorkoutCard's Map key. Full type audit is a separate concern.

## Recommendation

**Create `src/composables/useDisplayName.ts`, wire it at all four touchpoints, add GIF display to ExerciseHistoryView, fix WorkoutCard's local exerciseId type and name lookup.**

1. `useDisplayName(exercise: Exercise): ComputedRef<string>` — reads `useSettingsStore().language`, returns `exercise.name_ru || exercise.name` when `ru`, `exercise.name` otherwise. Returns a `ComputedRef<string>` so it's reactive.
2. Wire in `ExercisesView.vue`: exercise list item name (`exercise.name` → `displayName(exercise)`) + muscle group headers (`group.name` → `t('muscle_groups.' + group.name)`).
3. Wire in `ExerciseCard.vue`: `exercise.name` → composable; `exercise.muscle_group` → `t('muscle_groups.' + exercise.muscle_group)` (import `useI18n` since not already imported).
4. Wire in `ExerciseHistoryView.vue`: `exercise?.name ?? 'Exercise'` → `displayName(exercise) ?? t('exercises.exercise_fallback')`; also add GIF display block.
5. Wire in `WorkoutCard.vue`: import `useExercisesStore`, look up exercise by `exercise_id` from store, use composable for name. Fix `ExerciseGroup.exerciseId` to `string`. Fix RouterLink path.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Reactive language-aware display name | `useSettingsStore().language` + computed ref | Already reactive; no watcher needed; composable wraps it cleanly |
| Muscle group translation | `t('muscle_groups.' + group.name)` with keys in en.ts/ru.ts | Keys are already authored in S02; zero new locale work |
| Exercise cross-reference in WorkoutCard | `useExercisesStore().exercises.find(e => e.id === id)` | Store already loaded and cached; no new API call |
| GIF broken image fallback | `@error` handler on `<img>` that sets `v-show="false"` | One-liner; no need for a wrapper component |

## Existing Code and Patterns

- `../frontend/src/composables/useApi.ts`, `useRestTimer.ts`, `useSwipeLeft.ts` — composable pattern in this codebase: `defineComposable` / `export function use*()` with reactive state; follow the same pattern for `useDisplayName`
- `../frontend/src/stores/settings.ts` — `useSettingsStore().language` is a `ref<string>('en')`; import directly in composable with `const { language } = useSettingsStore()`; use in `computed()` to stay reactive
- `../frontend/src/views/ExercisesView.vue:353` — `{{ exercise.name }}` (in RouterLink); this is the primary name display site; has `useI18n()` already imported at top
- `../frontend/src/components/workout/ExerciseCard.vue:176` — `{{ exercise.name }}` in `<h3>`; no `useI18n` currently imported; must add both `useI18n` and store import
- `../frontend/src/views/ExerciseHistoryView.vue:35` — `exercise?.name ?? 'Exercise'` in the `<h1>`; also `exercise.muscle_group` in subtitle; has `useI18n` already imported
- `../frontend/src/components/history/WorkoutCard.vue:55-65` — local `ExerciseGroup` interface with `exerciseId: number` and `exerciseName: string`; computed `exerciseGroups` builds map from `workout.sets`; `exerciseName` comes from `s.exercise?.name || 'Exercise #...'` — no store access currently
- `../frontend/src/plugins/i18n.ts` — export: `export default i18n`; import in composable as `import i18n from '@/plugins/i18n'` (or use `useSettingsStore` which already tracks the reactive language state — prefer store over direct i18n import in composables)
- `../backend/app/workouts/routes.py:41-46` — `_set_to_read()` constructs `ExerciseRead` without `name_ru` (backend WorkoutSet embedded doc doesn't store it); confirms name_ru is NOT available from workout API responses — frontend must cross-reference exercises store

## Constraints

- **ExerciseCard.vue has no `useI18n()` import** — must add `import { useI18n } from 'vue-i18n'` and destructure `t` in script setup
- **WorkoutCard.vue is a pure-computed component** — currently no store imports; adding `useExercisesStore()` is appropriate since exercises are pre-loaded by router guard
- **`name_ru` fallback is required** — `exercise.name_ru` can be `null` (custom exercises have no Russian name); the display composable must always fallback to `exercise.name`
- **Locale keys for muscle groups already exist** — `muscle_groups.Chest`, `.Back`, `.Shoulders`, `.Arms`, `.Legs`, `.Core` defined in both `en.ts` and `ru.ts`; no locale file edits needed
- **gif_url is null for 141/142 seed entries** — only Bench Press has a real URL; `v-if="exercise.gif_url"` guard is essential
- **Only ExerciseHistoryView shows exercise detail** — this is where the GIF belongs; ExercisesView exercise rows are list items and shouldn't embed GIFs inline
- **Do not fix non-S03 type mismatches** — `WorkoutSet.id`, `workout_id`, `ProgramSet.id`, etc. are `number` in frontend types but `string` in backend; fixing them is a larger refactor outside this slice's boundary
- **`npm run build` must produce zero errors after changes** — TypeScript strict mode is on; any type fixes in WorkoutCard's local interface must be consistent throughout that file

## Common Pitfalls

- **Composable called outside component** — `useSettingsStore()` inside `useDisplayName` is fine if called within a component's `setup()`; don't try to call the composable at module level or in a `script` (non-setup)
- **`computed` on a per-exercise basis** — `useDisplayName(exercise)` where `exercise` is a prop (not a ref) can return a plain computed: `computed(() => settingsStore.language === 'ru' ? exercise.name_ru || exercise.name : exercise.name)`. This works because `settingsStore.language` is reactive.
- **WorkoutCard Map key type** — the local `Map<number, ExerciseGroup>` must become `Map<string, ExerciseGroup>` when fixing `exerciseId` to `string`; the `.has()`, `.get()`, `.set()` calls all work with strings
- **RouterLink path in WorkoutCard** — currently `/exercises/${group.exerciseId}/history`; with `exerciseId: string` this is correct as-is (string interpolation works); no change needed to the template string itself, only the type
- **ExerciseCard emits use `number` for exercise_id** — the emit `addSet: [exerciseId: number]` etc. use `exercise.id` which is already `string` in the type; these emits may have a `number` type annotation that needs updating if TypeScript complains. Check all emits in ExerciseCard that pass `props.exercise.id`.
- **Muscle group header in ExercisesView** — `group.name` is the raw English string from the API (e.g. "Chest"); `t('muscle_groups.' + group.name)` is the correct call; if a muscle group name has a space or special char, the key lookup will fail silently (returns key); the 6 standard values are safe
- **vue-i18n v9 deprecation warning** — already present from S02; don't attempt to resolve during S03; it's cosmetic

## Open Risks

- **Exercises store may not be loaded when WorkoutCard renders** — the router guard calls `loadLanguage` after `fetchMe`, but exercises are lazy-loaded (only fetched on ExercisesView mount). If the user navigates directly to History without visiting Exercises, `exercisesStore.exercises` will be empty and cross-reference will return `undefined`. Mitigation: keep `exerciseName: s.exercise?.name || 'Exercise #${s.exercise_id}'` as fallback when store lookup returns undefined.
- **ExerciseCard emit types** — `ExerciseCard.vue` emits use `number` in some event payload types (`addSet: [exerciseId: number]`, `removeExercise: [exerciseId: number]`, etc.) even though `exercise.id` is now `string`. These may emit string values with incorrect type annotation; TypeScript may warn. Audit all emits in ExerciseCard.vue that use `props.exercise.id`.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| vue-i18n | none needed | Standard library; S02 already established all patterns |
| Vue 3 composables | none needed | Pattern established in existing codebase |

## Sources

- S02-SUMMARY.md — locale keys for muscle_groups already authored; Exercise TypeScript type updated; `useSettingsStore().language` reactive ref pattern established
- S01-SUMMARY.md — gif_url=None for all but 1 seed entry (Bench Press); name_ru populated for ~150 exercises
- `../frontend/src/components/history/WorkoutCard.vue` — local ExerciseGroup type; exerciseId: number bug; name from denormalized exercise only
- `../backend/app/workouts/routes.py:41-46` — `_set_to_read()` confirms name_ru not denormalized in workout set responses
- `../frontend/src/composables/` — composable file pattern in this project
- `../backend/app/exercises/schemas.py` — ExerciseRead has name_ru and gif_url; confirmed available in GET /api/exercises
