# M007: Localization Coverage Completion — Roadmap

**Status:** Active — implementation in progress (2026-05-08).

Implementation plan for `M007-CONTEXT.md`. Five slices, frontend-only,
no backend changes. Each slice ends with `npm run type-check` +
`npm run build` + `npm run check:no-raw-fetch` clean.

## S01 — Locale keys

Extend `frontend/src/locales/en.ts` and `frontend/src/locales/ru.ts`
with the keys for every string surfaced by the six affected files.
Group by namespace following the existing structure:

- `programs.*` — list page, edit page, validation messages, delete
  confirmation, common labels (Edit / Delete / Cancel / New / Save).
- `workout.*` — picker title and subtitle, loading states for
  programs and exercises, empty-state messages.
- `summary.*` — new namespace for `WorkoutSummary` (title, stats
  labels, action buttons).
- `programs.exercise_count`, `programs.set_count`, `summary.*_count`
  use `vue-i18n` pluralization. Russian needs three forms
  (1 / 2–4 / many), English needs two.

Verification: type-check still clean (locale files don't fail TS),
no consumer changes yet.

## S02 — `ProgramEditView` refactor + i18n

Two changes here:

- Switch `BuilderExercise.exercise_name: string` to carry the
  full `Exercise` reference (`exercise: Exercise`) so `displayName`
  is reactive on language change. Update `addExercise` (push
  `{ exercise, sets }`) and the edit-mode hydration path
  (`pe.exercise` already on the wire). In the template, replace
  `{{ ex.exercise_name }}` with `{{ displayName(ex.exercise) }}`
  and `ex.exercise_id` with `ex.exercise.id` everywhere it's
  referenced. Keep payload-build path consuming `ex.exercise.id`.
- All hardcoded English (header, validation messages, buttons,
  set-row labels, picker placeholder) routed through `t(...)`.
  `validate()` becomes `validate(t)` since validation strings
  must come from the i18n instance, or returns an i18n key path
  which the caller translates.
- The exercise-picker rows render `displayName(ex)` instead of
  `ex.name`, so search results follow the language toggle.

Verification: type-check + build clean. Manual read-through
confirms every string in the file goes through `t(...)`.

## S03 — `ProgramsView`

- All hardcoded text → `t(...)`.
- `confirm(...)` text comes from `t('programs.delete_confirm',
  { name })` — native dialog chrome stays OS-localized but the
  message body is translated.
- The exercise-count line uses pluralized
  `t('programs.exercise_count', n, { count: n })`.

## S04 — `ProgramPicker` + `WorkoutSummary` + `ActiveWorkout`

Mostly mechanical i18n routing. Three small files, parallel work.

- `ProgramPicker`: title, subtitle, loading state, empty state,
  exercise/set count pluralization.
- `WorkoutSummary`: header, stat labels (Duration / Exercise(s) /
  Set(s) / Volume), Keep Going / Finish buttons.
- `ActiveWorkout`: single string — the loading state.

## S05 — Verification & docs

- Browser-style read-through (manual diff against M007-CONTEXT
  acceptance list).
- Run all CI guards: `type-check`, `build`, `check:no-raw-fetch`.
- Append `M007-SUMMARY.md` in the M001–M005 style: surfaces
  covered, key count delta, the `Exercise`-reference refactor
  note, links to the PR.

## Out of scope

Per `M007-CONTEXT.md` already-named exclusions. Plus: any string
outside the six files (`history`, `settings`, `report`, `nav`,
`muscle_groups` are already localized in M003); any backend
changes; any new view scaffolding.

## Risks

- Pluralization keys must be referenced via `vue-i18n` plural
  API (`t('key', count)` with the legacy-false setup). If a
  consumer accidentally passes a count via interpolation only
  (`t('key', { count: n })`) the plural form won't pick correctly
  — verify on every use.
- `ProgramEditView`'s payload build (`buildPayload`) currently
  reads `ex.exercise_id` — after refactor it must read
  `ex.exercise.id`. Easy to miss; covered by type-check because
  `BuilderExercise` shape changes.
- Native `confirm(...)` returns a localized OK/Cancel from the
  browser regardless of our `t(...)` text. Acceptable per
  `M007-CONTEXT.md`.
