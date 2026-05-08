# Phase 1: Foundation and Schema - Research

**Researched:** 2026-03-06
**Domain:** Project scaffolding, SQLite schema design, Python/Vue dev environments
**Confidence:** HIGH

## Summary

Phase 1 scaffolds three empty repos (backend, frontend, scripts) into working dev environments, creates the SQLite database schema with Alembic migrations, and seeds an exercise library. All repos start from scratch -- no existing code or config to work around.

The stack is well-established: FastAPI + SQLAlchemy 2.0 + Pydantic v2 for backend, Vue 3 + Vite + Pinia + Tailwind CSS v4 for frontend, and Click + Rich for CLI scripts. All three Python-side repos share a single SQLite database at `../data/gymcoach.db`. The user has made clear decisions on schema conventions (kg-canonical weights, integer PKs, plan-vs-log separation, key-value settings table) and repo layouts (domain-grouped backend, type-based frontend).

**Primary recommendation:** Scaffold repos in dependency order -- scripts first (models + migrations create the DB), then backend (imports models, serves API), then frontend (connects via Vite proxy). Use synchronous `def` endpoints throughout since there is no async benefit for single-user SQLite.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- ~40-60 exercises covering major compounds and popular accessories
- Categorized by body region groups: Chest, Back, Shoulders, Arms, Core, Legs
- Equipment types (expanded set): Barbell, Dumbbell, Cable, Machine, Bodyweight, Kettlebell, Smith Machine, EZ Bar, Resistance Band, Trap Bar, Landmine
- Each exercise has one primary muscle group only (no secondary)
- Weight stored in kilograms as canonical unit; display unit is user-configurable
- Key-value settings table for user preferences (weight_unit, rest_timer_seconds, etc.)
- Warm-up sets tracked via `is_warmup` boolean flag on workout_sets table
- Auto-increment integer primary keys throughout
- Plan tables (programs, program_exercises) separated from log tables (workouts, workout_sets)
- Backend: Domain-grouped layout (app/exercises/, app/workouts/, app/programs/)
- Frontend: Type-based layout (src/components/, src/views/, src/composables/, src/stores/)
- Pinia for state management
- Vue Router with stub routes for exercises, programs, workout, history
- Python: Ruff for linting/formatting
- Frontend: ESLint + Prettier
- Testing: pytest (backend/scripts), Vitest (frontend) -- installed with config, no tests written yet
- Vite dev server proxies /api/* to FastAPI backend
- Dockerfiles included for backend and frontend (not deploying yet)
- SQLite database in shared directory: ../data/gymcoach.db
- Synchronous `def` endpoints (no async)
- Alembic for migrations

### Claude's Discretion
- Exact exercise list within the ~40-60 range and category assignments
- Directory structure details within the domain-grouped (backend) and type-based (frontend) patterns
- Dockerfile specifics and multi-stage build setup
- Alembic configuration details
- Ruff/ESLint/Prettier rule configuration

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCRP-01 | DB schema migrations manage SQLite schema changes | Alembic with `render_as_batch=True` for SQLite compatibility; models defined in scripts or shared package, Alembic autogenerate from model diffs |
| SCRP-02 | Seed script populates exercise library | Click CLI command that reads exercise data and bulk-inserts via SQLAlchemy; ~40-60 exercises with muscle_group and equipment fields |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.x | REST API framework | Official recommendation for Python APIs, auto-generates OpenAPI docs |
| SQLAlchemy | 2.0.x | ORM and database toolkit | Industry standard Python ORM, Mapped[] annotation style in 2.0 |
| Pydantic | 2.x | Request/response validation | Built into FastAPI, `from_attributes=True` for ORM bridging |
| Alembic | 1.18.x | Database migrations | Official SQLAlchemy migration tool, autogenerate support |
| Vue | 3.x | Frontend framework | Composition API, reactive, lightweight |
| Vite | 6.x | Frontend build tool | Fast HMR, native ESM, built-in proxy |
| Pinia | 2.x | Vue state management | Official Vue state library, replaces Vuex |
| Vue Router | 4.x | Client-side routing | Official Vue router |
| Tailwind CSS | 4.x | Utility-first CSS | No PostCSS config needed in v4, Vite plugin |
| Click | 8.x | Python CLI framework | Standard for Python CLIs, decorator-based |
| Rich | 13.x | Terminal formatting | Pretty tables, progress bars for CLI output |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uvicorn | 0.34.x | ASGI server | Running FastAPI in dev and production |
| python-dotenv | 1.x | Env var loading | Database path configuration |
| ruff | 0.9.x | Python linter/formatter | Replaces flake8+black+isort in one tool |
| pytest | 8.x | Python testing | Backend and scripts test framework |
| vitest | 3.x | Frontend testing | Vue component and unit tests |
| @tailwindcss/vite | 4.x | Tailwind Vite plugin | Zero-config Tailwind integration |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLAlchemy + Pydantic | SQLModel | Less code duplication but lags behind SQLAlchemy/Pydantic updates; user chose separate models |
| Alembic | Manual SQL | Alembic autogenerates from model diffs, manual SQL is error-prone |
| Click | argparse | Click has better UX (decorators, help text, colors) |

**Installation (backend):**
```bash
cd ../backend
uv init --app --bare
uv add fastapi uvicorn sqlalchemy pydantic python-dotenv
uv add --dev ruff pytest
```

**Installation (scripts):**
```bash
cd ../scripts
uv init --app --bare
uv add sqlalchemy alembic click rich python-dotenv
uv add --dev ruff pytest
```

**Installation (frontend):**
```bash
cd ../frontend
npm create vue@latest . -- --force
# Select: TypeScript, Vue Router, Pinia, ESLint + Prettier, Vitest
npm install
npm install -D tailwindcss @tailwindcss/vite
```

## Architecture Patterns

### Recommended Project Structure

**Backend (../backend/):**
```
app/
├── __init__.py
├── main.py              # FastAPI app, health endpoint
├── database.py          # Engine, SessionLocal, get_db dependency
├── config.py            # Settings (DB path, etc.)
├── exercises/
│   ├── __init__.py
│   ├── models.py        # SQLAlchemy Exercise model
│   ├── schemas.py       # Pydantic schemas
│   └── routes.py        # API endpoints
├── programs/
│   ├── __init__.py
│   ├── models.py        # Program, ProgramExercise models
│   ├── schemas.py
│   └── routes.py
└── workouts/
    ├── __init__.py
    ├── models.py        # Workout, WorkoutSet models
    ├── schemas.py
    └── routes.py
```

**Scripts (../scripts/):**
```
gymcoach_scripts/
├── __init__.py
├── cli.py               # Click group, entry point
├── migrate.py           # Migration commands
├── seed.py              # Seed data commands
├── seed_data/
│   └── exercises.json   # Exercise library data
└── db/
    ├── __init__.py
    ├── models.py         # All SQLAlchemy models (canonical source)
    ├── engine.py         # Engine creation, WAL pragma
    └── alembic/
        ├── alembic.ini
        ├── env.py
        └── versions/
```

**Frontend (../frontend/):**
```
src/
├── App.vue
├── main.ts
├── router/
│   └── index.ts         # Routes: exercises, programs, workout, history
├── views/
│   ├── ExercisesView.vue
│   ├── ProgramsView.vue
│   ├── WorkoutView.vue
│   └── HistoryView.vue
├── components/          # Reusable components (empty stubs for now)
├── composables/         # Shared composition functions
├── stores/              # Pinia stores
│   └── exercises.ts
├── assets/
│   └── main.css         # @import "tailwindcss"
└── types/               # TypeScript interfaces
```

### Pattern 1: SQLAlchemy 2.0 Declarative Models

**What:** Use the modern `Mapped[]` annotation style for model definitions.
**When to use:** All database models.

```python
from sqlalchemy import String, Integer, ForeignKey, Boolean, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    muscle_group: Mapped[str] = mapped_column(String(50))  # Chest, Back, etc.
    equipment: Mapped[str] = mapped_column(String(50))      # Barbell, Dumbbell, etc.
    is_custom: Mapped[bool] = mapped_column(default=False)

class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    exercises: Mapped[list["ProgramExercise"]] = relationship(back_populates="program", cascade="all, delete-orphan")

class ProgramExercise(Base):
    __tablename__ = "program_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    order: Mapped[int] = mapped_column(Integer)
    target_sets: Mapped[int] = mapped_column(Integer)
    target_reps: Mapped[int] = mapped_column(Integer)
    target_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    program: Mapped["Program"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()

class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sets: Mapped[list["WorkoutSet"]] = relationship(back_populates="workout", cascade="all, delete-orphan")

class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    set_number: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_warmup: Mapped[bool] = mapped_column(default=False)
    workout: Mapped["Workout"] = relationship(back_populates="sets")
    exercise: Mapped["Exercise"] = relationship()

class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))
```

### Pattern 2: SQLite WAL Mode via Event Listener

**What:** Enable WAL mode on every connection using SQLAlchemy events.
**When to use:** Engine creation in both backend and scripts.

```python
from sqlalchemy import create_engine, event
import os

DB_PATH = os.environ.get("GYMCOACH_DB", os.path.join(os.path.dirname(__file__), "..", "..", "data", "gymcoach.db"))

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### Pattern 3: FastAPI Synchronous Session Dependency

**What:** Yield-based dependency injection for DB sessions with sync endpoints.
**When to use:** All FastAPI route handlers.

```python
from sqlalchemy.orm import Session, sessionmaker

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in routes -- note: def, not async def
from fastapi import Depends

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    return {"status": "ok", "database": "connected"}
```

### Pattern 4: Vite Proxy Configuration

**What:** Forward /api/* requests from Vite dev server to FastAPI backend.
**When to use:** vite.config.ts setup.

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

Note: No `rewrite` needed -- FastAPI routes will be prefixed with `/api` as well.

### Pattern 5: Alembic Batch Mode for SQLite

**What:** Configure Alembic to use batch operations, required for SQLite ALTER TABLE support.
**When to use:** env.py configuration.

```python
# In env.py run_migrations_online():
def run_migrations_online():
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # CRITICAL for SQLite
        )

        with context.begin_transaction():
            context.run_migrations()
```

### Anti-Patterns to Avoid
- **async def with sync SQLAlchemy:** Using `async def` endpoints with synchronous `Session` blocks the event loop. Use plain `def` for all endpoints since there is no async benefit for single-user SQLite.
- **Models defined in multiple places:** Define SQLAlchemy models once in scripts (canonical source), import in backend. Do NOT duplicate model definitions.
- **Hardcoded DB paths:** Use environment variables or config for the database path so backend and scripts can share it.
- **Missing check_same_thread=False:** SQLite will throw errors when accessed from FastAPI's threadpool without this flag.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Database migrations | SQL scripts | Alembic autogenerate | Tracks schema versions, generates diffs from models, handles SQLite batch mode |
| API documentation | Manual docs | FastAPI auto-OpenAPI | Built-in Swagger UI at /docs |
| Request validation | Manual checks | Pydantic schemas | Type-safe, auto-generates error messages |
| CLI argument parsing | sys.argv | Click decorators | Help text, type coercion, subcommands |
| CSS utilities | Custom classes | Tailwind CSS | Consistent design tokens, purging, responsive |
| State management | Custom reactive stores | Pinia | Devtools integration, SSR-ready, type-safe |

**Key insight:** This phase establishes the foundation -- every shortcut or hand-rolled solution here will be inherited by all subsequent phases. Use the standard tools.

## Common Pitfalls

### Pitfall 1: SQLite ALTER TABLE Limitations
**What goes wrong:** Alembic generates standard ALTER TABLE commands that SQLite does not support (e.g., dropping columns, renaming columns in older SQLite versions).
**Why it happens:** SQLite has limited ALTER TABLE support compared to PostgreSQL/MySQL.
**How to avoid:** Set `render_as_batch=True` in Alembic env.py. This makes Alembic use a "move and copy" strategy.
**Warning signs:** Migration errors mentioning "near ALTER: syntax error".

### Pitfall 2: Foreign Keys Disabled by Default in SQLite
**What goes wrong:** Foreign key constraints are not enforced, leading to orphaned records.
**Why it happens:** SQLite has PRAGMA foreign_keys=OFF by default.
**How to avoid:** Add `PRAGMA foreign_keys=ON` in the connect event listener. Must be set per-connection, not once.
**Warning signs:** Deleting a program does not cascade-delete its program_exercises.

### Pitfall 3: Model Import Order with Alembic Autogenerate
**What goes wrong:** Alembic autogenerate does not detect all tables.
**Why it happens:** Models must be imported before `target_metadata` is used so they register with `Base.metadata`.
**How to avoid:** Import all model modules in env.py before accessing `target_metadata`.
**Warning signs:** `alembic revision --autogenerate` creates empty migration.

### Pitfall 4: Shared Database Path Mismatch
**What goes wrong:** Backend and scripts create separate database files.
**Why it happens:** Each repo resolves relative paths from its own root.
**How to avoid:** Use an absolute path or environment variable (e.g., `GYMCOACH_DB`) that both repos read. The `../data/` directory must be created if it does not exist.
**Warning signs:** Seed data not visible in API responses.

### Pitfall 5: create-vue Interactive Prompts in CI/Automation
**What goes wrong:** `npm create vue@latest` hangs waiting for interactive input.
**Why it happens:** The scaffolding tool prompts for feature selection.
**How to avoid:** The executor should either use the interactive prompts or manually set up the project structure with the right dependencies. For automation, manually create package.json and install dependencies.
**Warning signs:** Command hangs indefinitely.

### Pitfall 6: Tailwind v4 Setup Differs from v3
**What goes wrong:** Using old `@tailwind base; @tailwind components; @tailwind utilities;` directives.
**Why it happens:** Most tutorials still show v3 syntax.
**How to avoid:** In Tailwind v4, use `@import "tailwindcss"` in CSS. No `tailwind.config.js` needed. Use `@tailwindcss/vite` plugin.
**Warning signs:** Tailwind classes not applying, PostCSS errors.

## Code Examples

### Seed Script Pattern (Click + SQLAlchemy)

```python
import json
import os
import click
from sqlalchemy.orm import Session
from gymcoach_scripts.db.engine import engine, SessionLocal
from gymcoach_scripts.db.models import Exercise

@click.command()
@click.option("--data-file", default=None, help="Path to exercises JSON file")
def seed(data_file: str | None):
    """Populate the exercise library with seed data."""
    if data_file is None:
        data_file = os.path.join(os.path.dirname(__file__), "seed_data", "exercises.json")

    with open(data_file) as f:
        exercises = json.load(f)

    with SessionLocal() as db:
        existing = db.query(Exercise).count()
        if existing > 0:
            click.echo(f"Database already has {existing} exercises. Use --force to re-seed.")
            return

        for ex in exercises:
            db.add(Exercise(
                name=ex["name"],
                muscle_group=ex["muscle_group"],
                equipment=ex["equipment"],
                is_custom=False,
            ))
        db.commit()
        click.echo(f"Seeded {len(exercises)} exercises.")
```

### Exercise Seed Data Format

```json
[
  {"name": "Barbell Bench Press", "muscle_group": "Chest", "equipment": "Barbell"},
  {"name": "Incline Dumbbell Press", "muscle_group": "Chest", "equipment": "Dumbbell"},
  {"name": "Cable Fly", "muscle_group": "Chest", "equipment": "Cable"},
  {"name": "Barbell Back Squat", "muscle_group": "Legs", "equipment": "Barbell"},
  {"name": "Romanian Deadlift", "muscle_group": "Legs", "equipment": "Barbell"},
  {"name": "Pull-Up", "muscle_group": "Back", "equipment": "Bodyweight"}
]
```

### Settings Table Access Pattern

```python
def get_setting(db: Session, key: str, default: str | None = None) -> str | None:
    setting = db.query(Setting).filter(Setting.key == key).first()
    return setting.value if setting else default

def set_setting(db: Session, key: str, value: str) -> None:
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        setting.value = value
    else:
        db.add(Setting(key=key, value=value))
    db.commit()
```

### Pydantic Schema with from_attributes

```python
from pydantic import BaseModel

class ExerciseRead(BaseModel):
    id: int
    name: str
    muscle_group: str
    equipment: str
    is_custom: bool

    model_config = {"from_attributes": True}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SQLAlchemy 1.x `Column()` style | SQLAlchemy 2.0 `Mapped[]` annotations | 2023 (SA 2.0 release) | Type-safe, IDE autocomplete, cleaner syntax |
| Pydantic v1 `orm_mode` | Pydantic v2 `from_attributes` in `model_config` | 2023 (Pydantic v2) | Breaking change -- use `model_config` dict not `class Config` |
| Tailwind v3 + PostCSS | Tailwind v4 + Vite plugin | Jan 2025 | No tailwind.config.js, no PostCSS, `@import "tailwindcss"` |
| Vuex | Pinia | 2022 (Vue 3 official) | Simpler API, TypeScript-native, devtools |
| pip + requirements.txt | uv + pyproject.toml | 2024 | 10-100x faster installs, lockfile, venv management |

**Deprecated/outdated:**
- `class Config: orm_mode = True` -- replaced by `model_config = {"from_attributes": True}` in Pydantic v2
- `@tailwind base; @tailwind components; @tailwind utilities;` -- replaced by `@import "tailwindcss"` in v4
- `Column(Integer)` style models -- replaced by `Mapped[int]` in SQLAlchemy 2.0

## Open Questions

1. **Model sharing between backend and scripts**
   - What we know: Models are defined in scripts (which owns Alembic), but backend needs them too.
   - What's unclear: Whether to duplicate models or import across repos.
   - Recommendation: Define models canonically in scripts, have backend import from `../scripts/` via path manipulation or symlink. Alternatively, duplicate and keep in sync (simpler for a small project). Given the repos are independent git repos, duplication with a comment noting the canonical source is pragmatic for a single-user project.

2. **uv not installed on this machine**
   - What we know: `uv` is not found in PATH. The project specifies uv for Python package management.
   - What's unclear: Whether it should be installed via homebrew or standalone installer.
   - Recommendation: Install via `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh` before Phase 1 execution begins.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (backend/scripts), Vitest 3.x (frontend) |
| Config file | None -- Wave 0 must create pytest.ini / vitest.config.ts |
| Quick run command | `cd ../backend && uv run pytest -x -q` / `cd ../scripts && uv run pytest -x -q` / `cd ../frontend && npx vitest run --reporter=verbose` |
| Full suite command | `cd ../backend && uv run pytest` && `cd ../scripts && uv run pytest` && `cd ../frontend && npx vitest run` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCRP-01 | Migration creates all tables (exercises, programs, program_exercises, workouts, workout_sets) | integration | `cd ../scripts && uv run pytest tests/test_migrations.py -x` | No -- Wave 0 |
| SCRP-02 | Seed script populates exercise library with categorized exercises | integration | `cd ../scripts && uv run pytest tests/test_seed.py -x` | No -- Wave 0 |
| HEALTH | FastAPI health endpoint responds | smoke | `cd ../backend && uv run pytest tests/test_health.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** Quick run command for the affected repo
- **Per wave merge:** Full suite across all repos
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `../scripts/tests/conftest.py` -- shared fixtures (test DB engine, session)
- [ ] `../scripts/tests/test_migrations.py` -- covers SCRP-01
- [ ] `../scripts/tests/test_seed.py` -- covers SCRP-02
- [ ] `../backend/tests/conftest.py` -- test client, test DB
- [ ] `../backend/tests/test_health.py` -- covers health endpoint
- [ ] `../scripts/pyproject.toml` -- pytest dependency
- [ ] `../backend/pyproject.toml` -- pytest dependency
- [ ] `../frontend/vitest.config.ts` -- created by create-vue scaffolding

## Sources

### Primary (HIGH confidence)
- [FastAPI official tutorial on SQL databases](https://fastapi.tiangolo.com/tutorial/sql-databases/) -- session dependency, check_same_thread
- [Alembic batch migrations docs](https://alembic.sqlalchemy.org/en/latest/batch.html) -- render_as_batch, SQLite limitations
- [Alembic autogenerate docs](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) -- model import requirements
- [Tailwind CSS v4 Vite install guide](https://tailwindcss.com/docs/guides/vite) -- @tailwindcss/vite plugin, @import syntax
- [Vite server proxy options](https://vite.dev/config/server-options) -- proxy configuration
- [uv project guide](https://docs.astral.sh/uv/guides/projects/) -- uv init, uv add

### Secondary (MEDIUM confidence)
- [SQLAlchemy PyPI](https://pypi.org/project/SQLAlchemy) -- version 2.0.48 stable
- [FastAPI PyPI](https://pypi.org/project/fastapi/) -- version 0.135.x
- [Simon Willison WAL mode TIL](https://til.simonwillison.net/sqlite/enabling-wal-mode) -- SQLAlchemy WAL pragma pattern

### Tertiary (LOW confidence)
- None -- all findings verified with official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries are mature, well-documented, versions verified on PyPI
- Architecture: HIGH -- patterns from official docs (FastAPI SQL tutorial, Alembic batch docs, Vite proxy docs)
- Pitfalls: HIGH -- SQLite limitations well-documented in Alembic and SQLAlchemy official docs

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable stack, 30-day validity)
