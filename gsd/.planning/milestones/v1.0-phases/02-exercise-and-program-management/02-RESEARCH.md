# Phase 2: Exercise and Program Management - Research

**Researched:** 2026-03-06
**Domain:** CRUD APIs (FastAPI + SQLAlchemy) + Interactive Vue 3 UI (exercise library, program builder)
**Confidence:** HIGH

## Summary

Phase 2 builds the exercise browsing/creation UI and program builder on top of the Phase 1 scaffold. The backend needs CRUD endpoints for exercises and programs. The frontend needs two major interactive views (exercise library with grouped/filterable list, program builder with per-set targets) plus responsive navigation (top navbar desktop, bottom tab bar mobile).

A critical schema change is required: the current `program_exercises` table uses flat `target_sets/target_reps/target_weight_kg` columns, but the user wants per-set targets (each set has its own reps, weight, and warmup flag). This requires a new `program_sets` table and an Alembic migration in the scripts repo, plus model updates in both scripts and backend repos. Additionally, the `exercises.name` column currently has a `UNIQUE` constraint that must be dropped since the user decided duplicate exercise names are allowed.

**Primary recommendation:** Start with the schema migration and backend CRUD, then build frontend views. The navigation refactor (responsive navbar/tab bar) should be done first in the frontend since it affects the app shell used by all views.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Grouped list layout: exercises grouped by muscle group with collapsible sections
- Equipment dropdown filter + text search box for finding exercises by name
- Custom exercises shown with a subtle "Custom" badge to distinguish from seeded ones
- Per-section inline "+" button: clicking [+] next to a muscle group header opens an inline form within that section
- Inline form fields: name and equipment dropdown (muscle group pre-filled from section)
- Custom exercises can be edited (rename, change equipment/muscle group) and deleted; seeded exercises are read-only
- Duplicate exercise names allowed (exact match only)
- Per-set targets: each exercise in a program has individually defined sets, each with its own reps, weight, and warmup flag
- This requires a new `program_sets` table (current schema only has single target_sets/reps/weight on program_exercises -- needs migration)
- Exercise reordering via up/down arrow buttons (no drag-and-drop)
- Same exercise allowed multiple times in one program
- Program creation/editing on a separate page (/programs/new, /programs/:id/edit)
- Programs list page shows all programs with edit and delete actions
- Responsive from the start -- works on both desktop and mobile
- Adaptive navigation: top navbar on desktop, bottom tab bar on mobile
- 4 navigation items: Exercises, Programs, Workout, History
- Clean minimal aesthetic: lots of whitespace, subtle borders, muted colors (Linear/Notion style)

### Claude's Discretion
- Section expand/collapse default behavior
- Exercise picker UX within program builder
- Loading states and empty states
- Exact spacing, typography, and color palette within the minimal style
- Error handling and validation feedback presentation

### Deferred Ideas (OUT OF SCOPE)
- Superset/circuit support (grouped exercises executed continuously) -- ADV-03
- Discard entire workout session mid-workout or after -- Phase 3 (LOG-03)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| EXER-01 | User can browse a library of exercises categorized by muscle group and equipment | Backend GET /exercises with filtering; frontend grouped list view with collapsible sections and equipment filter |
| EXER-02 | User can create custom exercises with name, muscle group, and equipment | Backend POST /exercises; frontend inline form per muscle group section; edit/delete for custom only |
| PROG-01 | User can create a workout program as an ordered list of exercises with target sets/reps/weight | New `program_sets` table + migration; backend POST /programs with nested sets; frontend program builder page |
| PROG-02 | User can edit and delete programs | Backend PUT/DELETE /programs/:id; frontend program edit page reusing builder; delete confirmation |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.135 | REST API framework | Already in backend pyproject.toml |
| SQLAlchemy | >=2.0.48 | ORM with Mapped[] typing | Already in use, canonical models in scripts repo |
| Pydantic | >=2.12 | Request/response validation | FastAPI's native schema layer |
| Vue 3 | ^3.5 | Frontend framework | Already scaffolded with Composition API |
| Pinia | ^3.0 | State management | Already has exercises store stub |
| Vue Router | ^4.6 | Client-side routing | Routes already defined |
| Tailwind CSS | ^4.2 (v4) | Utility CSS | Already configured with @import syntax |
| Alembic | (in scripts) | Schema migrations | Already has initial migration |

