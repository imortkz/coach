# S03: Exercise name localization + GIF display + type fix — UAT

**Milestone:** M003
**Written:** 2026-03-14

## UAT Type

- UAT mode: live-runtime
- Why this mode is sufficient: All deliverables are UI-visible behaviors (language switching, GIF display) that require a running frontend + backend to verify. TypeScript type correctness is confirmed by `npm run build`.

## Preconditions

1. Backend running: `cd ../backend && uv run uvicorn app.main:app --reload` (port 8000)
2. Frontend running: `cd ../frontend && npm run dev` (port 5173)
3. App is in dev mode (DEV_MODE=true in backend .env) — no Telegram login required
4. Seed data loaded — exercises exist with Russian names and at least Barbell Bench Press has a gif_url
5. `npm run build` has been run and produced zero errors
6. `uv run pytest tests/ -q` has been run and all 64 tests pass

## Smoke Test

Navigate to http://localhost:5173, go to Exercises tab — if exercise names are visible and the app loads without console errors, the basic wiring is intact.

## Test Cases

### 1. Exercise names display in English by default

1. Open http://localhost:5173
2. Navigate to the **Exercises** tab
3. **Expected:** Muscle group headers show English labels: "Arms", "Back", "Chest", "Core", "Legs", "Shoulders"
4. **Expected:** Exercise names under each group show in English (e.g., "Barbell Bench Press", "Pull-up", "Barbell Squat")

### 2. Language toggle switches exercise names to Russian

1. Navigate to the **Settings** tab (gear icon, 5th tab)
2. Toggle language to **Russian** (Русский)
3. Navigate to the **Exercises** tab
4. **Expected:** Muscle group headers show in Russian: "Руки", "Спина", "Грудь", "Пресс", "Ноги", "Плечи"
5. **Expected:** Exercise names show in Russian (e.g., "Жим штанги лёжа" for Barbell Bench Press)
6. **Expected:** No page reload was required — change is reactive

### 3. ExerciseCard displays localized name and muscle group

1. With language set to Russian, navigate to **Exercises** tab
2. Observe any exercise card
3. **Expected:** The card shows the Russian exercise name (e.g., "Жим штанги лёжа")
4. **Expected:** The muscle group label on the card shows in Russian (e.g., "Грудь")
5. Switch language back to English via Settings
6. **Expected:** Card immediately shows English name and muscle group without navigation

### 4. ExerciseHistoryView shows localized name with GIF for Bench Press

1. With language set to Russian, navigate to **Exercises** tab
2. Tap/click on **Barbell Bench Press** (Жим штанги лёжа)
3. **Expected:** ExerciseHistoryView heading shows "Жим штанги лёжа"
4. **Expected:** Subtitle shows "Грудь · Barbell" (muscle group translated, equipment stays as-is)
5. **Expected:** A GIF image is present in the view (may load or show nothing if Wikimedia is inaccessible — no broken image icon should appear)
6. Switch language to English via Settings (back button → Settings → toggle → back to exercise)
7. **Expected:** Heading reverts to "Barbell Bench Press"; subtitle reverts to "Chest · Barbell"

### 5. WorkoutCard in History shows localized exercise names

1. Ensure at least one completed workout exists in history (log a quick set if needed)
2. Navigate to the **History** tab
3. With language set to Russian, open a workout detail that contains exercises
4. **Expected:** Exercise names inside WorkoutCard are shown in Russian
5. Switch language to English in Settings
6. **Expected:** Exercise names in the already-rendered WorkoutCard update to English reactively (or on next navigation)

### 6. Language preference persists across page refresh

1. Set language to Russian in Settings
2. Hard-refresh the browser (Cmd+Shift+R / Ctrl+Shift+R)
3. Navigate to Exercises tab
4. **Expected:** Muscle group headers and exercise names are still in Russian — preference was restored from backend

### 7. Build produces zero TypeScript errors

1. Run: `cd ../frontend && npm run build`
2. **Expected:** Build completes successfully with output ending `✓ built in X.XXs` and no TypeScript errors
3. **Expected:** No errors mentioning `exerciseId`, `logSet`, `emit`, or `Map<number`

### 8. Backend tests all pass

1. Run: `cd ../backend && uv run pytest tests/ -q`
2. **Expected:** Output shows `64 passed` (or more) with zero failures

## Edge Cases

### Exercise with no Russian name falls back to English

1. If any exercise has `name_ru: null` (custom user exercise or incomplete seed entry)
2. With language set to Russian, navigate to Exercises tab
3. **Expected:** That exercise's English name is shown — no blank/empty name cell, no "undefined", no crash

### Exercise without a GIF shows no image element

1. Navigate to any exercise other than Barbell Bench Press in ExerciseHistoryView
2. **Expected:** No `<img>` element is rendered — no broken image icon, no empty image placeholder
3. Inspect DOM to confirm absence of `<img>` for gif

### GIF load failure is handled gracefully

1. If network access to Wikimedia Commons is blocked (common in dev environments)
2. Navigate to Barbell Bench Press in ExerciseHistoryView
3. **Expected:** The `<img>` element is hidden (display:none) by the @error handler — no broken image icon visible to user

### Switching language back to English reverts all views

1. Set language to Russian
2. Verify Russian names showing in Exercises tab
3. Navigate to Settings, toggle back to English
4. Navigate to Exercises tab
5. **Expected:** All headers and names immediately show in English — no stale Russian text remains

## Failure Signals

- Muscle group headers not translating → `t('muscle_groups.X')` key missing in locale file or vue-i18n not registered
- Exercise names not switching → `useDisplayName` composable not imported/wired in that view, or `settingsStore.language` not reactive
- Broken image icon on Barbell Bench Press → `v-if="exercise?.gif_url"` guard missing, or @error handler not firing
- TypeScript build errors mentioning `number` vs `string` on exercise IDs → type fix not cascaded to SetRow or workouts store
- `npm run build` fails → check for remaining `Map<number` or `emit('select', exercise.id as number)` patterns

## Requirements Proved By This UAT

- LOC-04 (exercise names use name_ru when language is Russian in ExercisesView, ExerciseCard, ExerciseHistoryView, WorkoutCard)
- LOC-05 (muscle group labels translated in ExercisesView and ExerciseCard)
- LOC-06 (exercise GIF displays inline with graceful null handling)
- FIX-01 (Exercise.id TypeScript type is string)

## Not Proven By This UAT

- Seed upsert safety (proved in S01 UAT — upsert doesn't clobber custom exercises)
- vue-i18n registration and static UI string switching (proved in S02 UAT)
- Language persistence to backend (proved in S02 UAT — Settings view PUT /api/settings/language)
- ~120–180 total exercises seeded (proved in S01 UAT)

## Notes for Tester

- GIF from Wikimedia Commons (`Bench_press_2.gif`) may not render in dev environments due to network restrictions — this is expected. The `@error` handler hides it silently. Verify by checking the DOM: the `<img>` element should be present but have `style="display: none"`. A broken image icon would indicate the @error handler failed.
- Language switching is reactive — no page reload needed. If a reload is required to see changes, that's a bug in `useDisplayName` wiring or `useSettingsStore` reactivity.
- Vue DevTools are the fastest diagnostic: Pinia → settings store → `language` field shows the current locale. If the store shows the correct language but the UI doesn't update, the composable isn't reactive in that view.
