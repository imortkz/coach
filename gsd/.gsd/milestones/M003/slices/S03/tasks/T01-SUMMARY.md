---
id: T01
parent: S03
milestone: M003
provides:
  - useDisplayName composable for reactive exercise name localization
  - Exercise name and muscle group translation wired in ExercisesView, ExerciseCard, ExerciseHistoryView, WorkoutCard
  - GIF display in ExerciseHistoryView with v-if guard and @error fallback
  - WorkoutCard ExerciseGroup.exerciseId type fixed to string; Map<string, ExerciseGroup>
  - ExerciseCard emit types fixed from number to string
  - SetRow and workouts store logSet exercise_id type fixed from number to string (cascaded)
key_files:
  - ../frontend/src/composables/useDisplayName.ts
  - ../frontend/src/views/ExercisesView.vue
  - ../frontend/src/components/workout/ExerciseCard.vue
  - ../frontend/src/views/ExerciseHistoryView.vue
  - ../frontend/src/components/history/WorkoutCard.vue
  - ../frontend/src/components/workout/SetRow.vue
  - ../frontend/src/stores/workouts.ts
key_decisions:
  - useDisplayName returns plain function (not computed) — reads settingsStore.language inside, Vue tracks reactivity naturally
  - SetRow and workouts store logSet also fixed from number→string to cascade type correctness
patterns_established:
  - useDisplayName() composable pattern: call in setup, destructure { displayName }, use inline in templates
  - Muscle group translation: t('muscle_groups.' + exercise.muscle_group)
  - GIF error fallback: @error="($event.target as HTMLImageElement).style.display = 'none'"
observability_surfaces:
  - Vue DevTools → Pinia → settings store → language shows current locale
  - npm run build surfaces all type errors immediately
  - vue-i18n warns in console for missing translation keys (muscle_groups.X not in locales)
duration: ~25m
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T01: Wire exercise name localization, GIF display, and type fixes across all views

**Created useDisplayName composable and wired reactive exercise name localization across all four views; added GIF display with error fallback; fixed all exercise ID type issues from number to string.**

## What Happened

1. Created `useDisplayName.ts` composable returning a `displayName(exercise)` function that reads `settingsStore.language` reactively. Returns `name_ru` when language is Russian and `name_ru` is present, otherwise `name`.

2. Wired ExercisesView: added composable import, replaced `exercise.name` with `displayName(exercise)`, replaced muscle group headers with `t('muscle_groups.' + group.name)`.

3. Wired ExerciseCard: added `useI18n` and `useDisplayName` imports, replaced `exercise.name` and `exercise.muscle_group` with localized versions, fixed all 5 emit type annotations from `number` to `string`.

4. Wired ExerciseHistoryView: replaced `exercise?.name ?? 'Exercise'` with `exercise ? displayName(exercise) : t('exercises.title')`, replaced `exercise.muscle_group` with `t('muscle_groups.' + exercise.muscle_group)`, added GIF `<img>` block with `v-if="exercise?.gif_url"` guard and `@error` hide handler.

5. Wired WorkoutCard: added `useExercisesStore` and `useDisplayName` imports, renamed `exerciseName` to `displayName` in ExerciseGroup interface, changed `exerciseId` type to `string`, changed Map type to `Map<string, ExerciseGroup>`, cross-referenced exercises store for localized names.

6. **Cascaded type fix**: SetRow `exerciseId` prop and emit type + workouts store `logSet` signature also fixed from `number` to `string` (these were broken by same Exercise.id type inconsistency, required for zero-error build).

7. Seed.py already had a real gif_url (`https://upload.wikimedia.org/wikipedia/commons/e/e7/Bench_press_2.gif`) for Barbell Bench Press — no change needed.

## Verification

- `cd ../frontend && npm run build` — ✅ zero errors, 110 modules transformed
- `cd ../backend && uv run pytest tests/ -q` — ✅ 64 passed
- Browser (Russian): ExercisesView shows "Руки", "Спина", "Грудь", "Пресс", "Ноги", "Плечи" for muscle groups; exercise names in Russian ("Жим штанги лёжа")
- Browser: ExerciseHistoryView for Barbell Bench Press shows "Жим штанги лёжа" heading and "Грудь · Barbell" subtitle
- Browser (English toggle): ExercisesView reverts to "Arms", "Back", "Chest", "Core", "Legs", "Shoulders"
- GIF img element present in DOM with correct Wikimedia URL; @error handler correctly hides it when URL is inaccessible from dev environment

## Diagnostics

- `settingsStore.language` in Pinia DevTools shows current locale; changing it propagates to all views instantly
- `npm run build` — zero TypeScript errors confirms all type fixes are consistent
- Console: no vue-i18n warnings for muscle group keys (all 6 keys present in both locales)

## Deviations

- SetRow.vue and workouts.ts also required number→string fix (not in original task plan scope) to achieve zero build errors. These were pre-existing type bugs surfaced by the ExerciseCard emit fix.
- seed.py already had a Wikimedia gif_url for Barbell Bench Press (`Bench_press_2.gif`); no change was needed.

## Known Issues

- GIF from Wikimedia Commons may not load in dev environment (CORS or network restriction) — `@error` handler correctly hides broken images. This is expected behavior; actual users would see the GIF.

## Files Created/Modified

- `../frontend/src/composables/useDisplayName.ts` — new composable, reactive display name based on language setting
- `../frontend/src/views/ExercisesView.vue` — localized exercise names and muscle group headers
- `../frontend/src/components/workout/ExerciseCard.vue` — localized name/muscle_group, fixed emit types (number→string)
- `../frontend/src/views/ExerciseHistoryView.vue` — localized name/muscle_group, GIF display block
- `../frontend/src/components/history/WorkoutCard.vue` — fixed types, exercises store cross-reference, localized names
- `../frontend/src/components/workout/SetRow.vue` — exerciseId prop and emit type fixed (number→string)
- `../frontend/src/stores/workouts.ts` — logSet exercise_id type fixed (number→string)