### Supporting (no new installs needed)
| Library | Purpose | When to Use |
|---------|---------|-------------|
| Vitest (^4.0) | Frontend unit tests | Already in devDependencies |
| @vue/test-utils (^2.4) | Vue component testing | Already in devDependencies |
| pytest (>=9.0) | Backend API tests | Already in dev dependencies |
| httpx (>=0.28) | Async test client for FastAPI | Already in dev dependencies |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw fetch() | Axios | No need -- fetch() is fine for simple CRUD, avoids extra dependency |
| Drag-and-drop lib | Up/down arrow buttons | User explicitly chose arrows over drag-and-drop |

**Installation:** No new packages needed. All dependencies are already installed.

## Architecture Patterns

### Schema Change: program_sets Table

The most critical architectural decision. The current `program_exercises` table has flat `target_sets/target_reps/target_weight_kg` columns. The user wants per-set targets. The new schema:

```
programs (unchanged)
  |-- program_exercises (remove target_sets, target_reps, target_weight_kg)
  |     |-- program_sets (NEW: set_number, target_reps, target_weight_kg, is_warmup)
```

**New table: `program_sets`**
```python
class ProgramSet(Base):
    __tablename__ = "program_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("program_exercises.id"), nullable=False
    )
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    target_reps: Mapped[int] = mapped_column(Integer, nullable=False)
    target_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_warmup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    program_exercise: Mapped["ProgramExercise"] = relationship(back_populates="sets")
```

**Migration strategy:**
1. Add `program_sets` table
2. Remove `target_sets`, `target_reps`, `target_weight_kg` from `program_exercises` (use Alembic batch mode since SQLite requires it -- already configured with `render_as_batch=True`)
3. Drop `UNIQUE` constraint on `exercises.name` (also batch mode)

**IMPORTANT:** Models must be updated in BOTH `scripts/gymcoach_scripts/db/models.py` (canonical) AND `backend/app/programs/models.py` (duplicate). The Alembic autogenerate reads from the scripts models.

### Backend API Structure

Follow the existing domain-grouped pattern:

```
app/
  exercises/
    routes.py    # GET /exercises (list+filter), POST (create), PUT/:id, DELETE/:id
    schemas.py   # ExerciseCreate, ExerciseUpdate, ExerciseRead (exists)
    models.py    # Exercise (exists)
  programs/
    routes.py    # NEW: GET /programs, POST, GET/:id, PUT/:id, DELETE/:id
    schemas.py   # ProgramCreate (with nested sets), ProgramRead (with nested), ProgramSetRead/Create
    models.py    # Program, ProgramExercise (exist), ProgramSet (NEW)
```

### Pattern 1: FastAPI CRUD Endpoints with SQLAlchemy Session

```python
# Established pattern: synchronous def, Depends(get_db)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/exercises", tags=["exercises"])

@router.get("/", response_model=list[ExerciseRead])
def list_exercises(
    muscle_group: str | None = None,
    equipment: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Exercise)
    if muscle_group:
        query = query.filter(Exercise.muscle_group == muscle_group)
    if equipment:
        query = query.filter(Exercise.equipment == equipment)
    if search:
        query = query.filter(Exercise.name.ilike(f"%{search}%"))
    return query.order_by(Exercise.muscle_group, Exercise.name).all()
```

### Pattern 2: Nested Create with Pydantic Schemas

Programs need nested creation (program + exercises + sets in one request):

```python
class ProgramSetCreate(BaseModel):
    set_number: int
    target_reps: int
    target_weight_kg: float | None = None
    is_warmup: bool = False

class ProgramExerciseCreate(BaseModel):
    exercise_id: int
    order: int
    sets: list[ProgramSetCreate]

class ProgramCreate(BaseModel):
    name: str
    exercises: list[ProgramExerciseCreate]
```

### Pattern 3: Vue Composition API with Pinia Store

```typescript
// Established pattern: Composition API setup function
export const useExercisesStore = defineStore('exercises', () => {
  const exercises = ref<Exercise[]>([])
  const loading = ref(false)

  async function fetchExercises(params?: { muscle_group?: string; equipment?: string; search?: string }) {
    loading.value = true
    try {
      const query = new URLSearchParams()
      if (params?.muscle_group) query.set('muscle_group', params.muscle_group)
      if (params?.equipment) query.set('equipment', params.equipment)
      if (params?.search) query.set('search', params.search)
      const res = await fetch(`/api/exercises?${query}`)
      exercises.value = await res.json()
    } finally {
      loading.value = false
    }
  }

  return { exercises, loading, fetchExercises }
})
```

### Pattern 4: Responsive Navigation (Desktop Navbar / Mobile Tab Bar)

