# M007: Localization Coverage Completion — Context

**Gathered:** 2026-03-14
**Status:** Queued — pending auto-mode execution.

## Project Description

GymCoach is a personal gym training companion with EN/RU language support added in M003. The `useDisplayName` composable and vue-i18n locale files were introduced in M003, but coverage was incomplete — several views and components still display hardcoded English text or use `exercise.name` directly instead of `displayName(exercise)`.

## Why This Milestone

M003 wired localization to 4 surfaces (ExercisesView, ExerciseCard, ExerciseHistoryView, WorkoutCard) but missed the following:

1. **Program editor (`ProgramEditView.vue`)** — exercise names in the added-exercises list render from `exercise_name` which is populated with `ex.name` (English only). The exercise picker panel also uses `ex.name` directly. `useDisplayName` is not imported here.
2. **Program list (`ProgramsView.vue`)** — "Loading programs…" and the delete confirmation dialog (`confirm(...)`) are hardcoded English strings with no translation keys.
3. **Workout view / Program picker (`ProgramPicker.vue`)** — "Loading programs…" and the pluralized exercise count label are hardcoded.
4. **Workout summary modal (`WorkoutSummary.vue`)** — "Exercise/Exercises" label is hardcoded English.
5. **Active workout (`ActiveWorkout.vue`)** — "Loading exercises…" loading state is hardcoded.
6. **Locale file gaps** — `en.ts` / `ru.ts` have no keys for: program editor labels (New Program, Edit Program, Save Program, Saving…, Add at least one exercise, Program name is required, etc.), program list labels, workout picker labels, workout summary labels, history filter label.

This is a direct continuation of M003 scope that shipped incomplete. No new architecture is needed — the composable and locale infrastructure are already in place.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Switch to Russian and see Russian text throughout the entire app — program editor, program list, workout picker, workout summary, active workout loading states
- See Russian exercise names in the program editor's exercise list and exercise picker search results
- See all button labels, confirmation dialogs, validation messages, and loading states in the selected language

### Entry point / environment

- Entry point: http://localhost:5173 — Settings → Russian → navigate to Programs, create/edit a program, start a workout, view workout summary
- Environment: browser (mobile-first)
- Live dependencies involved: none beyond the running dev server

## Completion Class

- Contract complete means: `npm run build` exits 0; no untranslated hardcoded English strings remain in the 6 affected files
- Integration complete means: browser walkthrough with Russian selected — program editor, program picker, workout summary, program list all render Russian text
- Operational complete means: none

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Language set to Russian → open program editor → exercise names in the exercise list and exercise picker show Russian names
- Language set to Russian → "Новая программа" / "Редактировать программу" appears in program editor header; "Сохранить программу" on the save button
- Language set to Russian → ProgramsView loading state and delete confirmation text appear in Russian
- Language set to Russian → ProgramPicker loading state and exercise count label appear in Russian
- Language set to Russian → WorkoutSummary exercise count label appears in Russian
- Language set to Russian → ActiveWorkout "Loading exercises…" state appears in Russian
- `npm run build` exits 0; no TypeScript errors

## Risks and Unknowns

- **`exercise_name` field in ProgramEditView** — This is a local computed field (string, not `Exercise` object) populated at construction time from `ex.name`. Simply swapping to `displayName(ex)` at construction time won't be reactive to language changes mid-session. The fix requires either: (a) storing the `Exercise` object reference instead of just the name string, then calling `displayName` in the template; or (b) recomputing `exercise_name` whenever language changes. Option (a) is cleaner — the local exercise list already carries the full `Exercise` object from the picker, so keeping a reference is straightforward. This is the main implementation decision to make in planning.
- **Pluralization in Russian** — Russian has 3 plural forms (1, 2–4, many). The "N упражнение/упражнения/упражнений" pattern in ProgramPicker and ProgramsView needs correct Russian pluralization. vue-i18n supports plural rules via `$tc` / `t('key', count)` with `|`-separated forms. The locale entry needs all 3 forms: `'{n} упражнение | {n} упражнения | {n} упражнений'`.
- **`confirm()` dialog localization** — Native browser `confirm()` in ProgramsView cannot be styled or translated directly (it renders OS chrome). Options: (a) pass a translated string via `t(...)` — the dialog text is Russian even if the buttons are OS-localized; (b) replace with a custom modal. Option (a) is zero-effort and acceptable for a personal tool.
- **Validation messages** — "Program name is required." and "Add at least one exercise." in `validate()` are returned as plain strings. These need to become `t(...)` calls, which requires `useI18n()` inside the setup function — already the pattern in other views.

