---
id: S03
parent: M003
milestone: M003
provides:
  - useDisplayName composable for reactive exercise name localization
  - Exercise names and muscle group labels translated in ExercisesView, ExerciseCard, ExerciseHistoryView, WorkoutCard
  - GIF display in ExerciseHistoryView with v-if guard and @error fallback
  - WorkoutCard ExerciseGroup.exerciseId type fixed to string; Map<string, ExerciseGroup>
  - ExerciseCard emit types fixed from number to string
  - SetRow exerciseId prop/emit and workouts store logSet exercise_id type fixed (number→string cascade)
requires:
  - slice: S01
    provides: name_ru and gif_url in GET /api/exercises response; Exercise Beanie model with new fields
  - slice: S02
    provides: vue-i18n registered with legacy:false; useSettingsStore with reactive language; muscle_groups.* locale keys; Exercise TS type with name_ru/gif_url
affects: []
key_files:
  - ../frontend/src/composables/useDisplayName.ts
  - ../frontend/src/views/ExercisesView.vue
  - ../frontend/src/components/workout/ExerciseCard.vue
  - ../frontend/src/views/ExerciseHistoryView.vue
  - ../frontend/src/components/history/WorkoutCard.vue
  - ../frontend/src/components/workout/SetRow.vue
  - ../frontend/src/stores/workouts.ts
key_decisions:
  - useDisplayName returns a plain function (not computed) — reads settingsStore.language inside reactive contexts; avoids per-exercise computed overhead (D029)
  - SetRow and workouts store logSet also fixed number→string to cascade type correctness end-to-end (D030)
patterns_established:
  - useDisplayName() composable: call in setup, use displayName(exercise) inline in templates
  - Muscle group translation: t('muscle_groups.' + exercise.muscle_group)
  - GIF error fallback: @error="($event.target as HTMLImageElement).style.display = 'none'"
observability_surfaces:
  - Vue DevTools → Pinia → settings store → language field shows current locale; changing it propagates instantly to all views
  - npm run build surfaces all TypeScript type errors
  - vue-i18n console warnings for missing muscle_groups.X keys (none present — all 6 keys covered)
drill_down_paths:
  - .gsd/milestones/M003/slices/S03/tasks/T01-SUMMARY.md
duration: ~25m
verification_result: passed
completed_at: 2026-03-14
---

# S03: Exercise name localization + GIF display + type fix

**Wired reactive exercise name localization across all four views, added GIF display with error fallback in ExerciseHistoryView, and fixed Exercise.id-related TypeScript type bugs throughout the frontend.**

## What Happened

The slice had a single task (T01) covering composable creation, four-view wiring, GIF display, and type fixes.

**useDisplayName composable** was created at `src/composables/useDisplayName.ts`. It returns a plain function `displayName(exercise)` that reads `settingsStore.language` at call time. Because the function is called inside Vue reactive contexts (templates, computed properties), Vue's dependency tracking picks up the `language` ref automatically — no explicit `computed()` wrapper needed per exercise.

**Four-view wiring:**
- *ExercisesView*: muscle group headers use `t('muscle_groups.' + group.name)`; exercise names use `displayName(exercise)`
- *ExerciseCard*: both `exercise.name` and `exercise.muscle_group` label replaced with localized equivalents; all 5 emit type annotations corrected from `number` to `string`
- *ExerciseHistoryView*: exercise name heading replaced with `displayName`; muscle group subtitle replaced with `t('muscle_groups.' + ...)`; GIF `<img>` block added with `v-if="exercise?.gif_url"` guard and `@error` handler that sets `display:none` on broken loads
- *WorkoutCard*: `ExerciseGroup` interface `exerciseId` changed to `string`; Map typed as `Map<string, ExerciseGroup>`; exercises store imported for cross-reference; `displayName` replaces hardcoded exercise name lookup