The current App.vue has a top navbar only. It needs to become adaptive:

```vue
<!-- Desktop: top navbar (hidden on mobile) -->
<nav class="hidden md:block ...">...</nav>

<!-- Mobile: bottom tab bar (hidden on desktop) -->
<nav class="fixed bottom-0 left-0 right-0 md:hidden ...">...</nav>

<!-- Main content needs bottom padding on mobile for tab bar clearance -->
<main class="pb-16 md:pb-0 ...">
  <RouterView />
</main>
```

Use Tailwind's `md:` breakpoint (768px) for the responsive switch. No JavaScript needed -- pure CSS with Tailwind responsive utilities.

### Frontend Route Additions

```typescript
// New routes needed for program builder
{ path: '/programs/new', name: 'program-new', component: () => import('../views/ProgramEditView.vue') },
{ path: '/programs/:id/edit', name: 'program-edit', component: () => import('../views/ProgramEditView.vue') },
```

### Anti-Patterns to Avoid
- **Separate API calls per set:** Build the full program (with all exercises and sets) and send as a single nested POST/PUT. Do not make N+1 API calls.
- **Storing filter state in URL query params for exercises:** Keep it simple with component state. URL-based filtering adds complexity without benefit for a single-user app.
- **Using async def endpoints:** The project uses sync `def` endpoints -- no async benefit for single-user SQLite. Stay consistent.
- **Editing canonical models only in backend:** Always update scripts/db/models.py first (canonical), then duplicate to backend.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form validation | Custom validation logic | Pydantic schemas (backend), HTML5 + simple reactive checks (frontend) | Pydantic handles type coercion, constraints, error messages automatically |
| Responsive breakpoints | Custom JS resize listeners | Tailwind responsive prefixes (md:, lg:) | Pure CSS, no JS, standard approach |
| API error responses | Custom error formatting | FastAPI's HTTPException with status codes | Consistent error shape, automatic OpenAPI docs |
| SQLite batch operations | Raw ALTER TABLE | Alembic batch mode (already configured with render_as_batch=True) | SQLite doesn't support ALTER TABLE DROP COLUMN natively |
| Cascade deletes | Manual child deletion code | SQLAlchemy cascade="all, delete-orphan" (already on Program.exercises) | Handles nested deletion automatically |

**Key insight:** The entire stack is already set up. This phase is pure CRUD implementation -- no new infrastructure, no new patterns, just applying established patterns to new endpoints and views.

## Common Pitfalls

### Pitfall 1: SQLite ALTER TABLE Limitations
**What goes wrong:** Trying to drop columns from `program_exercises` fails because SQLite doesn't support `ALTER TABLE DROP COLUMN` in older versions.
**Why it happens:** SQLite has limited ALTER TABLE support.
**How to avoid:** Alembic's `render_as_batch=True` is already configured in env.py. This recreates the table behind the scenes. Verify the migration uses batch operations.
**Warning signs:** Migration error mentioning "ALTER TABLE" not supported.

### Pitfall 2: Model Duplication Drift
**What goes wrong:** Updating models in one repo (backend) but not the other (scripts), causing migration autogenerate to produce wrong diffs.
**Why it happens:** Models are duplicated between scripts (canonical) and backend repos.
**How to avoid:** Always update scripts/db/models.py FIRST, run migration from scripts, then copy model changes to backend.
**Warning signs:** Alembic autogenerate showing unexpected changes.

### Pitfall 3: Eager Loading N+1 Queries
**What goes wrong:** Loading programs list triggers separate queries for each program's exercises and each exercise's sets.
**Why it happens:** SQLAlchemy lazy-loads relationships by default.
**How to avoid:** Use `joinedload()` or `selectinload()` when querying programs with their exercises and sets:
```python
from sqlalchemy.orm import selectinload
db.query(Program).options(
    selectinload(Program.exercises)
    .selectinload(ProgramExercise.sets)
    .selectinload(ProgramExercise.exercise)
).all()
```
**Warning signs:** Slow program list page, many SQL queries in logs.

### Pitfall 4: Foreign Key Enforcement on Delete
**What goes wrong:** Deleting a custom exercise that's used in a program causes foreign key violation.
**Why it happens:** `program_exercises.exercise_id` references `exercises.id`. Foreign keys are ON (PRAGMA set in database.py).
**How to avoid:** Either prevent deletion of exercises that are in use (return 409 Conflict), or cascade. Recommend preventing deletion with a helpful error message.
**Warning signs:** 500 error when deleting exercises.

