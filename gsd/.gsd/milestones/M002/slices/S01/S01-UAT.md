# S01: Fix swipe actions and add template set skipping — UAT

**Milestone:** M002
**Written:** 2026-03-14

## UAT Type

- UAT mode: live-runtime
- Why this mode is sufficient: All changes are swipe interaction behaviours in the active workout view — no API contracts changed, no tests apply. Browser verification against the running dev server is the only meaningful signal.

## Preconditions

1. Backend running: `cd ../backend && uv run uvicorn app.main:app --reload`
2. Frontend dev server running: `cd ../frontend && npm run dev` (localhost:5173)
3. Dev mode enabled (DEV_MODE=true in backend .env) — auto-login active
4. At least one program exists with multiple sets per exercise (use seed data or create one)
5. Start an active workout from a program

## Smoke Test

Swipe left on any set row in the active workout view — the swipe action panel should appear with a Delete button visible.

## Test Cases

### 1. Edit button hidden on unlogged extra set

1. In an active workout, tap "Add Set" on any exercise to create an extra set (unlogged, extra)
2. Swipe left on the newly added extra set row
3. **Expected:** Action panel appears with only a Delete button. No Edit button visible.

### 2. Edit button visible on logged set

1. Log a set (enter reps and weight, tap the checkmark)
2. Swipe left on the now-logged set row
3. **Expected:** Action panel appears with both Edit and Delete buttons visible.

### 3. Swipe works on unlogged template set

1. Find an unlogged template set row (a set from the program that has not been logged yet)
2. Swipe left on it
3. **Expected:** Action panel appears with a Delete button. No Edit button visible.

### 4. Tapping Delete on unlogged template set hides the row and shows undo toast

1. Swipe left on an unlogged template set row
2. Tap Delete
3. **Expected:** The set row disappears from the exercise card. An undo toast appears at the bottom of the screen with message "Set skipped" and an Undo button.

### 5. Tapping Undo restores the skipped template set

1. After completing test case 4, tap Undo on the toast before it dismisses
2. **Expected:** The skipped set row reappears in the exercise card in its original position.

### 6. Skipped sets do not persist to next workout

1. Skip one or more template sets during a workout (let the undo toast expire without tapping Undo)
2. Complete or discard the workout
3. Start a new workout from the same program
4. **Expected:** All template sets are present — previously skipped sets reappear. No sets are missing.

## Edge Cases

### Toast auto-dismiss without Undo

1. Skip a template set
2. Wait for the undo toast to auto-dismiss (7 seconds) without tapping Undo
3. **Expected:** The set row remains hidden for this workout session. No error thrown.

### Skipping all sets on an exercise

1. Skip every template set on a given exercise (swipe + Delete on each)
2. **Expected:** The exercise card shows no set rows (empty state, or just the exercise header). No crash or error.

### Undo after skipping multiple sets

1. Skip two template sets in quick succession
2. Tap Undo on the most recent toast
3. **Expected:** The most recently skipped set is restored. The earlier skipped set remains hidden (each toast controls its own set).

## Failure Signals

- Edit button appears on an unlogged set row → T01 guard not applied
- Swiping an unlogged template set does nothing (no panel appears) → T02 swipe guard not removed
- Tapping Delete on a template set fires a backend API call → T03 no-op delete path bypassed
- Row remains visible after Delete tap → T03 skippedTemplateSets filter not working
- Undo does not restore the row → T03 restore callback not removing key from Set
- Starting a new workout is missing sets → skippedTemplateSets not cleared on unmount

## Requirements Proved By This UAT

- none (bug fixes / UX gaps — no formal requirements tracked)

## Not Proven By This UAT

- That program data in MongoDB is unmodified after skip (no backend API call is made, but direct DB inspection would be the definitive proof)
- Behaviour under poor network / server-down conditions (not relevant since skip is client-only)

## Notes for Tester

- Extra sets are created via the "Add Set" button at the bottom of each exercise card.
- Template sets are the sets shown before any have been logged — they appear at the start of a fresh workout.
- The undo toast timeout is 7 seconds — act quickly when testing the Undo case.
- Vue DevTools can be used to inspect `skippedTemplateSets` on the ActiveWorkout component to verify Set contents during testing.
