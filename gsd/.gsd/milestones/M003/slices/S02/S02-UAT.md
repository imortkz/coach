# S02: vue-i18n infrastructure + Settings view with language toggle — UAT

**Milestone:** M003
**Written:** 2026-03-14

## UAT Type

- UAT mode: live-runtime
- Why this mode is sufficient: Reactive locale switching requires a running browser to verify — static build checks alone cannot confirm that `$t()` calls update dynamically when locale changes. Backend persistence requires a live API call.

## Preconditions

1. Frontend dev server running: `cd ../frontend && npm run dev` (or production build served)
2. Backend running: `cd ../backend && uv run uvicorn app.main:app --reload`
3. DEV_MODE=true in backend environment (or valid JWT available)
4. App accessible at http://localhost:5173 (or equivalent)
5. Browser devtools available (for console/network inspection)
6. Any prior language preference cleared: `DELETE /api/settings/language` or start with fresh DB

## Smoke Test

Navigate to http://localhost:5173/settings — page must load with a "Settings" heading and two language buttons ("English", "Russian"). If this renders, basic i18n infrastructure is working.

## Test Cases

### 1. Settings view renders and is accessible via nav

1. Navigate to http://localhost:5173 (any view)
2. Observe the bottom navigation bar (mobile) or top nav (desktop)
3. **Expected:** A 5th icon appears (gear/cog icon) alongside Exercises, Workout, History, Programs
4. Click the gear icon
5. **Expected:** URL changes to `/settings`; page shows heading "Settings" (EN), a "Language" label, and two buttons: "English" (highlighted/selected) and "Russian"

### 2. Language toggle switches all static UI strings to Russian

1. Navigate to http://localhost:5173/settings (language must be English/default)
2. Click the "Russian" button
3. **Expected:**
   - The page heading immediately changes to "Настройки"
   - The label changes to "Язык"
   - The "Russian" button becomes "Русский" and appears selected (blue border or highlighted)
   - The "English" button becomes "English" (or "Английский" per locale)
   - A brief "Сохранено" confirmation appears and fades after ~2 seconds
4. Without navigating, observe the nav labels
5. **Expected:** All 5 nav labels switch to Russian (e.g., "Упражнения", "Тренировка", "История", "Программы", "Настройки")

### 3. Language preference persists across page refresh

1. With language set to Russian (from Test Case 2), refresh the browser (F5 / Cmd+R)
2. **Expected:** Page loads showing Russian UI — heading "Настройки", toggle shows "Русский" selected
3. Navigate to another view (e.g., Exercises)
4. **Expected:** View title and UI strings render in Russian (e.g., page title is Russian equivalent)

### 4. Language preference persists in backend

1. With language set to Russian, open browser devtools console
2. Run: `fetch('/api/settings/language', { headers: { Authorization: 'Bearer ' + localStorage.getItem('gymcoach_token') } }).then(r => r.json()).then(console.log)`
3. **Expected:** Response is `{"key": "language", "value": "ru"}` (200 OK)

### 5. Toggle back to English reverts all strings

1. With language set to Russian, navigate to `/settings`
2. Click the "English" / "Английский" button
3. **Expected:**
   - Heading immediately changes back to "Settings"
   - Label changes to "Language"
   - "English" button appears selected
   - "Saved" confirmation appears briefly
4. Navigate to Exercises view
5. **Expected:** UI strings are in English (title, search placeholder, filter options, button labels)

### 6. Default language on first use is English

1. Ensure no language preference is saved (fresh install or cleared setting)
2. Navigate to any view
3. **Expected:** UI renders in English — no Russian strings visible
4. Navigate to `/settings`
5. **Expected:** "English" button is selected (highlighted)

### 7. ExercisesView static strings are reactive

1. Set language to English
2. Navigate to Exercises view
3. **Expected:** Search placeholder in English (e.g., "Search exercises..."), filter shows "All Equipment" or equivalent
4. Switch language to Russian via Settings (or open devtools and run `i18n.global.locale.value = 'ru'`)
5. Navigate back to Exercises view
6. **Expected:** Search placeholder and filter label show Russian strings; "Add Exercise" button shows Russian text

### 8. Build produces zero TypeScript errors

1. Run `cd ../frontend && npm run build`
2. **Expected:** Build completes successfully with "✓ built in X.XXs"; zero TypeScript errors; zero template compilation warnings about missing keys

## Edge Cases

### First visit with no backend language set (404 handling)

1. Clear the language setting from the database
2. Navigate to any view
3. **Expected:** App loads normally in English; no error toast or console error about 404 (404 is silently swallowed, default 'en' applied)
4. Console should NOT show `[SettingsStore] loadLanguage error:` for 404 responses

### Network error during setLanguage (non-404)

1. Set language in Settings while backend is unreachable (stop backend)
2. **Expected:** Console shows `[SettingsStore] setLanguage error:` message; locale may still change locally but won't persist; no app crash

### Exercise.id is string type (TypeScript enforcement)

1. Run `cd ../frontend && npm run build`
2. **Expected:** Build succeeds — TypeScript type for `Exercise.id` is `string`; any code that was comparing it to a number would fail compilation
3. Verify: grep in ExerciseHistoryView shows `route.params.id as string` (no `Number()` cast)

## Failure Signals

- "Settings" nav icon missing → 5th nav item not added to App.vue
- `/settings` returns 404 → route not registered in router/index.ts
- Language change doesn't update nav labels immediately → navItems is not using `t()` or locale ref is not reactive
- Browser refresh resets to English → loadLanguage() not called in router guard, or store state not persisting to backend
- Build fails with TypeScript error about `id: number` → Exercise.id type fix not applied correctly
- `[SettingsStore] loadLanguage error:` in console on fresh install → 404 not being caught silently
- Russian button shows raw key like `nav.settings` → locale file missing that key

## Requirements Proved By This UAT

- LOC-01 (implied) — User can switch language between English and Russian
- LOC-02 (implied) — Language preference persists across refresh via backend storage
- LOC-03 (implied) — Static UI strings (nav, view titles, buttons) are reactive to locale changes
- FIX-01 (implied) — Exercise.id TypeScript type is string (compiler-enforced)

## Not Proven By This UAT

- Exercise names displaying in Russian (`name_ru` field) — this is S03 scope
- Muscle group labels rendering in Russian in ExercisesView filter — S03 scope (locale keys are ready, but the filter UI wiring is S03)
- GIF display for exercises — S03 scope
- Full coverage of all views (WorkoutView, ProgramsView, ProgramEditView still have some hardcoded strings) — deferred

## Notes for Tester

- The vue-i18n v9 deprecation warning in the browser console is expected and benign — it does not affect functionality
- `i18n.global.locale.value` is the authoritative live signal for current locale state; inspect it in browser devtools at any time
- If a string appears as its raw key (e.g. `exercises.loading`) instead of translated text, the key is missing from one of the locale files — check `src/locales/en.ts` or `src/locales/ru.ts`
- The "Saved"/"Сохранено" feedback is a 2-second timer; it will disappear automatically — this is intentional
- Dev mode auto-login means no manual JWT setup is needed for local testing with DEV_MODE=true
