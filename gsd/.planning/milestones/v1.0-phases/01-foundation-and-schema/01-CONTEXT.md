# Phase 1: Foundation and Schema - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Scaffold all three repos (backend, frontend, scripts) with working dev environments. Create the SQLite database schema with plan-vs-log table separation, run migrations cleanly, and seed the exercise library with categorized data. No UI features, no business logic beyond schema and seed.

</domain>

<decisions>
## Implementation Decisions

### Exercise Seed Data
- ~40-60 exercises covering major compounds and popular accessories
- Categorized by body region groups: Chest, Back, Shoulders, Arms, Core, Legs
- Equipment types (expanded set): Barbell, Dumbbell, Cable, Machine, Bodyweight, Kettlebell, Smith Machine, EZ Bar, Resistance Band, Trap Bar, Landmine
- Each exercise has one primary muscle group only (no secondary)

### Schema Conventions
- Weight stored in kilograms as canonical unit; display unit is user-configurable
- Key-value settings table for user preferences (weight_unit, rest_timer_seconds, etc.) — easy to extend without migrations
- Warm-up sets tracked via `is_warmup` boolean flag on workout_sets table
- Auto-increment integer primary keys throughout
- Plan tables (programs, program_exercises) separated from log tables (workouts, workout_sets) per research decision

### Repo Structure — Backend
- Domain-grouped layout: app/exercises/, app/workouts/, app/programs/, etc.
- Each domain folder contains routes, models, and schemas

### Repo Structure — Frontend
- Type-based layout: src/components/, src/views/, src/composables/, src/stores/
- Pinia for state management
- Vue Router set up from the start with stub routes for exercises, programs, workout, history

### Dev Environment
- Python: Ruff for linting and formatting
- Frontend: ESLint + Prettier
- Testing: pytest (backend/scripts) and Vitest (frontend) installed with config — no tests written yet
- Package management: uv for Python repos, npm for frontend

### Build and Deployment
- Dev workflow: separate terminals for backend and frontend
- Vite dev server proxies /api/* requests to FastAPI backend (no CORS config needed)
- Dockerfiles included for backend and frontend (not deploying yet, just ready)
- SQLite database in shared directory: ../data/gymcoach.db (both backend and scripts access same path)

### Claude's Discretion
- Exact exercise list within the ~40-60 range and category assignments
- Directory structure details within the domain-grouped (backend) and type-based (frontend) patterns
- Dockerfile specifics and multi-stage build setup
- Alembic configuration details
- Ruff/ESLint/Prettier rule configuration

</decisions>

<specifics>
## Specific Ideas

- Research decision: use synchronous `def` endpoints (no async benefit for single-user SQLite)
- Research decision: Alembic for migrations (auto-generates from model diffs)
- Settings table should be key-value to avoid migrations when adding new preferences
- Shared data directory (../data/) keeps database accessible to both backend and scripts repos

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — all three repos are empty (clean slate)

### Established Patterns
- None yet — Phase 1 establishes the patterns that all subsequent phases follow

### Integration Points
- SQLite DB at ../data/gymcoach.db shared between backend and scripts
- Vite proxy connects frontend to backend API
- Alembic migrations in scripts/ manage schema for backend's models

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-and-schema*
*Context gathered: 2026-03-06*
