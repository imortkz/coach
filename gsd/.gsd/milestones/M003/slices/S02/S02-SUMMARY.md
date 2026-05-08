---
id: S02
parent: M003
milestone: M003
provides:
  - vue-i18n v9 plugin registered in main.ts (legacy: false, fallbackLocale: 'en')
  - English and Russian locale files with full string inventory (7 namespaces, 30 keys each)
  - useSettingsStore Pinia store syncing language to PUT/GET /api/settings/language
  - SettingsView with two-button language toggle and "Saved"/"Сохранено" feedback
  - /settings route in router with gear icon in 5th nav tab
  - Language loaded in router beforeEach guard after fetchMe()
  - Exercise.id TypeScript type fixed from number to string
  - name_ru and gif_url optional fields added to Exercise TypeScript type
  - $t() reactive strings in App.vue, ExercisesView, ExerciseHistoryView
requires:
  - slice: S01
    provides: PUT/GET /api/settings/language backend endpoint (from M001, available since M001)
affects:
  - S03
key_files:
  - ../frontend/src/plugins/i18n.ts
  - ../frontend/src/locales/en.ts
  - ../frontend/src/locales/ru.ts
  - ../frontend/src/stores/settings.ts
  - ../frontend/src/views/SettingsView.vue
  - ../frontend/src/main.ts
  - ../frontend/src/router/index.ts
  - ../frontend/src/App.vue
  - ../frontend/src/types/index.ts
  - ../frontend/src/stores/exercises.ts
  - ../frontend/src/views/ExercisesView.vue
  - ../frontend/src/views/ExerciseHistoryView.vue
key_decisions:
  - vue-i18n v9 with legacy:false for Composition API reactive locale switching
  - i18n instance exported from plugins/i18n.ts as plain module; store imports directly (no useI18n() outside components)
  - loadLanguage() catches 404 silently (expected on first use); non-404 errors log as [SettingsStore] prefix
  - Language loaded once in router beforeEach guard after fetchMe(), not in component onMounted
  - navItems use i18n key names (not display strings); $t('nav.' + item.label) pattern
  - Muscle group translation via static locale keys, not API — finite 6-value set, avoids backend changes
  - Settings view as 5th nav tab with gear icon — no existing settings surface
  - Exercise.id fixed from number to string — MongoDB uses UUID strings; zero marginal cost while touching type file
patterns_established:
  - Store accessing i18n locale via i18n.global.locale.value (not useI18n()) — safe outside component context
  - useI18n() composable in script setup for reactive t() calls in Vue 3 components
  - navItems use i18n key names, resolved at render time via $t('nav.' + item.label)
  - Router guard pattern: devLogin → fetchMe → loadLanguage → return true
observability_surfaces:
  - i18n.global.locale.value readable in browser devtools console — shows current locale
  - useSettingsStore().language inspectable in Vue Devtools Pinia panel
  - GET /api/settings/language returns {"key":"language","value":"ru"} confirming persistence
  - Console logs [SettingsStore] loadLanguage/setLanguage errors on non-404 failures
drill_down_paths:
  - .gsd/milestones/M003/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M003/slices/S02/tasks/T02-SUMMARY.md
duration: ~35m (T01: ~25m, T02: ~10m)
verification_result: passed
completed_at: 2026-03-14
---

# S02: vue-i18n infrastructure + Settings view with language toggle

**Full i18n stack delivered: vue-i18n v9 plugin, EN/RU locale files, settings store synced to backend, Settings view with reactive language toggle, 5th gear nav tab, and Exercise.id type fixed — all verified with zero build errors and live browser persistence test.**

## What Happened

Two tasks executed in sequence, together completing the entire i18n infrastructure and settings surface.

**T01** built the infrastructure from the ground up: installed vue-i18n v9 (`npm install vue-i18n@9`), created `plugins/i18n.ts` with `createI18n({ legacy: false })`, authored English and Russian locale files covering 7 namespaces (nav, muscle_groups, exercises, workout, history, programs, settings), created `useSettingsStore` that mutates `i18n.global.locale.value` directly (importing the i18n instance as a plain module — no `useI18n()` in store context), built `SettingsView.vue` with a two-button toggle showing "Saved"/"Сохранено" confirmation, added the `/settings` route, wired `app.use(i18n)` in main.ts, and added `await settingsStore.loadLanguage()` in the router `beforeEach` guard.

**T02** wired `$t()` throughout the app: fixed `Exercise.id` from `number` to `string` in types, added `name_ru` and `gif_url` optional fields to the type, updated `updateExercise`/`deleteExercise` store params to `string`, added the 5th gear nav item in App.vue with `t('nav.' + item.label)` for all five tabs, replaced all hardcoded strings in ExercisesView (title, search placeholder, filter options, loading, empty state, form labels, buttons) and ExerciseHistoryView (loading, error text) with `t()` calls, and fixed `Number(route.params.id)` → `route.params.id as string` in ExerciseHistoryView.