### Pitfall 5: Order Column Gaps After Reordering
**What goes wrong:** After moving exercises up/down, order values have gaps (1, 3, 4) instead of sequential (1, 2, 3).
**Why it happens:** Naive swap-based reordering.
**How to avoid:** On save, renumber all exercises sequentially based on their position in the list. The frontend manages order as array index; the backend receives the final ordered list.
**Warning signs:** Inconsistent ordering when editing a program.

### Pitfall 6: Tailwind v4 Syntax Differences
**What goes wrong:** Using Tailwind v3 patterns like `@tailwind base` or `tailwind.config.js`.
**Why it happens:** Most documentation and examples still show v3.
**How to avoid:** The project uses Tailwind v4 with `@import "tailwindcss"` in main.css and `@tailwindcss/vite` plugin. No config file needed. Custom values use CSS variables or arbitrary values.
**Warning signs:** Styles not applying, build warnings about deprecated directives.

## Code Examples

### Backend: Exercise CRUD with Filtering

```python
# GET /api/exercises - list with optional filters
@router.get("/", response_model=list[ExerciseRead])
def list_exercises(
    muscle_group: str | None = None,
    equipment: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Exercise)
    if muscle_group:
        query = query.filter(Exercise.muscle_group == muscle_group)
    if equipment:
        query = query.filter(Exercise.equipment == equipment)
    if search:
        query = query.filter(Exercise.name.ilike(f"%{search}%"))
    return query.order_by(Exercise.muscle_group, Exercise.name).all()

# POST /api/exercises - create custom exercise
@router.post("/", response_model=ExerciseRead, status_code=201)
def create_exercise(data: ExerciseCreate, db: Session = Depends(get_db)):
    exercise = Exercise(
        name=data.name,
        muscle_group=data.muscle_group,
        equipment=data.equipment,
        is_custom=True,  # Always true for API-created exercises
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise
```

### Backend: Program with Nested Sets (Create)

```python
@router.post("/", response_model=ProgramRead, status_code=201)
def create_program(data: ProgramCreate, db: Session = Depends(get_db)):
    program = Program(name=data.name)
    db.add(program)
    db.flush()  # Get program.id

    for pe_data in data.exercises:
        pe = ProgramExercise(
            program_id=program.id,
            exercise_id=pe_data.exercise_id,
            order=pe_data.order,
        )
        db.add(pe)
        db.flush()  # Get pe.id

        for s_data in pe_data.sets:
            ps = ProgramSet(
                program_exercise_id=pe.id,
                set_number=s_data.set_number,
                target_reps=s_data.target_reps,
                target_weight_kg=s_data.target_weight_kg,
                is_warmup=s_data.is_warmup,
            )
            db.add(ps)

    db.commit()
    db.refresh(program)
    return program
```

### Frontend: Grouped Exercise List (Computed)

```typescript
// Group exercises by muscle_group for collapsible sections
const grouped = computed(() => {
  const groups: Record<string, Exercise[]> = {}
  for (const ex of exercises.value) {
    if (!groups[ex.muscle_group]) groups[ex.muscle_group] = []
    groups[ex.muscle_group].push(ex)
  }
  return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b))
})
```

### Alembic Migration: Add program_sets, Modify program_exercises

