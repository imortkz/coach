# M005: Progress Report — Context

**Gathered:** 2026-03-14
**Status:** Queued — pending auto-mode execution.

## Project Description

GymCoach is a personal gym training companion. Users log workouts against programs, and the app tracks weight progression over time. Historical data exists (workouts with denormalized sets including weight, reps, muscle group, exercise name, timestamps) but there is no aggregated progress view beyond per-exercise session history.

## Why This Milestone

The existing history tab shows a reverse-chronological list of workouts and per-exercise line charts (weight over sessions). There is no way to see monthly patterns — how training load changed week-over-week, whether frequency dropped, or which PRs were hit during a period. The goal is to give the user context on a month of progress in a single, readable view.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Navigate to a `/report` page and see a 4-week progress report (default window, configurable)
- See total training volume broken down by muscle group per week (stacked bar or grouped line chart)
- See workout frequency per week (workouts completed per calendar week)
- See a personal records table listing the heaviest set per exercise hit during the period, with a comparison to the previous best before the period
- Adjust the report window (e.g. 2 weeks, 4 weeks, 8 weeks) and have the charts re-render

### Entry point / environment

- Entry point: http://localhost:5173/report — linked from the main navigation
- Environment: browser (mobile-first)
- Live dependencies involved: backend API (new aggregation endpoint), MongoDB (workout history)

## Completion Class

- Contract complete means: `GET /api/workouts/report?weeks=4` returns structured JSON with volume-by-week-by-muscle, frequency-by-week, and PR data; endpoint is covered by at least 2 backend tests
- Integration complete means: `/report` page renders all three sections with real data from a seeded dev workout history; chart.js charts load without errors; empty state handled gracefully
- Operational complete means: none

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- `GET /api/workouts/report?weeks=4` returns correctly bucketed data for a user with at least 3 weeks of workout history
- `/report` page renders: volume-by-muscle-group chart, frequency chart, PR table — all three sections visible without scrolling past a broken state
- Changing weeks selector from 4 to 8 re-fetches and re-renders all three charts with the wider window
- User with zero workout history in the period sees a graceful empty state (not a blank/broken chart)
- Existing backend test suite still passes (≥ current count) after the new endpoint is added

## Risks and Unknowns

- **Aggregation complexity in Python vs MongoDB** — Volume aggregation (sets × reps × weight, grouped by week and muscle group) can be done either via MongoDB aggregation pipeline or in Python after fetching workouts in range. MongoDB aggregation is more efficient but harder to test; Python-side aggregation is simpler and fully testable. Given personal-tool scale (~hundreds of workouts max), Python-side is the right call — no premature pipeline complexity.
- **PR definition** — "Personal record" means the heaviest single set (`weight_kg`) logged for an exercise during the report period, compared to the heaviest set for the same exercise in all prior workouts. Warmup sets should probably be excluded from PRs (`is_warmup=false`). This needs a clear definition in the plan.
- **Week bucketing** — Calendar week (Mon–Sun) vs rolling 7-day windows starting from today both work. Calendar weeks are more natural for monthly context. The plan should make an explicit choice.
- **Sparse data** — If a user only trained once in a 4-week window, volume charts will have 3 empty weeks. Chart.js handles sparse data fine with null values; the backend must return all weeks in the range (with zero volume) not just weeks with data.
- **Chart.js types already registered** — `ExerciseChart.vue` registers `Line` chart types. The report will need `Bar` for volume and frequency. New Chart.js component types (Bar) need to be registered; the existing registration in ExerciseChart.vue is component-local, so the report view will need its own registrations.
- **Mobile layout** — Three chart sections on mobile requires careful stacking. Volume chart (with multiple muscle group datasets) can get crowded on narrow screens — a legend placement choice matters.

## Existing Codebase / Prior Art

- `../backend/app/workouts/routes.py` — `list_workouts` returns paginated raw workouts; a new `/report` endpoint aggregates across the date window; can reuse the `user_id` filter pattern
- `../backend/app/workouts/models.py` — `WorkoutSet` has `weight_kg`, `reps`, `is_warmup`, `exercise_name`, `exercise_muscle_group`, `exercise_id`; `Workout` has `completed_at`, `user_id` — all fields needed for aggregation are present and denormalized
- `../frontend/src/components/history/ExerciseChart.vue` — uses `vue-chartjs` Line chart with Chart.js already installed; pattern to follow for new chart components
- `../frontend/src/stores/history.ts` — paginated workout fetch; report will need a separate store or composable (different fetch shape, date-range params, not paginated)
- `../frontend/src/views/HistoryView.vue` — existing history view; report is a new sibling route, not an extension of this view
- `../frontend/src/router/index.ts` — router where `/report` route needs to be added

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

No existing requirements map directly — this is new scope. New capability introduced:

- Aggregated progress reporting over a configurable time window (volume by muscle group, workout frequency, personal records)

## Scope

### In Scope

- New backend endpoint: `GET /api/workouts/report?weeks=N` — returns three payloads:
  1. `volume_by_week`: list of `{ week_label, muscle_group, volume_kg }` records for stacked bar chart
  2. `frequency_by_week`: list of `{ week_label, count }` for bar chart
  3. `personal_records`: list of `{ exercise_name, best_weight_in_period, previous_best, is_new_pr }` (excluding warmup sets)
- Aggregation done in Python (not MongoDB pipeline) — fetch completed workouts in date range, compute in-memory
- At least 2 backend tests for the report endpoint (typical user with data, empty state)
- New frontend route `/report` with:
  - Week selector (2 / 4 / 8 weeks) — defaults to 4
  - Volume by muscle group chart (stacked bar, one bar group per week, one color per muscle group)
  - Workout frequency chart (simple bar, one bar per week)
  - PR table (exercise name, best weight in period, previous best, "NEW PR" badge if `is_new_pr`)
- New Pinia store or composable for report data fetching (separate from history store)
- Link to `/report` in main navigation
- Graceful empty state for each section when no data exists in the period

### Out of Scope / Non-Goals

- PDF export — in-app view only
- Per-exercise volume breakdown (only muscle group level)
- Rep-based volume metrics separate from weight-based (volume = sets × reps × weight_kg only)
- Streak tracking or consistency scores
- Comparison between two custom date ranges
- Sharing or exporting the report
- Push notifications or scheduled report delivery

## Technical Constraints

- Backend: Python aggregation only (no MongoDB `$group` pipeline) — keeps the logic testable and the complexity appropriate to scale
- Frontend: chart.js + vue-chartjs already installed; `Bar` chart type needs registering in the report view (not globally, following existing component-local pattern from ExerciseChart.vue)
- Week bucketing: calendar weeks (Monday–Sunday) — consistent with how people think about training weeks
- PR calculation excludes `is_warmup=true` sets
- Report endpoint must return all N weeks in the range even if some have zero workouts (zero-fill gaps)
- All existing backend tests must continue to pass

## Integration Points

- `GET /api/workouts/report?weeks=N` → new Pinia store/composable → three chart components + PR table in `ReportView.vue`
- `../frontend/src/router/index.ts` → new `/report` route, guarded like other authenticated routes
- Main navigation (App.vue or nav component) → link to `/report`
- Existing workout data in MongoDB → Python aggregation in the new endpoint → structured JSON response

## Open Questions

- None — design questions resolved during discussion.