## Verification

- `cd ../frontend && npm run build` — ✅ Zero TypeScript errors, zero template compilation errors (109 modules, built in ~2.5s)
- Browser: `/settings` route renders with "Settings" heading and language toggle
- Browser: clicking "Russian" → heading instantly changes to "Настройки", nav labels switch to Russian, "Сохранено" feedback shown
- Backend: `GET /api/settings/language` returns `{"key":"language","value":"ru"}` — PUT persisted correctly
- Browser: refresh → Russian still selected (loaded from backend via router guard before render)
- Browser assertions: 4/4 PASS (url contains /settings, "Настройки" visible, "Язык" visible, "Русский" visible)
- Hardcoded string grep in ExercisesView — zero matches for "Loading exercises", "Search exercises", "All Equipment", "No exercises found", "Try again"

## Requirements Advanced

- None — this slice adds new localization capability not tracked as an Active requirement in REQUIREMENTS.md

## Requirements Validated

- None — no existing Active requirements map to this slice

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

None. Implemented exactly as planned. Used `useI18n()` composable (Composition API pattern) rather than template-only `$t()` in script blocks — this is the canonical Vue 3 approach and functionally equivalent.

## Known Limitations

- vue-i18n v9 shows deprecation warning (`v9 no longer supported`). v9 is pinned per plan constraint for Vue 3 Composition API compatibility. Migration to v11 is out of scope for M003.
- Only App.vue, ExercisesView, and ExerciseHistoryView have `$t()` wiring. WorkoutView, ProgramsView, ProgramEditView, and WorkoutView still have some hardcoded English strings — these are out of scope for S02 (exercise name localization, the main user-facing concern, is in S03).
- Exercise names themselves still render in English regardless of language setting — S03 wires `name_ru` for that.

## Follow-ups

- S03: Wire `name_ru` for exercise name display in ExercisesView, ExerciseCard, ExerciseHistoryView, WorkoutCard
- S03: Wire `gif_url` for exercise GIF display
- S03: Translate muscle group filter labels using `t('muscle_groups.' + group)` (locale keys are ready in en.ts/ru.ts)

## Files Created/Modified

- `../frontend/src/plugins/i18n.ts` — new: i18n instance module (legacy: false, en/ru messages)
- `../frontend/src/locales/en.ts` — new: English messages (7 namespaces, 30 keys)
- `../frontend/src/locales/ru.ts` — new: Russian messages (7 namespaces, 30 keys)
- `../frontend/src/stores/settings.ts` — new: useSettingsStore with loadLanguage + setLanguage
- `../frontend/src/views/SettingsView.vue` — new: Settings page with language toggle, save feedback
- `../frontend/src/main.ts` — modified: added app.use(i18n)
- `../frontend/src/router/index.ts` — modified: /settings route + loadLanguage in beforeEach guard
- `../frontend/src/App.vue` — modified: 5th gear nav item, useI18n(), $t() nav labels
- `../frontend/src/types/index.ts` — modified: Exercise.id: string, added name_ru and gif_url optional fields
- `../frontend/src/stores/exercises.ts` — modified: updateExercise and deleteExercise id params changed to string
- `../frontend/src/views/ExercisesView.vue` — modified: editingId: string | null, all hardcoded strings → t()
- `../frontend/src/views/ExerciseHistoryView.vue` — modified: exerciseId as string, loading/error strings → t()

## Forward Intelligence

### What the next slice should know
- Locale keys are already defined for muscle_groups (en.ts: `muscle_groups.Chest = "Chest"`, ru.ts: `muscle_groups.Chest = "Грудь"`). S03 can wire `t('muscle_groups.' + exercise.muscle_group)` directly — no locale file changes needed.
- `name_ru` and `gif_url` are already in the Exercise TypeScript type as optional fields. S03 just needs to use them in templates with null guards.
- `useSettingsStore().language` is a reactive ref — S03 components can `watch` it or use computed properties to switch between `name` and `name_ru`.
- The i18n instance is at `src/plugins/i18n.ts` — import as `import { i18n } from '@/plugins/i18n'` for direct locale access outside components.

### What's fragile
- vue-i18n v9 deprecation — the library still works but any upgrade to v10/v11 will require API changes (especially `createI18n` options and `useI18n()` return types). Don't upgrade during M003.
- `i18n.global.locale.value` mutation in the store — this bypasses Vue's reactivity system for the i18n locale; it works because vue-i18n tracks locale internally as a ref, but it's a direct mutation pattern that's subtle.

### Authoritative diagnostics
- `i18n.global.locale.value` in browser devtools console — ground truth for current active locale
- `GET /api/settings/language` with auth bearer token — ground truth for persisted backend preference
- `npm run build` output — ground truth for TypeScript correctness; zero errors means all type contracts hold

### What assumptions changed
- No assumptions changed. Plan was accurate throughout.
