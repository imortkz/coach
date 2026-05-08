# S02: vue-i18n infrastructure + Settings view with language toggle — Research

**Date:** 2026-03-14

---

## Summary

S02 wires internationalization into the frontend: install vue-i18n v9, create English and Russian locale files, add a Pinia settings store that syncs language to the backend, build a Settings view with a language toggle, and make all static UI strings switch reactively. No backend changes are needed — `PUT/GET /api/settings/language` already works via the existing key-value settings endpoint.

The frontend has zero i18n today: no vue-i18n dependency, no locale files, no settings store, no Settings view, no /settings route. App.vue has exactly 4 nav items. Every string is hardcoded in place. This slice adds the full i18n stack from scratch — install, configure, locale files, store, view, and route — then replaces hardcoded strings with `t()` calls across all affected components.

The critical architectural decision is how to share the i18n instance between the plugin (registered in main.ts) and the settings store (which needs to set `i18n.global.locale.value`). The correct pattern is to create the instance in a separate module (`src/plugins/i18n.ts`) that both main.ts and the settings store can import without circularity. The `Exercise.id: number` TypeScript bug is also fixed here — it's a zero-cost change while touching the types file, and it unblocks the `exercisesStore.find(e => e.id === exerciseId)` lookup in ExerciseHistoryView that is currently broken for UUID-based IDs.

---

## Recommendation

**Create `src/plugins/i18n.ts` as the single i18n instance export; build `useSettingsStore` that imports it directly; load language in the router guard after `fetchMe()` resolves.**

- Don't register `i18n` only in main.ts and pass it around via `provide/inject` — that adds ceremony and makes the store hard to test. Exporting the instance from its own module is the standard pattern for Pinia + vue-i18n coexistence.
- Don't use `useI18n()` inside the store to access locale — `useI18n()` requires a component setup context. Use `i18n.global.locale.value` from the imported instance directly.
- Don't load language preference on component mount or in the exercises store — load it once in the router guard, right after `fetchMe()`, so it's available before the first view renders. Wrap in try/catch and default to `'en'` on 404 (no saved preference yet).
- The 5 muscle group keys (`Chest`, `Back`, `Shoulders`, `Arms`, `Legs`, `Core`) must be in the locale file for S03 to consume — create them in S02 even if the view wiring (`t('muscle_groups.' + group.name)`) happens in S03.

---

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Vue 3 reactive i18n | `vue-i18n@9.x`, `createI18n({ legacy: false })`, `useI18n()` | Reactive locale ref; all `t()` calls update automatically on `locale.value` change; handles fallback locale |
| Language persistence | Existing `PUT/GET /api/settings/{key}` in `../backend/app/workouts/routes.py` | Already handles upsert, user scoping, 404 on missing key; `language` key works with zero backend changes |
| Pinia state for language | New `useSettingsStore` (thin — just `language` ref + `loadLanguage` + `setLanguage`) | Consistent with existing store pattern; reactive `language` ref lets S03 composable watch it |

---

## Existing Code and Patterns

