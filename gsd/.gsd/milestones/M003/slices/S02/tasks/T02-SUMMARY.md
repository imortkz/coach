---
id: T02
parent: S02
milestone: M003
provides:
  - Exercise.id typed as string (compiler-enforced) with name_ru and gif_url optional fields
  - $t() reactive strings in App.vue, ExercisesView, ExerciseHistoryView
  - 5th gear/Settings nav item in App.vue (desktop + mobile)
  - editingId ref typed as string | null in ExercisesView
  - exerciseId in ExerciseHistoryView as string (no Number() cast)
key_files:
  - ../frontend/src/types/index.ts
  - ../frontend/src/stores/exercises.ts
  - ../frontend/src/App.vue
  - ../frontend/src/views/ExercisesView.vue
  - ../frontend/src/views/ExerciseHistoryView.vue
key_decisions:
  - App.vue uses useI18n() composable (t function) rather than global $t in script block — consistent with component-level i18n pattern
  - ExercisesView and ExerciseHistoryView both use useI18n() composable pattern
  - navItems label keys changed from display strings ('Exercises') to i18n keys ('exercises') — $t('nav.' + item.label) resolves to locale string
patterns_established:
  - useI18n() composable in script setup for reactive t() calls in Vue 3 components
  - navItems use i18n key names (not display strings) — $t('nav.' + item.label) pattern
observability_surfaces:
  - i18n.global.locale.value in browser devtools console — shows current locale
  - grep -r 'useI18n' ../frontend/src/views/ExercisesView.vue — confirms i18n wired
  - npm run build — TypeScript enforces Exercise.id as string; any number cast fails compilation
duration: ~10 min
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T02: Wire $t() into App.vue and views, fix Exercise.id type to string

**Replaced all hardcoded UI strings with reactive $t() calls in App.vue, ExercisesView, and ExerciseHistoryView; fixed Exercise.id to string type with compiler-enforced ripple through store and views; added Settings gear nav item.**

## What Happened

1. **types/index.ts** — `Exercise.id: number` → `id: string`; added `name_ru?: string | null` and `gif_url?: string | null` optional fields.
2. **stores/exercises.ts** — `updateExercise(id: number)` and `deleteExercise(id: number)` params changed to `id: string` to match type.
3. **App.vue** — Added 5th nav item `{ to: '/settings', label: 'settings', icon: 'gear' }`. Changed `item.label` display to `t('nav.' + item.label)` in both desktop navbar and mobile tab bar. Added gear SVG icon branch. Switched from `$t()` global to `useI18n()` composable in script setup.
4. **ExercisesView.vue** — `editingId` ref changed from `ref<number | null>` to `ref<string | null>`. Replaced all hardcoded strings (title, search placeholder, all equipment option, loading text, try again button, empty state, add_custom_title, name placeholder, custom badge, add/save/cancel button labels) with `t()` calls. Removed unused `watch` import.
5. **ExerciseHistoryView.vue** — `exerciseId = Number(route.params.id)` → `route.params.id as string`. Replaced "Loading history..." and "Try again" with `t()` calls. Added `useI18n()` import.

## Verification

- `cd ../frontend && npm run build` — ✅ Zero TypeScript errors, zero template compilation errors (109 modules transformed, built in 2.54s)
- `grep -n "Loading exercises\|Search exercises\|All Equipment\|No exercises found\|Try again" ../frontend/src/views/ExercisesView.vue` — ✅ Zero matches (exit code 1 = no matches)

## Diagnostics

- **Locale reactivity:** Toggle `i18n.global.locale.value = 'ru'` in browser devtools → all 5 nav labels, Exercises page title, filters, and buttons switch to Russian immediately
- **Type enforcement:** Any code passing a `number` to `updateExercise`/`deleteExercise` or comparing `Exercise.id` to a number fails `npm run build` with TypeScript error
- **Missing i18n key:** Vue-i18n falls back to raw key string (e.g. `exercises.title`) if a key is absent from locale file — visible in browser, no crash

## Deviations

- Used `useI18n()` composable (import + `const { t } = useI18n()`) rather than template-only `$t()` — this is the correct Vue 3 Composition API pattern and works equivalently in templates

## Known Issues

None.

## Files Created/Modified

- `../frontend/src/types/index.ts` — Exercise.id: string, added name_ru and gif_url optional fields
- `../frontend/src/stores/exercises.ts` — updateExercise and deleteExercise id params changed to string
- `../frontend/src/App.vue` — 5 nav items, gear icon, $t() labels via useI18n()
- `../frontend/src/views/ExercisesView.vue` — editingId: string | null, all hardcoded strings replaced with t()
- `../frontend/src/views/ExerciseHistoryView.vue` — exerciseId as string, loading/error strings via t()
- `.gsd/milestones/M003/slices/S02/tasks/T02-PLAN.md` — Added Observability Impact section (pre-flight fix)
