# S02: vue-i18n infrastructure + Settings view with language toggle

**Goal:** User can navigate to Settings, toggle language between English and Russian, and see all static UI strings switch reactively; preference persists across refresh.
**Demo:** Open Settings → toggle to Russian → nav labels, view titles, button text all switch to Russian → refresh → still Russian → toggle back to English → all revert.

## Must-Haves

- vue-i18n v9 installed and registered with `legacy: false`, `fallbackLocale: 'en'`
- English and Russian locale files with all static UI strings including `muscle_groups.*` namespace
- `useSettingsStore` Pinia store syncs language to `PUT/GET /api/settings/language`; defaults to `'en'` on 404
- Settings view with language toggle accessible from 5th nav tab (gear icon)
- Language loads once in router guard after `fetchMe()`, before first view renders
- `Exercise.id` TypeScript type fixed from `number` to `string`; ripple fixes in exercises store and views
- All hardcoded UI strings in App.vue, ExercisesView, ExerciseHistoryView replaced with `t()` / `$t()` calls
- `npm run build` passes clean (zero TypeScript errors)

## Proof Level

- This slice proves: integration (i18n plugin + store + backend settings + reactive UI)
- Real runtime required: yes (browser verification of reactive locale switching)
- Human/UAT required: no (build pass + browser check sufficient)

## Verification

- `cd ../frontend && npm run build` — zero errors (TypeScript + template compilation)
- Browser: navigate to `/settings`, toggle to Russian, verify nav labels changed, refresh, verify language persisted

## Observability / Diagnostics

- **Runtime signals:** `i18n.global.locale.value` readable in browser devtools console; `useSettingsStore().language` ref inspectable via Vue Devtools Pinia panel
- **Locale persistence:** Backend state inspectable via `GET /api/settings/language` — returns `{"key": "language", "value": "ru"}` or 404 if never set
- **Language load failure:** `loadLanguage()` catches 404 silently (expected); any 5xx or network error logs to console as `[SettingsStore] loadLanguage error:` and defaults to `'en'`
- **Build failures:** `npm run build` surfaces all TypeScript errors including `Exercise.id` type ripple — run in CI and locally to catch regressions
- **Inspection command:** `localStorage.getItem('gymcoach_token')` confirms auth token present; `fetch('/api/settings/language', { headers: { Authorization: 'Bearer ' + localStorage.getItem('gymcoach_token') } }).then(r => r.json()).then(console.log)` shows persisted language
- **Redaction:** JWT token in localStorage is a dev concern only (no production users); no PII in settings response; language value is `'en'` or `'ru'` — safe to log

## Integration Closure

- Upstream surfaces consumed: `PUT/GET /api/settings/language` (existing backend endpoint from M001)
- New wiring introduced: vue-i18n plugin in main.ts, settings store in router guard, `$t()` in templates
- What remains before milestone is truly usable end-to-end: S03 (exercise name localization via `name_ru` + GIF display)

## Tasks

- [x] **T01: Install vue-i18n and build i18n infrastructure with Settings view** `est:45m`
  - Why: Creates the entire i18n stack from scratch — plugin, locales, store, view, route, and wiring
  - Files: `../frontend/src/plugins/i18n.ts`, `../frontend/src/locales/en.ts`, `../frontend/src/locales/ru.ts`, `../frontend/src/stores/settings.ts`, `../frontend/src/views/SettingsView.vue`, `../frontend/src/main.ts`, `../frontend/src/router/index.ts`
  - Do: `npm install vue-i18n@9`; create `plugins/i18n.ts` exporting `createI18n({ legacy: false })`; create `en.ts` and `ru.ts` with full string inventory (nav, muscle_groups, exercises, workout, history, programs, settings); create `useSettingsStore` that imports i18n instance directly (NOT `useI18n()`) for `i18n.global.locale.value` mutation; create `SettingsView.vue` with language toggle UI; add `/settings` route; wire `app.use(i18n)` in main.ts; add `await settingsStore.loadLanguage()` in router guard after `fetchMe()`
  - Verify: `npm run build` passes; `/settings` route renders; language toggle calls backend
  - Done when: Settings view accessible from nav, language toggle switches `i18n.global.locale.value` and persists to backend

- [x] **T02: Wire t() into App.vue and views, fix Exercise.id type to string** `est:30m`
  - Why: Makes all static strings reactive to locale changes and fixes the UUID type mismatch
  - Files: `../frontend/src/App.vue`, `../frontend/src/types/index.ts`, `../frontend/src/stores/exercises.ts`, `../frontend/src/views/ExercisesView.vue`, `../frontend/src/views/ExerciseHistoryView.vue`
  - Do: In App.vue — add 5th gear nav item, make `navItems` a `computed` (or use `$t()` directly in template) so labels are reactive; add gear SVG icon. In types/index.ts — change `Exercise.id: number` to `string`, add `name_ru?: string | null` and `gif_url?: string | null`. In exercises.ts — change `id: number` params to `string` in `updateExercise` and `deleteExercise`. In ExercisesView.vue — fix `editingId` ref type to `ref<string | null>`, replace hardcoded strings with `$t()`. In ExerciseHistoryView.vue — change `Number(route.params.id)` to `route.params.id as string`, replace hardcoded strings with `$t()`
  - Verify: `npm run build` passes clean (all type errors resolved)
  - Done when: All nav labels and view strings use `$t()`, `Exercise.id` is `string` throughout, zero TS errors

## Files Likely Touched

- `../frontend/package.json` (npm install)
- `../frontend/src/plugins/i18n.ts` (new)
- `../frontend/src/locales/en.ts` (new)
- `../frontend/src/locales/ru.ts` (new)
- `../frontend/src/stores/settings.ts` (new)
- `../frontend/src/views/SettingsView.vue` (new)
- `../frontend/src/main.ts`
- `../frontend/src/router/index.ts`
- `../frontend/src/App.vue`
- `../frontend/src/types/index.ts`
- `../frontend/src/stores/exercises.ts`
- `../frontend/src/views/ExercisesView.vue`
- `../frontend/src/views/ExerciseHistoryView.vue`