- `../frontend/src/main.ts` — bootstraps app; add `app.use(i18n)` here after importing from `src/plugins/i18n.ts`; no other changes needed
- `../frontend/src/router/index.ts` — router guard calls `auth.devLogin()` then `auth.fetchMe()` then returns `true`; language load goes after `fetchMe()` resolves, before `return true`; add `/settings` route pointing to `SettingsView.vue`
- `../frontend/src/App.vue` — `navItems` array drives both desktop nav and mobile bottom tab bar; add a 5th item `{ to: '/settings', label: t('nav.settings'), icon: 'gear' }` and add a gear SVG branch in the icon template; labels should use `t()` for all 5
- `../frontend/src/stores/auth.ts` — `devLogin()` and `fetchMe()` are async; language load in router guard happens after `fetchMe()` resolves; no changes needed to auth store
- `../frontend/src/lib/apiFetch.ts` — all API calls go through this; settings store uses it for `GET/PUT /api/settings/language`; no changes needed
- `../frontend/src/types/index.ts` — `Exercise.id: number` must change to `id: string`; also add `name_ru?: string | null` and `gif_url?: string | null` here (S01 boundary product consumed by S02's type touch); `WorkoutSet.exercise_id` is a separate `number` typed field — leave it for now to avoid cascade changes beyond S02's scope
- `../frontend/src/views/ExerciseHistoryView.vue` — line 13: `const exerciseId = Number(route.params.id)` must change to `const exerciseId = route.params.id as string`; line 28: `find((e) => e.id === exerciseId)` then works because both sides are strings; line 38: URL `/api/exercises/${exerciseId}/history` works unchanged (UUID string in path)
- `../frontend/src/views/ExercisesView.vue` — `editingId` ref typed as `ref<number | null>` must change to `ref<string | null>`; `deleteExercise(id: number)` and `updateExercise(id: number, ...)` in exercises store also need the id param changed to `string`; the group header `group.name` renders English muscle group name — S02 can optionally wire `t('muscle_groups.' + group.name)` here since it's a one-liner

---

## File Inventory for S02

### New files to create
- `../frontend/src/plugins/i18n.ts` — `createI18n({ legacy: false, locale: 'en', fallbackLocale: 'en', messages: { en, ru } })`; exports `i18n` instance
- `../frontend/src/locales/en.ts` — English messages (see string inventory below)
- `../frontend/src/locales/ru.ts` — Russian messages
- `../frontend/src/stores/settings.ts` — `useSettingsStore` with `language`, `loadLanguage()`, `setLanguage()`
- `../frontend/src/views/SettingsView.vue` — language toggle UI

### Files to modify
- `../frontend/package.json` — add `vue-i18n@9` to dependencies (via `npm install`)
- `../frontend/src/main.ts` — `app.use(i18n)` import and registration
- `../frontend/src/router/index.ts` — add `/settings` route; call `settingsStore.loadLanguage()` in guard
- `../frontend/src/App.vue` — add 5th gear nav item; wrap all label strings with `t()`
- `../frontend/src/types/index.ts` — fix `Exercise.id: string`; add `name_ru`, `gif_url` optional fields
- `../frontend/src/views/ExerciseHistoryView.vue` — fix `Number(route.params.id)` → string
- `../frontend/src/stores/exercises.ts` — fix `id: number` param types in `updateExercise` and `deleteExercise`
- `../frontend/src/views/ExercisesView.vue` — fix `editingId` ref type; wire `t()` for static strings

---

## Translation String Inventory

All keys needed in both `en.ts` and `ru.ts`:

```
nav:
  exercises: "Exercises" / "Упражнения"
  programs: "Programs" / "Программы"
  workout: "Workout" / "Тренировка"
  history: "History" / "История"
  settings: "Settings" / "Настройки"

muscle_groups:
  Chest: "Chest" / "Грудь"
  Back: "Back" / "Спина"
  Shoulders: "Shoulders" / "Плечи"
  Arms: "Arms" / "Руки"
  Legs: "Legs" / "Ноги"
  Core: "Core" / "Пресс"

exercises:
  title: "Exercises" / "Упражнения"
  search_placeholder: "Search exercises..." / "Поиск упражнений..."
  all_equipment: "All Equipment" / "Всё оборудование"
  loading: "Loading exercises..." / "Загрузка упражнений..."
  try_again: "Try again" / "Попробовать снова"
  empty_title: "No exercises found." / "Упражнения не найдены."
  empty_hint: "Try adjusting your search or filters." / "Попробуйте изменить поиск или фильтры."
  add_custom_title: "Add custom exercise" / "Добавить упражнение"
  name_placeholder: "Exercise name" / "Название упражнения"
  custom_badge: "Custom" / "Своё"
  add: "Add" / "Добавить"
  save: "Save" / "Сохранить"
  cancel: "Cancel" / "Отмена"

workout:
  title: "Workout" / "Тренировка"
  loading: "Loading..." / "Загрузка..."

history:
  title: "History" / "История"
  loading: "Loading workouts..." / "Загрузка тренировок..."
  empty: "No completed workouts yet." / "Пока нет завершённых тренировок."
  empty_hint: "Start a workout from the Programs page!" / "Начните тренировку на странице программ!"

programs:
  title: "Programs" / "Программы"

settings:
  title: "Settings" / "Настройки"
  language_label: "Language" / "Язык"
  language_en: "English" / "English"
  language_ru: "Russian" / "Русский"
  language_saved: "Saved" / "Сохранено"
```

---

## Constraints

- **vue-i18n v9 only** — v9 is the Vue 3 stable target; v10 changed composition API shape. Pin to `vue-i18n@9`.
- **`legacy: false` required** — Composition API mode; `i18n.global.locale` is a `ref`, changed with `.value`. Mixing with legacy string-assign silently fails.
- **No new backend routes** — `PUT/GET /api/settings/language` already exists and handles the `language` key via the key-value pattern in workouts/routes.py.
- **Language default is `'en'`** — on 404 (no setting saved), settings store silently defaults to English. No error shown to user.
- **Settings store loads once in router guard** — not in every component's `onMounted`. Language is a global concern, not per-view.
- **`useI18n()` is component-only** — the settings store cannot call `useI18n()`. It must use `i18n.global.locale.value` from the exported instance.
- **`Exercise.id` fix is scoped** — fix `Exercise.id: string` and `ExerciseHistoryView.vue`'s cast; leave `WorkoutSet.id`, `Program.id` etc. as `number` to avoid cascade changes beyond S02's scope. Note: these other IDs likely have the same bug but are out of scope for M003.
- **`npm run build` must pass clean** — no TypeScript errors after all changes. The id type change ripples into exercises store and ExercisesView; catch them all.

---

## Common Pitfalls

- **`i18n.global.locale` as ref vs string** — With `legacy: false`, locale is a `Ref<string>`. Set it with `i18n.global.locale.value = 'ru'`, NOT `i18n.global.locale = 'ru'`. The latter silently no-ops.
- **Circular import between i18n and store** — If `plugins/i18n.ts` imports from any store, or a store imports from a file that imports from i18n before i18n is initialized, Vite's ESM evaluation order will produce `undefined`. Keep `plugins/i18n.ts` a pure module with no store imports.
- **Language race condition in router guard** — The guard is called before the first route renders. `loadLanguage()` is async (network call). The guard must `await settingsStore.loadLanguage()` — if it's not awaited, the first render may use `'en'` even when the user's preference is `'ru'`.
- **`t()` in `navItems` array** — `navItems` is defined in `<script setup>` and evaluated once at component mount. If you put `t('nav.exercises')` into a static array, it won't be reactive to locale changes. Use a `computed` property for `navItems` or call `t()` directly in the template (`{{ t('nav.exercises') }}`). Using `t()` in the template is reactive; in a static array it's not.
- **`editingId` type cascade** — Changing `Exercise.id` to `string` causes TypeScript errors in `ExercisesView.vue` where `editingId` is `ref<number | null>`. Fix the ref type to `ref<string | null>` and fix all id comparisons.
- **`deleteExercise` / `updateExercise` id parameter** — These functions in `exercises.ts` take `id: number`. Must change to `id: string` after `Exercise.id` type fix, or TypeScript will error.
- **Settings 404 is not an error** — `GET /api/settings/language` returns 404 if the user has never set a language. The store's `loadLanguage()` must catch 404 and silently use `'en'`; only 5xx or network errors are real failures.
- **`fallbackLocale: 'en'` in createI18n** — Set this so any key missing from `ru.ts` falls back to English instead of showing the raw key string.

---

## Open Risks

- **TypeScript type ripple from `id: string`** — The ExercisesView and exercises store use `id: number` in multiple places. Touching `types/index.ts` will surface all of them as TS errors. This is desirable (catch them all at compile time) but requires fixing every site in the same task. Run `npm run type-check` after the fix to catch stragglers before committing.
- **Other `id: number` types in types/index.ts** — `ProgramSet.id`, `Program.id`, `ProgramExercise.id`, `Workout.id`, `WorkoutSet.id` are all `number` but almost certainly UUID strings at runtime. S02 fixes only `Exercise.id`. The others could be silent bugs that surface if any view does numeric arithmetic or strict equality with these IDs. Flag in S02 summary as known tech debt.
- **`$t()` in Options API components** — All existing components use `<script setup>` (Composition API). `$t()` (template helper) works in both modes when `legacy: false` is set... actually with `legacy: false`, the `$t()` global property is NOT available. Use `const { t } = useI18n()` in each component setup. Confirm this — docs show $t is available in legacy mode but template `{{ $t(...) }}` should still work with legacy:false via the global composer. Test one component to verify before mass-changing.
  - **Confirmed safe pattern**: In `legacy: false` mode, `$t()` IS still available as a component template helper (injected globally by the plugin). `useI18n()` in `<script setup>` returns `{ t }` for script use. Both work; `$t()` in templates is fine without needing `useI18n()` in every component's setup.

---

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| vue-i18n | (standard library, docs sufficient) | none found |

---

## Sources

- vue-i18n v9 `legacy: false` composition API setup: `createI18n({ legacy: false, locale: 'en', messages: { en, ru } })` (Context7: /intlify/vue-i18n)
- `i18n.global.locale.value = 'ru'` for programmatic locale change with `legacy: false` (Context7: /intlify/vue-i18n — scope.md)
- Backend settings endpoint confirmed: `GET/PUT /api/settings/{key}` at lines 442–480 of `../backend/app/workouts/routes.py`; returns 404 when key not found
- `Exercise.id` UUID bug confirmed: `types/index.ts` line 2 declares `id: number`; `ExerciseHistoryView.vue` line 13 does `Number(route.params.id)` producing `NaN` for UUID strings
- Muscle groups confirmed as 6 English strings: Arms, Back, Chest, Core, Legs, Shoulders (from `../backend/app/seed.py`)
- `$t()` availability in `legacy: false` mode: confirmed globally injected by vue-i18n plugin; safe to use in templates without `useI18n()` in each component