## Existing Codebase / Prior Art

- `../frontend/src/composables/useDisplayName.ts` — `displayName(exercise)` returns `exercise.name_ru` if language is Russian and available, else `exercise.name`; already used in 4 views
- `../frontend/src/locales/en.ts` and `../frontend/src/locales/ru.ts` — existing locale files; need ~30 new keys added covering the 6 affected surfaces
- `../frontend/src/views/ProgramEditView.vue` — main gap; uses `exercise_name: ex.name` at line 61 and `ex.name` in template at line 368; `useDisplayName` not imported
- `../frontend/src/views/ProgramsView.vue` — hardcoded "Loading programs…" (line 46) and `confirm(...)` string (line 20)
- `../frontend/src/components/workout/ProgramPicker.vue` — hardcoded "Loading programs…" (line 29) and exercise count pluralization (line 51)
- `../frontend/src/components/workout/WorkoutSummary.vue` — hardcoded "Exercise/Exercises" label (line 70)
- `../frontend/src/components/workout/ActiveWorkout.vue` — hardcoded "Loading exercises…" (line 356)

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

Directly continues M003 scope. No new requirements — this closes the coverage gap left by M003.

## Scope

### In Scope

- `ProgramEditView.vue`: import `useDisplayName`; store `Exercise` object reference in local exercise list instead of just `exercise_name` string; use `displayName(ex)` in template and exercise picker search; use `t()` for all static labels, button text, and validation messages
- `ProgramsView.vue`: use `t()` for loading state and delete confirmation string
- `ProgramPicker.vue`: use `t()` for loading state and exercise count with Russian pluralization (`t('programs.exercise_count', n)`)
- `WorkoutSummary.vue`: use `t()` for exercise count label with Russian pluralization
- `ActiveWorkout.vue`: use `t()` for loading state
- `en.ts` / `ru.ts`: add all missing translation keys for the 6 affected surfaces (~30 new keys), including 3-form Russian plurals where needed
- `WorkoutCard.vue`: verify `exercise.name` fallback path at line 72 also uses `displayName` (currently partially wired — confirm and fix if needed)

### Out of Scope / Non-Goals

- Translating user-entered data (program names, custom exercise names)
- Replacing native `confirm()` with a custom modal — passing a translated string is sufficient
- Any backend changes
- Adding more languages beyond EN/RU
- Translating error messages returned from the backend API (FastAPI 422/404 detail strings)

## Technical Constraints

- Frontend only — `../frontend/src/` is the only target
- Must use existing `useDisplayName` composable — no new translation mechanism
- Russian pluralization via vue-i18n built-in plural syntax: `'1 упражнение | {n} упражнения | {n} упражнений'` with `t('key', n)`
- `useI18n()` composable must be called inside `setup()` — already the pattern in other views; no global `$t` usage
- `npm run build` must exit 0 after all changes

## Integration Points

- `useDisplayName` composable → `ProgramEditView` and `ProgramPicker` — same import pattern as existing wired views
- `useI18n` → all 6 files for static string translation — already imported in ExercisesView, ExerciseHistoryView, etc.
- `en.ts` / `ru.ts` → consumed by all components via `t()` calls — adding keys is backward-compatible (missing keys fall back to key name, not a crash)

## Open Questions

- None — root cause is fully understood from codebase inspection. Implementation approach is clear.