```python
def upgrade() -> None:
    # Create program_sets table
    op.create_table('program_sets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('program_exercise_id', sa.Integer(), nullable=False),
        sa.Column('set_number', sa.Integer(), nullable=False),
        sa.Column('target_reps', sa.Integer(), nullable=False),
        sa.Column('target_weight_kg', sa.Float(), nullable=True),
        sa.Column('is_warmup', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['program_exercise_id'], ['program_exercises.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Remove old flat columns from program_exercises (batch mode for SQLite)
    with op.batch_alter_table('program_exercises') as batch_op:
        batch_op.drop_column('target_sets')
        batch_op.drop_column('target_reps')
        batch_op.drop_column('target_weight_kg')

    # Drop UNIQUE constraint on exercises.name (allow duplicates)
    with op.batch_alter_table('exercises') as batch_op:
        batch_op.drop_constraint('uq_exercises_name', type_='unique')  # or use batch recreate
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind v3 config file | Tailwind v4 `@import "tailwindcss"` + Vite plugin | 2025 | No tailwind.config.js, use CSS variables for customization |
| Options API (Vue) | Composition API + `<script setup>` | Vue 3.2+ | All components use `<script setup lang="ts">` |
| Vuex | Pinia ^3 with Composition API stores | 2024+ | defineStore with setup function pattern |

**Notes on current project state:**
- No CORS middleware configured in backend -- not needed because Vite proxy handles `/api` in development
- Frontend uses `fetch()` (no Axios) -- keep this pattern, no need for extra dependency
- Backend routes use `/api` prefix (set in main.py include_router)

## Open Questions

1. **Exercise name uniqueness constraint removal**
   - What we know: User wants duplicate names allowed. Current schema has `UNIQUE` on `exercises.name`. Seed script uses `filter_by(name=...)` to check for existing exercises.
   - What's unclear: The seed script's dedup logic may need adjustment -- currently skips exercises with matching names. With duplicates allowed, it could create duplicates on re-run.
   - Recommendation: Keep the seed script's existing dedup behavior (skip if name exists). The UNIQUE constraint removal is only for user-created custom exercises. Or better: keep the unique constraint but only for seeded exercises (use the seed script's existing `filter_by` check). Actually simplest: remove the DB-level unique constraint, keep the seed script's application-level dedup. This way custom exercises can have any name, and re-running seed won't create duplicates.

2. **Program update strategy (PUT)**
   - What we know: Need full program edit capability.
   - What's unclear: Partial update (PATCH) vs full replace (PUT).
   - Recommendation: Use PUT with full replace -- delete all existing program_exercises and program_sets for the program, then recreate from the request body. Simpler than diffing. The cascade="all, delete-orphan" on the relationship handles cleanup.

3. **Exercise deletion guard**
   - What we know: Custom exercises can be deleted. Foreign keys are enforced. Exercise might be used in programs.
   - Recommendation: Check if exercise is referenced in any program_exercises before deleting. Return 409 Conflict with a message listing which programs use it. Let the user remove it from programs first.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (backend) | pytest >=9.0 with FastAPI TestClient |
| Framework (frontend) | vitest ^4.0 with @vue/test-utils ^2.4 |
| Config file (backend) | pytest runs from backend/ root (auto-discovers tests/) |
| Config file (frontend) | vitest.config.ts or vite.config.ts (vitest reads vite config) |
| Quick run (backend) | `cd ../backend && uv run pytest tests/ -x -q` |
| Quick run (frontend) | `cd ../frontend && npx vitest run --reporter=verbose` |
| Full suite (backend) | `cd ../backend && uv run pytest tests/ -v` |
| Full suite (frontend) | `cd ../frontend && npx vitest run` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXER-01 | GET /api/exercises returns exercises, filters by muscle_group/equipment/search | unit (API) | `cd ../backend && uv run pytest tests/test_exercises.py -x` | No -- Wave 0 |
| EXER-02 | POST /api/exercises creates custom exercise; PUT/DELETE for custom only | unit (API) | `cd ../backend && uv run pytest tests/test_exercises.py -x` | No -- Wave 0 |
| PROG-01 | POST /api/programs creates program with nested exercises and per-set targets | unit (API) | `cd ../backend && uv run pytest tests/test_programs.py -x` | No -- Wave 0 |
| PROG-02 | PUT /api/programs/:id updates program; DELETE removes program | unit (API) | `cd ../backend && uv run pytest tests/test_programs.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd ../backend && uv run pytest tests/ -x -q`
- **Per wave merge:** Full backend suite + frontend type-check
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `../backend/tests/test_exercises.py` -- covers EXER-01, EXER-02 (exercise CRUD endpoints)
- [ ] `../backend/tests/test_programs.py` -- covers PROG-01, PROG-02 (program CRUD with nested sets)
- [ ] Frontend vitest config may need setup (check if vitest.config.ts exists or if vite.config.ts is sufficient)

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection of all four repos (backend, frontend, scripts, gsd)
- Existing models, schemas, routes, stores, router, and configuration files
- Alembic migration history and env.py configuration
- Seed data analysis: 50 exercises, 6 muscle groups, 6 equipment types

### Secondary (MEDIUM confidence)
- FastAPI patterns: synchronous endpoints with Depends(get_db) -- verified from existing test_health.py and routes
- SQLAlchemy 2.0 Mapped[] patterns -- verified from existing models
- Tailwind v4 setup -- verified from vite.config.ts and main.css

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already installed, versions verified from package.json and pyproject.toml
- Architecture: HIGH - patterns established in Phase 1, just extending with new CRUD endpoints and views
- Schema change: HIGH - Alembic batch mode already configured, migration path clear
- Pitfalls: HIGH - based on direct codebase analysis (duplicate models, SQLite limitations, eager loading)

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable stack, no fast-moving dependencies)
