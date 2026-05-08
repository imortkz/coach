# Phase 3: Workout Logging - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

The critical gym screen: start a workout from a program template, log each set with actual weight and reps (pre-filled from last session), edit/delete any logged set, exercise entry, or entire workout, and track rest between sets with a configurable timer. Covers LOG-01, LOG-02, LOG-03, LOG-04. History views and progression suggestions are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Workout flow
- Landing on /workout shows a program picker — tap a program to start a session with its exercises pre-loaded
- Active workout shows a scrollable list of all exercises with their sets — user can jump to any exercise and log sets in any order
- Workout state auto-saves to the server as sets are logged — returning to /workout resumes the active session (survives browser close)
- Explicit "Finish Workout" button — tapping it shows a quick summary (exercises done, total sets, duration) before confirming to save and set completed_at

### Set logging UX
- Tap-to-complete interaction: each set row shows pre-filled weight/reps — tap the row or a checkmark to log it as-is; tap weight/reps fields to edit before completing
- Pre-fill values from last session's actuals for this exercise (most recent completed workout with that exercise_id). If no prior session exists, fall back to program targets
- Warmup sets shown with a subtle "W" badge and lighter text/background — clearly secondary but still loggable
- "+Add Set" button below the last set for each exercise — allows adding extra sets beyond program definition during a workout

### Rest timer
- Floating countdown bar positioned above the mobile tab bar — always visible while scrolling through exercises
- Auto-starts after logging a set
- Default duration: 120 seconds, stored in settings table (user-configurable)
- Per-program option to disable the rest timer entirely
- Browser notification when rest period completes (requires notification permission)
- Skip button on the floating bar to dismiss/end rest early

### Edit and delete
- Editing a logged set: tap the set row on desktop, swipe left on mobile to reveal edit/delete actions — adaptive interaction based on viewport
- Deleting a single logged set: delete immediately, show bottom undo toast (5-10s timeout) before permanent deletion
- Removing an exercise from active workout: swipe or menu action on exercise header, confirmation required, removes exercise and all its logged sets
- Discarding entire workout: button in workout header (desktop) or right swipe (mobile), with bottom undo toast (5-10s timeout) before permanent deletion — catches accidental discards

### Claude's Discretion
- Exact layout spacing, typography, and color within the minimal aesthetic (Linear/Notion style from Phase 2)
- Loading states and empty states for the workout screen
- Program picker UI design (card list, simple list, etc.)
- Summary screen layout and content details
- How the undo toast looks and animates
- Notification permission request flow
- How per-program timer disable is exposed in the UI (this may touch Program model — Claude can decide if it's a settings-level or program-level flag)

</decisions>

<specifics>
## Specific Ideas

- Tap-to-complete is optimized for gym use — gloves on, minimal taps to log a set
- Undo toast pattern used consistently for all destructive actions (set delete, exercise remove, workout discard) — same visual treatment
- Rest timer disable is per-program because some workouts (e.g., circuits) don't need rest tracking
- Browser notifications chosen over sound because gym environments are noisy

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Workout` and `WorkoutSet` models already exist in backend (app/workouts/models.py) with proper FK relationships — no schema migration needed for core logging
- `Setting` model (key-value) exists for user preferences — rest_timer_seconds can be stored here
- `WorkoutRead` and `WorkoutSetRead` Pydantic schemas exist but need expansion (missing nested sets, exercise info)
- Frontend types already defined: `Workout`, `WorkoutSet` interfaces in types/index.ts
- `useProgramsStore` pattern (Pinia composition API, fetch + re-fetch) can be replicated for a `useWorkoutsStore`
- `ProgramSet` has target_reps/target_weight_kg/is_warmup — source for pre-fill fallback values

### Established Patterns
- Backend: domain-grouped layout (app/workouts/ already has models.py, schemas.py — needs routes.py)
- Backend: `selectinload` for eager loading nested relationships (used in programs routes)
- Backend: synchronous `def` endpoints, no async
- Frontend: Pinia stores with loading/error refs, mutation then re-fetch pattern
- Frontend: Tailwind CSS v4, lazy-loaded routes, adaptive nav (desktop top bar, mobile bottom tabs)
- Frontend: SVG icons inline (no icon library)

### Integration Points
- Vue Router: /workout route exists pointing to stub WorkoutView.vue
- Backend: app/workouts/__init__.py exists but no router registered in main.py yet
- Program data available via GET /api/programs — needed for program picker and pre-loading exercises
- workout_sets.exercise_id FK to exercises table — need exercise names for display
- settings table for rest_timer_seconds default

</code_context>

<deferred>
## Deferred Ideas

- Per-program rest timer duration (different rest times for different programs) — keep simple with global default for now, per-program is a future enhancement
- Add exercises to a workout that aren't in the program (ad-hoc exercises) — Phase 3 only covers adding extra sets, not extra exercises

</deferred>

---

*Phase: 03-workout-logging*
*Context gathered: 2026-03-06*
