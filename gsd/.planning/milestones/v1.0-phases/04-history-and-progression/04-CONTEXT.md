# Phase 4: History and Progression - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

View past workout data (chronological history and per-exercise history) and receive intelligent weight progression suggestions during workouts. Covers HIST-01, HIST-02, PRGS-01, PRGS-02. CLI analytics and data export are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Workout history list
- Summary cards in reverse chronological order — most recent at top
- Each card shows: date, program name, exercise count, total sets, duration
- Tap card to expand inline showing full exercise details (sets/reps/weight) — no page navigation
- Tap again to collapse
- Program filter dropdown at top ("All", "Push Day A", etc.) — no date range filter
- Load-more or infinite scroll for older workouts

### Per-exercise history
- Dedicated page at /exercises/:id/history with chart on top, session table below
- Two entry points: tap exercise name in expanded history card, or tap exercise in exercise library
- Chart shows two lines: best set weight per session and total volume (sets x reps x weight)
- Session table shows last 10-20 sessions with date and all sets (reps @ weight)
- At the top of the page, show next progression suggestion: "Next session: try 82.5kg (+2.5)" or "Keep at 80kg — missed reps last time"

### Progression algorithm
- Trigger: all non-warmup sets hit or exceeded target reps at current weight in last session
- Lookback: last session only (simple linear progression)
- Increment varies by equipment type (stored in settings, user-overridable):
  - Barbell: +2.5kg
  - Dumbbell: +2.0kg
  - Cable/Machine: +2.5kg
  - Bodyweight: +1 rep (no weight increase)
  - Kettlebell: +4.0kg
  - Smith Machine: +2.5kg
  - EZ Bar: +2.5kg
  - Resistance Band: +1 rep
  - Trap Bar: +2.5kg
  - Landmine: +2.5kg
- Runs server-side, extending the existing pre-fill endpoint with a `suggestions` field

### Suggestion presentation
- Suggested weight replaces the pre-fill value with a small upward arrow indicator and accent color
- User can edit freely — override is silent, no tracking or feedback
- Exercises without enough history show normal pre-fill (program targets or last session), no special indicator
- Progression suggestions also visible on the per-exercise history page (not just during workouts)

### Claude's Discretion
- Chart library choice and styling
- Exact arrow/accent color for suggestion indicator
- Loading and empty states for history views
- Session table pagination or scroll behavior
- How progression increments are stored in settings (key naming, defaults)

</decisions>

<specifics>
## Specific Ideas

- Tap-to-expand cards keep the history browsable without page transitions — scan multiple workouts quickly
- Progression suggestions integrated into pre-fill response keeps the existing tap-to-complete flow unchanged — user just taps to accept the suggested weight
- Equipment-based increments match real-world plate/dumbbell availability
- Chart with weight + volume lines gives both strength trend and work capacity at a glance

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `WorkoutRead` schema with nested `WorkoutSetRead` (includes exercise info via `ExerciseRead`) — ready for history endpoints
- `Workout` model has `started_at`, `completed_at`, `program_id` — all needed for history display
- `WorkoutSet` model has `exercise_id`, `weight_kg`, `reps`, `is_warmup` — all needed for progression algorithm
- Pre-fill endpoint already queries last session per exercise — progression logic extends this naturally
- `useProgramsStore` and `useWorkoutsStore` Pinia patterns — replicate for history store
- `Exercise` model has `equipment` field — used to determine increment type
- `Setting` model (key-value) — store progression increment overrides

### Established Patterns
- Backend: domain-grouped layout, synchronous endpoints, `selectinload` for eager loading
- Frontend: Pinia composition API stores, lazy-loaded routes, adaptive nav (top bar desktop, bottom tabs mobile)
- Frontend: Tailwind CSS v4, SVG inline icons, Linear/Notion minimal aesthetic
- Phase 3: expand/collapse pattern on exercise cards — reuse for history card expand

### Integration Points
- Vue Router: /history route exists pointing to stub HistoryView.vue
- New route needed: /exercises/:id/history for per-exercise history page
- Backend: extend WorkoutStartResponse with `suggestions` dict alongside existing `pre_fill`
- Backend: new history endpoints (GET /api/workouts with pagination, GET /api/exercises/:id/history)
- Settings table: progression increment defaults per equipment type
- Exercise library: add tap handler to navigate to exercise history

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-history-and-progression*
*Context gathered: 2026-03-07*
