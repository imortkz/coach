---
estimated_steps: 7
estimated_files: 6
---

# T01: Wire exercise name localization, GIF display, and type fixes across all views

**Slice:** S03 — Exercise name localization + GIF display + type fix
**Milestone:** M003

## Description

Create a `useDisplayName` composable that reactively returns `name_ru || name` when language is Russian, then wire it across ExercisesView, ExerciseCard, ExerciseHistoryView, and WorkoutCard. Add muscle group translation via `t()` in ExercisesView and ExerciseCard. Add GIF display to ExerciseHistoryView with null guard and error fallback. Fix WorkoutCard's local `ExerciseGroup.exerciseId` type from `number` to `string` and its Map type. Fix ExerciseCard emit type annotations from `number` to `string`. Add a real Wikimedia Commons gif_url for Bench Press in seed.py.

## Steps

1. **Create `useDisplayName.ts` composable** — `export function useDisplayName()` returning a function `displayName(exercise: Exercise): string` that uses `computed` internally or just reads `useSettingsStore().language` reactively. Pattern: return a function (not a computed per-call) so it can be called inline in templates like `displayName(exercise)`. The function reads `settingsStore.language` (reactive ref) so Vue's reactivity tracks it.

2. **Wire ExercisesView.vue** — Replace `exercise.name` (line 353) with `displayName(exercise)`. Replace muscle group headers with `t('muscle_groups.' + group.name)`. Import composable and destructure. The view already has `useI18n` and `useExercisesStore`.

3. **Wire ExerciseCard.vue** — Add `import { useI18n } from 'vue-i18n'` and `import { useDisplayName } from '@/composables/useDisplayName'`. Replace `exercise.name` (line 176) with `displayName(props.exercise)`. Replace `exercise.muscle_group` display (line 177) with `t('muscle_groups.' + exercise.muscle_group)`. Fix emit type annotations: `exerciseId: number` → `exerciseId: string` in all five emit signatures.

4. **Wire ExerciseHistoryView.vue** — Import and use `useDisplayName`. Replace `exercise?.name ?? 'Exercise'` (line 73) with `exercise ? displayName(exercise) : t('exercises.title')`. Replace `exercise.muscle_group` (line 76) with `t('muscle_groups.' + exercise.muscle_group)`. Add GIF display block after the header div: `<img v-if="exercise?.gif_url" :src="exercise.gif_url" :alt="displayName(exercise)" @error="($event.target as HTMLImageElement).style.display = 'none'" class="w-full max-w-md mx-auto rounded-lg mt-4" />`.

5. **Wire WorkoutCard.vue** — Fix `ExerciseGroup` interface: `exerciseId: string`. Fix Map type: `Map<string, ExerciseGroup>`. Import `useExercisesStore` and `useDisplayName`. In the `exerciseGroups` computed, after building the map from workout sets, cross-reference each group's exerciseId against the exercises store to get the full Exercise object for `displayName()`. Keep `s.exercise?.name || 'Exercise #...'` as fallback when store has no match (exercises may not be loaded). Store the display name in the ExerciseGroup interface (add `displayName: string` field) so the template uses `group.displayName`.

6. **Fix seed.py** — Add a real Wikimedia Commons gif_url for the "Bench Press" entry. Use `https://upload.wikimedia.org/wikipedia/commons/f/f1/Bench_press_1.gif`.

7. **Build and test** — Run `npm run build` (zero errors), `uv run pytest tests/ -q` (all pass).

## Must-Haves

- [ ] `useDisplayName` composable exists and returns reactive display name based on language setting
- [ ] All four views (ExercisesView, ExerciseCard, ExerciseHistoryView, WorkoutCard) use localized exercise names
- [ ] Muscle group labels translated via `t()` in ExercisesView and ExerciseCard
- [ ] GIF displays in ExerciseHistoryView with null guard and error handling
- [ ] WorkoutCard `exerciseId` type is `string`; Map<string, ExerciseGroup>
- [ ] ExerciseCard emit types use `string` not `number` for exercise IDs
- [ ] Bench Press has a real gif_url in seed.py
- [ ] `npm run build` zero errors
- [ ] Backend tests pass

## Observability Impact

**Signals introduced:**
- `[SettingsStore] language` reactive ref change triggers `useDisplayName` recompute across all wired views simultaneously
- GIF `@error` handler silently hides broken images — no console error logged (browser's native image error)
- `t('muscle_groups.' + group)` produces vue-i18n warning `[intlify] Not found 'muscle_groups.X'` if a muscle group key is missing from locales

**How to inspect:**
- Vue DevTools → Pinia → `settings` store → `language` to confirm current locale
- Vue DevTools → Components → any wired view → inspect computed that calls `displayName()` to see reactive result
- `npm run build` output confirms zero TypeScript errors after type fixes

**Failure state visibility:**
- Language not switching: `useDisplayName` not imported or `settingsStore.language` not read inside the returned function (non-reactive closure)
- GIF not showing: `v-if="exercise?.gif_url"` evaluates false; check API response includes `gif_url` field
- Type errors surface as build failures — easy to detect via CI or `npm run build`

- `cd ../frontend && npm run build` — zero TypeScript/template errors
- `cd ../backend && uv run pytest tests/ -q` — ≥59 tests pass
- Browser: set language to Russian → exercise names and muscle groups display in Russian across all views
- Browser: navigate to Bench Press exercise history → GIF image renders
- Browser: switch to English → all names revert

## Inputs

- `../frontend/src/stores/settings.ts` — `useSettingsStore().language` reactive ref (from S02)
- `../frontend/src/locales/en.ts`, `ru.ts` — muscle_groups keys ready (from S02)
- `../frontend/src/types/index.ts` — Exercise type with `name_ru?: string | null`, `gif_url?: string | null`, `id: string` (from S02)
- `../backend/app/seed.py` — seed exercises with name_ru populated, gif_url=None (from S01)

## Expected Output

- `../frontend/src/composables/useDisplayName.ts` — new composable file
- `../frontend/src/views/ExercisesView.vue` — localized exercise names and muscle group headers
- `../frontend/src/components/workout/ExerciseCard.vue` — localized name/muscle_group, fixed emit types
- `../frontend/src/views/ExerciseHistoryView.vue` — localized name/muscle_group, GIF display block
- `../frontend/src/components/history/WorkoutCard.vue` — fixed types, exercises store cross-reference, localized names
- `../backend/app/seed.py` — Bench Press entry has real gif_url
