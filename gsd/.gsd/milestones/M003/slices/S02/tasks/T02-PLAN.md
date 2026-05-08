---
estimated_steps: 5
estimated_files: 5
---

# T02: Wire $t() into App.vue and views, fix Exercise.id type to string

**Slice:** S02 — vue-i18n infrastructure + Settings view with language toggle
**Milestone:** M003

## Description

Replace all hardcoded UI strings in App.vue, ExercisesView, and ExerciseHistoryView with `$t()` calls so they react to locale changes. Add the 5th gear nav item to App.vue for the Settings tab. Fix `Exercise.id` from `number` to `string` in the TypeScript type and chase the ripple through exercises store and views.

## Steps

1. In `src/types/index.ts` — change `Exercise.id: number` to `id: string`; add `name_ru?: string | null` and `gif_url?: string | null` fields
2. In `src/stores/exercises.ts` — change `id: number` param to `id: string` in `updateExercise()` and `deleteExercise()`
3. In `src/App.vue` — add 5th nav item `{ to: '/settings', label: 'settings', icon: 'gear' }`; use `$t('nav.' + item.label)` in template instead of `item.label` directly (so labels are reactive); add gear SVG icon branch
4. In `src/views/ExercisesView.vue` — change `editingId` from `ref<number | null>` to `ref<string | null>`; replace hardcoded strings (title "Exercises", placeholder "Search exercises...", "All Equipment", loading/error/empty text, button labels) with `$t()` calls
5. In `src/views/ExerciseHistoryView.vue` — change `const exerciseId = Number(route.params.id)` to `const exerciseId = route.params.id as string`; replace hardcoded strings with `$t()` calls

## Must-Haves

- [ ] `Exercise.id` is `string` in types/index.ts
- [ ] `Exercise` type has `name_ru` and `gif_url` optional fields
- [ ] `updateExercise` and `deleteExercise` take `id: string`
- [ ] `editingId` ref is `string | null`
- [ ] `exerciseId` in ExerciseHistoryView is string (no `Number()` cast)
- [ ] All nav labels in App.vue use `$t()`
- [ ] Gear icon and Settings nav item present
- [ ] Hardcoded strings in ExercisesView replaced with `$t()`
- [ ] `npm run build` passes with zero errors

## Verification

- `cd ../frontend && npm run build` — zero TypeScript errors, zero template compilation errors
- Grep for remaining hardcoded strings: `grep -n "Loading exercises\|Search exercises\|All Equipment\|No exercises found\|Try again" ../frontend/src/views/ExercisesView.vue` should return zero matches

## Inputs

- T01 output: vue-i18n registered, locale files with all keys, `$t()` globally available
- `../frontend/src/types/index.ts` — current Exercise type with `id: number`
- `../frontend/src/stores/exercises.ts` — `updateExercise(id: number)`, `deleteExercise(id: number)`
- `../frontend/src/App.vue` — 4 nav items, hardcoded labels
- `../frontend/src/views/ExercisesView.vue` — `editingId: ref<number | null>`, hardcoded strings
- `../frontend/src/views/ExerciseHistoryView.vue` — `Number(route.params.id)`, hardcoded strings

## Expected Output

- `../frontend/src/types/index.ts` — `Exercise.id: string`, `name_ru`, `gif_url` added
- `../frontend/src/stores/exercises.ts` — id params changed to `string`
- `../frontend/src/App.vue` — 5 nav items with `$t()` labels, gear icon
- `../frontend/src/views/ExercisesView.vue` — `$t()` strings, `editingId: ref<string | null>`
- `../frontend/src/views/ExerciseHistoryView.vue` — string exerciseId, `$t()` strings

## Observability Impact

**Signals that change after this task:**
- Nav labels in App.vue are now reactive to locale changes — toggling language in Settings immediately updates all 5 nav tab labels (both desktop navbar and mobile tab bar)
- Exercises page title, search placeholder, equipment filter label, loading/error/empty states, button labels all switch reactively on locale toggle
- ExerciseHistoryView loading/error strings switch reactively

**How a future agent inspects this task:**
- `i18n.global.locale.value` in browser devtools console — current locale; toggle to 'ru' and observe nav labels update
- Vue Devtools component inspector → App.vue → `navItems` — verify 5 items present; `t('nav.settings')` resolves to 'Settings'/'Настройки' per locale
- `grep -r '\$t\|useI18n' ../frontend/src/views/ExercisesView.vue ../frontend/src/views/ExerciseHistoryView.vue ../frontend/src/App.vue` — confirms i18n is wired
- TypeScript: `Exercise.id` type change is compiler-enforced — any downstream code treating id as `number` will fail `npm run build`

**Failure state:**
- If locale strings are missing for a key, vue-i18n falls back to key name (e.g. renders `exercises.title` instead of "Exercises") — visible in the browser as raw key strings
- Build errors manifest as TypeScript type mismatch if any caller passes `number` to `updateExercise`/`deleteExercise`
- `npm run build` is the gate — zero errors confirms all type ripples resolved
