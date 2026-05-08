---
estimated_steps: 7
estimated_files: 7
---

# T01: Install vue-i18n and build i18n infrastructure with Settings view

**Slice:** S02 — vue-i18n infrastructure + Settings view with language toggle
**Milestone:** M003

## Description

Create the entire i18n stack from scratch: install vue-i18n v9, create the plugin module exporting the i18n instance, write English and Russian locale files with the full string inventory, build a Pinia settings store that syncs language preference to the backend, create a Settings view with a language toggle, add the `/settings` route, register the plugin in main.ts, and load the saved language in the router guard.

The critical architectural pattern: `plugins/i18n.ts` exports the i18n instance as a plain module — both `main.ts` (for `app.use()`) and `stores/settings.ts` (for `i18n.global.locale.value` mutation) import from it. No circular dependencies, no `useI18n()` in the store.

## Steps

1. `cd ../frontend && npm install vue-i18n@9` — pin to v9 for Vue 3 compatibility
2. Create `src/plugins/i18n.ts` — `createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages: { en, ru } })`, export the instance
3. Create `src/locales/en.ts` and `src/locales/ru.ts` with the full string inventory from research (nav, muscle_groups, exercises, workout, history, programs, settings namespaces)
4. Create `src/stores/settings.ts` — `useSettingsStore` with `language` ref, `loadLanguage()` (GET, catch 404 → default 'en'), `setLanguage(lang)` (PUT + set `i18n.global.locale.value`); import i18n from `@/plugins/i18n`
5. Create `src/views/SettingsView.vue` — page title, language toggle (two-button or select), show "Saved" feedback on change; use `useSettingsStore` and `useI18n()` for template `t()`
6. Add `app.use(i18n)` in `src/main.ts` (import from `@/plugins/i18n`)
7. In `src/router/index.ts` — add `/settings` route pointing to `SettingsView.vue`; in the beforeEach guard, after `fetchMe()`, `await useSettingsStore().loadLanguage()`

## Must-Haves

- [ ] vue-i18n v9 in package.json dependencies
- [ ] `plugins/i18n.ts` exports i18n instance with `legacy: false`
- [ ] Both locale files have all keys from the string inventory (nav, muscle_groups, exercises, workout, history, programs, settings)
- [ ] Settings store imports i18n instance directly (not `useI18n()`)
- [ ] `loadLanguage()` catches 404 and defaults to `'en'`
- [ ] Settings view renders with language toggle
- [ ] `/settings` route works
- [ ] `app.use(i18n)` registered in main.ts
- [ ] Language loads in router guard before first view renders

## Verification

- `cd ../frontend && npm run build` — zero errors
- Manually check: `src/plugins/i18n.ts` exports i18n with `legacy: false`
- Confirm `stores/settings.ts` does NOT import from `useI18n()` — uses `i18n.global.locale.value`

## Observability Impact

- **New signal:** `i18n.global.locale.value` — readable in devtools console; changes reactively on `setLanguage()` call
- **New signal:** `useSettingsStore().language` — Pinia state panel in Vue Devtools shows current language ref value
- **Failure visibility:** 404 from `GET /api/settings/language` is expected on first run; silently defaults to `'en'`. Any other error logs `[SettingsStore] loadLanguage error: <status>` to browser console.
- **Guard trace:** Router `beforeEach` now awaits `loadLanguage()` — if language load is slow (network), first navigation is delayed by that round-trip. No loading indicator shown; acceptable for personal app.
- **Diagnostic command:** `npm run build` — zero errors confirms TypeScript + template compilation. `npm run type-check` shows type errors without bundling.
- **Inspection:** After language switch, `GET /api/settings/language` returns `{"key":"language","value":"ru"}` confirming persistence.

## Inputs

- S02-RESEARCH.md — full string inventory for locale files
- `../frontend/src/main.ts` — current app bootstrap (add `app.use(i18n)`)
- `../frontend/src/router/index.ts` — current router guard (add language load + settings route)
- `../frontend/src/lib/apiFetch.ts` — API utility for settings store calls

## Expected Output

- `../frontend/src/plugins/i18n.ts` — i18n instance module
- `../frontend/src/locales/en.ts` — English messages
- `../frontend/src/locales/ru.ts` — Russian messages
- `../frontend/src/stores/settings.ts` — settings Pinia store
- `../frontend/src/views/SettingsView.vue` — Settings page with language toggle
- `../frontend/src/main.ts` — modified (i18n registered)
- `../frontend/src/router/index.ts` — modified (settings route + guard language load)
