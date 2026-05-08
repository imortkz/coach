# Phase 2: Exercise and Program Management - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

API and UI for browsing the exercise library, creating custom exercises, and building workout programs as ordered lists of exercises with per-set targets (reps/weight/warmup). Covers EXER-01, EXER-02, PROG-01, PROG-02. Workout logging and history are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Exercise browsing
- Grouped list layout: exercises grouped by muscle group with collapsible sections
- Equipment dropdown filter + text search box for finding exercises by name
- Custom exercises shown with a subtle "Custom" badge to distinguish from seeded ones
- Section expand/collapse default: Claude's discretion (based on exercise count and UX)

### Custom exercise creation
- Per-section inline "+" button: clicking [+] next to a muscle group header opens an inline form within that section
- Inline form fields: name and equipment dropdown (muscle group pre-filled from section)
- Custom exercises can be edited (rename, change equipment/muscle group) and deleted; seeded exercises are read-only
- Duplicate exercise names allowed (exact match only) — user may want variations like "Bench Press (close grip)"

### Program builder
- Per-set targets: each exercise in a program has individually defined sets, each with its own reps, weight, and warmup flag (e.g., Set 1: 12x20kg warmup, Set 2: 12x40kg, Set 3: 12x45kg)
- This requires a new `program_sets` table (current schema only has single target_sets/reps/weight on program_exercises — needs migration)
- Exercise reordering via up/down arrow buttons (no drag-and-drop)
- Same exercise allowed multiple times in one program
- Program creation/editing on a separate page (/programs/new, /programs/:id/edit)
- Programs list page shows all programs with edit and delete actions
- Exercise selection within program builder: Claude's discretion on picker UX (inline search/autocomplete recommended)

### Navigation and layout
- Responsive from the start — works on both desktop and mobile
- Adaptive navigation: top navbar on desktop, bottom tab bar on mobile
- 4 navigation items: Exercises, Programs, Workout, History (routes already exist)

### Visual style
- Clean minimal aesthetic: lots of whitespace, subtle borders, muted colors (Linear/Notion style)

### Claude's Discretion
- Section expand/collapse default behavior
- Exercise picker UX within program builder
- Loading states and empty states
- Exact spacing, typography, and color palette within the minimal style
- Error handling and validation feedback presentation

</decisions>

<specifics>
## Specific Ideas

- Per-set target example from user: "dumbbell press, 12x20kg (warmup), 12x40kg, 12x45kg, 12x45kg" — each set is its own row with reps, weight, and optional warmup flag
- User wants ability to discard entire workout sessions (mid-workout or after) — noted for Phase 3 (LOG-03)
- Linear/Notion referenced as visual style benchmarks

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `useExercisesStore` (frontend/src/stores/exercises.ts): Pinia store with fetchExercises stub — ready to connect to API
- TypeScript types defined (frontend/src/types/index.ts): Exercise, Program, ProgramExercise, Workout, WorkoutSet
- Backend schemas exist: ExerciseRead, ProgramRead, ProgramExerciseRead (Pydantic models)
- Backend route stubs: exercises router at /exercises (empty), programs module exists with models/schemas

### Established Patterns
- Backend: domain-grouped layout (app/exercises/, app/programs/) with models.py, routes.py, schemas.py per domain
- Frontend: Pinia composition API stores, lazy-loaded Vue Router routes, Tailwind CSS v4
- SQLAlchemy models duplicated between scripts (canonical) and backend repos
- Synchronous `def` endpoints (no async)

### Integration Points
- Vue Router already has /exercises and /programs routes pointing to stub views
- Backend exercise router registered but empty — needs CRUD endpoints
- Backend programs module has models but no routes.py yet
- Schema change needed: `program_sets` table for per-set targets (migration via scripts repo Alembic)
- Frontend types/index.ts will need ProgramSet type added

</code_context>

<deferred>
## Deferred Ideas

- Superset/circuit support (grouped exercises executed continuously) — already tracked as ADV-03 in v2 requirements
- Discard entire workout session mid-workout or after — Phase 3 (LOG-03)

</deferred>

---

*Phase: 02-exercise-and-program-management*
*Context gathered: 2026-03-06*