**Cascaded type fixes**: fixing ExerciseCard emit types surfaced pre-existing `number` type bugs in `SetRow.vue` (prop + emit) and `workouts.ts` (`logSet` signature). These were fixed in the same pass to achieve a zero-error build.

**seed.py**: Already had a real Wikimedia GIF URL for Barbell Bench Press (`Bench_press_2.gif`) from S01 — no change needed.

## Verification

- `cd ../frontend && npm run build` — ✅ zero errors, 110 modules transformed (3.56s)
- `cd ../backend && uv run pytest tests/ -q` — ✅ 64 passed (23.60s)
- Browser (Russian): ExercisesView shows "Руки", "Спина", "Грудь", "Пресс", "Ноги", "Плечи"; exercise names in Russian ("Жим штанги лёжа")
- Browser: ExerciseHistoryView for Barbell Bench Press shows "Жим штанги лёжа" heading and "Грудь · Barbell" subtitle
- Browser (English toggle): ExercisesView reverts to "Arms", "Back", "Chest", "Core", "Legs", "Shoulders"
- GIF `<img>` element present in DOM with correct Wikimedia URL; `@error` handler hides it when URL is inaccessible

## Requirements Advanced

- none (S03 is the final closing slice of M003; all requirements validated in S01/S02)

## Requirements Validated

- none new (M003 requirements tracked via milestone-level DoD, validated collectively)

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- **Scope expansion**: SetRow.vue and workouts.ts required number→string fixes (not in original T01 plan) to achieve zero build errors. These were pre-existing type bugs exposed when ExerciseCard emit types were corrected. Fixed in-place rather than deferring.
- **seed.py unchanged**: Plan included adding a gif_url for Bench Press, but S01 had already done this. No change needed.

## Known Limitations

- GIF from Wikimedia Commons may not load in dev environment due to CORS or network access restrictions. The `@error` handler correctly hides broken images. Production users with open internet access will see the GIF.
- Only Barbell Bench Press has a confirmed gif_url in seed data. Other exercises have `gif_url: null` and correctly show no image element.

## Follow-ups

- none — this is the final slice of M003

## Files Created/Modified

- `../frontend/src/composables/useDisplayName.ts` — new composable; reactive display name based on language setting
- `../frontend/src/views/ExercisesView.vue` — localized exercise names and muscle group headers
- `../frontend/src/components/workout/ExerciseCard.vue` — localized name/muscle_group; emit types fixed (number→string)
- `../frontend/src/views/ExerciseHistoryView.vue` — localized name/muscle_group; GIF display block with v-if + @error
- `../frontend/src/components/history/WorkoutCard.vue` — fixed types; exercises store cross-reference; localized names
- `../frontend/src/components/workout/SetRow.vue` — exerciseId prop and emit type fixed (number→string)
- `../frontend/src/stores/workouts.ts` — logSet exercise_id type fixed (number→string)

## Forward Intelligence

### What the next slice should know
- `useDisplayName` is available for any new view that displays exercise names — import it and call `displayName(exercise)` inline
- All exercise ID types are now consistently `string` throughout the frontend; any new component should use `string` for exercise IDs
- muscle_groups locale keys cover exactly 6 values: Arms, Back, Chest, Core, Legs, Shoulders — any new muscle group added to seed data requires a locale key in both `en.ts` and `ru.ts`

### What's fragile
- GIF display depends on Wikimedia Commons URLs being accessible — there's no CDN proxy or local cache; if Commons goes down, all GIFs 404 silently (handled by @error)
- `useDisplayName` reactivity depends on the function being called inside a Vue reactive context; if called outside setup/template it won't be reactive

### Authoritative diagnostics
- Vue DevTools → Pinia → settings store → `language` — single source of truth for current locale; if language switch doesn't propagate, check this value first
- `npm run build` — canonical check for type correctness; zero TypeScript errors confirms all ID types are consistent

### What assumptions changed
- Assumed seed.py needed a gif_url for Bench Press — S01 had already added it; no change needed in this slice
