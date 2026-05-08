---
id: T01
parent: S02
milestone: M003
provides:
  - vue-i18n v9 plugin registered in main.ts
  - English and Russian locale files with full string inventory
  - useSettingsStore Pinia store syncing language to backend
  - SettingsView with language toggle
  - /settings route in router
  - Language loaded in router guard before first render
key_files:
  - ../frontend/src/plugins/i18n.ts
  - ../frontend/src/locales/en.ts
  - ../frontend/src/locales/ru.ts
  - ../frontend/src/stores/settings.ts
  - ../frontend/src/views/SettingsView.vue
  - ../frontend/src/main.ts
  - ../frontend/src/router/index.ts
key_decisions:
  - i18n instance exported from plugins/i18n.ts as plain module; both main.ts and settings store import it (no circular deps, no useI18n() in store)
  - loadLanguage() catches 404 silently and defaults to 'en'; any other error logs to console
  - Language loaded once in router beforeEach guard after fetchMe(); not in component onMounted
patterns_established:
  - Store accessing i18n locale via i18n.global.locale.value (not useI18n()) — safe outside component context
  - Router guard pattern: devLogin → fetchMe → loadLanguage → return true
observability_surfaces:
  - i18n.global.locale.value readable in browser devtools console
  - useSettingsStore().language inspectable in Vue Devtools Pinia panel
  - GET /api/settings/language returns {"key":"language","value":"ru"} confirming persistence
  - Console logs [SettingsStore] errors on non-404 failures
duration: ~25m
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T01: Install vue-i18n and build i18n infrastructure with Settings view

**vue-i18n v9 infrastructure fully wired: plugin, locale files, settings store, Settings view, route, and router guard language load — all verified with zero build errors and live browser persistence test.**

## What Happened

Executed all 7 steps in order:

1. `npm install vue-i18n@9` — installed v9.14.5 (deprecation warning expected; v9 pinned per constraint)
2. Created `src/plugins/i18n.ts` exporting `createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages: { en, ru } })`
3. Created `src/locales/en.ts` and `src/locales/ru.ts` with all 7 namespaces: nav, muscle_groups, exercises, workout, history, programs, settings
4. Created `src/stores/settings.ts` — `useSettingsStore` with `loadLanguage()` (404-safe) and `setLanguage()` (PUT + `i18n.global.locale.value` mutation); imports i18n instance directly, no `useI18n()`
5. Created `src/views/SettingsView.vue` — Settings page title, Language label, English/Russian two-button toggle with blue active border, "Saved"/"Сохранено" 2s feedback on change
6. Updated `src/main.ts` — added `app.use(i18n)` after pinia, before router
7. Updated `src/router/index.ts` — added `/settings` route; added `await settingsStore.loadLanguage()` in `beforeEach` guard after `fetchMe()`

## Verification

- `npm run build` — zero TypeScript and template compilation errors (109 modules, 1.46s)
- Architectural: `stores/settings.ts` uses `i18n.global.locale.value` only — confirmed via grep, no `useI18n()` import
- `plugins/i18n.ts` — confirmed `legacy: false` in createI18n options
- Browser: navigated to `/settings` — renders with "Settings" heading, Language toggle showing English selected
- Browser: clicked "Russian" — heading instantly changed to "Настройки", label to "Язык", button to "Русский" (selected), "Сохранено" feedback shown
- Backend: `GET /api/settings/language` returned `{"key":"language","value":"ru"}` — PUT persisted correctly
- Browser: refreshed `/settings` — Russian still selected (loaded from backend in router guard before render)
- Browser assertions: 4/4 PASS (url, Настройки visible, Язык visible, Русский visible)

## Diagnostics

- `i18n.global.locale.value` — readable in browser devtools console at any time
- Vue Devtools Pinia panel — `settings` store shows `language` ref current value
- `GET /api/settings/language` with auth token — confirms backend-persisted language
- Console error pattern: `[SettingsStore] loadLanguage error: <status>` for non-404 failures; `[SettingsStore] setLanguage error:` for PUT failures
- 404 on `GET /api/settings/language` is expected on first use (no preference saved) — silently defaults to `'en'`

## Deviations

None. Implemented exactly as planned.

## Known Issues

- vue-i18n v9 shows deprecation warning (`v9 no longer supported`). Per constraints, v9 is pinned for Vue 3 Composition API compatibility. Migration to v11 is out of scope for M003.
- Nav labels in App.vue are still hardcoded English strings — not using `$t()` yet. This is intentional: T02 wires `t()` into App.vue and all views.
- Settings nav tab (gear icon) not yet added to App.vue nav — also T02's responsibility.
- `Exercise.id: number` TypeScript bug not yet fixed — T02 scope.

## Files Created/Modified

- `../frontend/src/plugins/i18n.ts` — new: i18n instance module (legacy: false, en/ru messages)
- `../frontend/src/locales/en.ts` — new: English messages (7 namespaces, 30 keys)
- `../frontend/src/locales/ru.ts` — new: Russian messages (7 namespaces, 30 keys)
- `../frontend/src/stores/settings.ts` — new: useSettingsStore with loadLanguage + setLanguage
- `../frontend/src/views/SettingsView.vue` — new: Settings page with language toggle
- `../frontend/src/main.ts` — modified: added app.use(i18n)
- `../frontend/src/router/index.ts` — modified: /settings route + loadLanguage in guard
