# Phase 5: Analytics and Data Tools - Research

**Researched:** 2026-03-07
**Domain:** CLI analytics, data export/import (Python Click + Rich + SQLAlchemy)
**Confidence:** HIGH

## Summary

Phase 5 adds CLI commands to the existing scripts/ repo for analytics reports (1RM trends, volume per muscle group, workout frequency) and data export/import (JSON/CSV). All infrastructure is already in place: Click CLI group, SQLAlchemy models, Rich console, and the session factory. The work is purely additive -- new Click commands and supporting logic modules.

The domain is well-understood: SQLAlchemy queries against the existing schema, Rich table formatting for output, standard JSON/CSV serialization for export/import. No new dependencies are needed (Rich and Click are already installed). The main complexity lies in correct SQL queries for analytics aggregation and robust import with transactional safety.

**Primary recommendation:** Organize as separate modules (analytics.py, export_import.py) with pure-function query logic separated from Click command definitions for testability.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Rich tables with color for human-readable output; `--json` flag on all analytics subcommands
- Respect weight_unit setting from settings table for display (data stays in kg internally)
- Analytics as subcommand group: `gymcoach analytics 1rm`, `gymcoach analytics volume`, `gymcoach analytics frequency`
- Export/import as top-level commands: `gymcoach export`, `gymcoach import`
- 1RM uses Epley formula: 1RM = weight x (1 + reps/30)
- Default view for 1RM: all exercises with current estimated 1RM, best ever 1RM, trend direction
- `--exercise "Name"` flag to zoom into single exercise
- Volume report: by muscle group (total sets, total volume in kg, percentage of total), `--by-exercise` flag
- Volume = sets x reps x weight
- Frequency report: weekly breakdown with programs used, average workouts/week
- JSON export: nested by entity (exercises, programs with nested sets, workouts with nested sets, settings)
- CSV export: workout log only (date, exercise, muscle_group, set_number, weight_kg, reps, is_warmup, program)
- `--format json|csv` flag, `-o` for output path
- Export always includes all data (no date filtering)
- JSON import only (CSV is log-only)
- Replace-all strategy with auto-backup before replacing
- Interactive confirmation prompt before import
- Reports count of imported entities on completion
- Default lookback: 90 days; `--period` shorthand: 30d, 12w, 6m, all
- `--exercise "Name"` and `--muscle-group "Name"` flags where relevant

### Claude's Discretion
- Rich table styling details (colors, borders, alignment)
- Trend calculation logic (how many sessions to compare for up/down/flat)
- Exercises with insufficient data handling (minimum sessions threshold)
- JSON export field naming and exact nesting structure
- CSV column ordering
- Backup file naming format
- Error messages and edge case handling

### Deferred Ideas (OUT OF SCOPE)
- PDF export of analytics reports
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCRP-03 | CLI analytics show 1RM trends, volume per muscle group, workout frequency | Analytics subcommand group with three reports, Rich table output, --json flag, period filtering |
| SCRP-04 | Export/import scripts for JSON/CSV data backup | Top-level export/import commands, JSON nested export, CSV log export, JSON-only import with replace-all strategy |
</phase_requirements>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | >=8.3.1 | CLI framework | Already used for migrate/seed commands |
| rich | >=14.3.3 | Terminal tables and color output | Already a dependency, used in seed.py |
| sqlalchemy | >=2.0.48 | Database ORM and queries | Already used for all data access |

### Supporting (Already Available)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | - | JSON serialization/deserialization | Export/import JSON format |
| csv (stdlib) | - | CSV writing | Export CSV format |
| datetime (stdlib) | - | Date arithmetic for period filtering | All analytics date ranges |

### No New Dependencies Required
All required libraries are already in pyproject.toml. No `uv add` needed.

## Architecture Patterns

### Recommended Project Structure
```
gymcoach_scripts/
  cli.py                  # Add analytics group, export, import commands
  analytics/
    __init__.py
    queries.py            # Pure functions: get_1rm_data(), get_volume_data(), get_frequency_data()
    formatters.py         # Rich table builders + JSON output formatters
    commands.py           # Click commands: 1rm, volume, frequency
  export_import/
    __init__.py
    exporter.py           # Pure functions: export_json(), export_csv()
    importer.py           # Pure functions: import_json(), create_backup()
    commands.py           # Click commands: export, import
```

### Pattern 1: Separate Query Logic from CLI Plumbing
**What:** Keep SQLAlchemy queries in pure functions that accept a session and return data. Click commands handle CLI concerns (parsing args, creating session, calling formatter).
**When to use:** Every command.
**Why:** Enables testing query logic with in-memory SQLite (existing conftest.py pattern) without invoking Click.

```python
# queries.py - pure function, testable
def get_1rm_data(session, period_days: int | None = 90, exercise_name: str | None = None) -> list[dict]:
    """Return 1RM estimates per exercise within the period."""
    # SQLAlchemy query logic here
    ...

# commands.py - thin CLI wrapper
@click.command("1rm")
@click.option("--period", default="90d", help="Lookback period")
@click.option("--exercise", default=None, help="Filter to specific exercise")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def cmd_1rm(period, exercise, as_json):
    session = SessionLocal()
    try:
        data = get_1rm_data(session, parse_period(period), exercise)
        if as_json:
            click.echo(json.dumps(data, indent=2))
        else:
            print_1rm_table(data)
    finally:
        session.close()
```

### Pattern 2: Click Group Nesting
**What:** Analytics as a sub-group of the main CLI group.
**When to use:** For the analytics subcommand hierarchy.

```python
# cli.py
from gymcoach_scripts.analytics.commands import analytics
from gymcoach_scripts.export_import.commands import export_cmd, import_cmd

cli.add_command(analytics)
cli.add_command(export_cmd, "export")
cli.add_command(import_cmd, "import")

# analytics/commands.py
@click.group()
def analytics():
    """View workout analytics and progress reports."""
    pass

analytics.add_command(cmd_1rm, "1rm")
analytics.add_command(cmd_volume, "volume")
analytics.add_command(cmd_frequency, "frequency")
```

### Pattern 3: Period Parsing Utility
**What:** Parse `--period` shorthand (30d, 12w, 6m, all) into days or None.
**When to use:** All analytics commands share this.

```python
def parse_period(period_str: str) -> int | None:
    """Parse period string to number of days. Returns None for 'all'."""
    if period_str == "all":
        return None
    value = int(period_str[:-1])
    unit = period_str[-1]
    if unit == "d":
        return value
    elif unit == "w":
        return value * 7
    elif unit == "m":
        return value * 30
    else:
        raise click.BadParameter(f"Invalid period: {period_str}. Use Nd, Nw, Nm, or 'all'.")
```

### Pattern 4: Weight Unit Conversion for Display
**What:** Read weight_unit from settings, convert kg to lb for display only.
**When to use:** All analytics output and CSV export.

```python
def get_weight_unit(session) -> str:
    setting = session.query(Setting).filter_by(key="weight_unit").first()
    return setting.value if setting else "kg"

def convert_weight(weight_kg: float, unit: str) -> float:
    if unit == "lb":
        return round(weight_kg * 2.20462, 1)
    return weight_kg
```

### Pattern 5: Transactional Import with Auto-Backup
**What:** Export current data as backup, then replace all data in a transaction.
**When to use:** Import command.

```python
def import_data(session, data: dict, backup_path: Path) -> dict[str, int]:
    """Import JSON data, replacing all existing data. Returns entity counts."""
    # 1. Create backup first
    backup_data = export_all_json(session)
    backup_path.write_text(json.dumps(backup_data, indent=2))

    # 2. Delete all existing data (order matters for FK constraints)
    session.query(WorkoutSet).delete()
    session.query(Workout).delete()
    session.query(ProgramSet).delete()
    session.query(ProgramExercise).delete()
    session.query(Program).delete()
    session.query(Exercise).delete()
    session.query(Setting).delete()

    # 3. Insert imported data
    counts = {}
    # ... insert in dependency order: exercises, programs, program_exercises, etc.

    session.commit()
    return counts
```

### Anti-Patterns to Avoid
- **Loading all workout sets into Python for aggregation:** Use SQL GROUP BY and aggregate functions (SUM, COUNT) where possible. Only pull individual sets when per-set calculations (like 1RM) are needed.
- **Hard-coding weight unit:** Always read from settings table.
- **Importing CSV:** CSV is log-only and lacks the structure for full restore. JSON-only import is the correct decision.
- **Skipping FK order on delete/insert during import:** SQLite enforces FKs (PRAGMA foreign_keys=ON). Must delete children first, insert parents first.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Terminal tables | Custom print formatting | `rich.table.Table` | Handles column width, alignment, color, Unicode borders |
| CSV writing | Manual string concatenation | `csv.writer` / `csv.DictWriter` | Handles quoting, escaping, newlines correctly |
| JSON serialization | Manual string building | `json.dumps` with custom encoder | Handles datetime, float precision, Unicode |
| Date arithmetic | Manual day counting | `datetime.timedelta` | Handles month boundaries, leap years |
| CLI argument parsing | Manual sys.argv | Click decorators | Validation, help text, type conversion |
| Confirmation prompts | Manual input() | `click.confirm()` | Handles yes/no, abort, default |

## Common Pitfalls

### Pitfall 1: Datetime Handling in SQLite
**What goes wrong:** SQLite stores datetimes as strings. Comparisons fail if format is inconsistent.
**Why it happens:** SQLAlchemy's DateTime type uses ISO format strings in SQLite.
**How to avoid:** Use SQLAlchemy's column comparison operators (e.g., `Workout.completed_at >= cutoff_date`) which handle serialization. When constructing cutoff dates, use Python `datetime.now() - timedelta(days=N)`.
**Warning signs:** Empty results when data exists, or queries returning unexpected rows.

### Pitfall 2: Division by Zero in Analytics
**What goes wrong:** Volume percentage or average calculations crash with no data.
**Why it happens:** Empty workout history, filtered period with no workouts, or exercises with 0 reps logged.
**How to avoid:** Guard all divisions. Return "No data" message for empty result sets. The Epley formula with reps=0 gives weight x 1.0 which is fine, but check for None weight.
**Warning signs:** ZeroDivisionError in frequency (0 weeks) or volume percentage (0 total volume).

### Pitfall 3: Warmup Sets in Analytics
**What goes wrong:** Including warmup sets inflates volume and skews 1RM estimates.
**Why it happens:** Forgetting to filter `is_warmup=False` in queries.
**How to avoid:** Always add `WorkoutSet.is_warmup == False` to analytics queries. Warmup sets should be excluded from 1RM, volume, and frequency calculations.
**Warning signs:** Unrealistically high volume numbers, 1RM lower than expected (warmup sets have lower weight).

### Pitfall 4: Foreign Key Order During Import
**What goes wrong:** Import fails with FK constraint violation.
**Why it happens:** Trying to delete exercises before workout_sets that reference them, or inserting workouts before exercises.
**How to avoid:** Delete order: workout_sets -> workouts -> program_sets -> program_exercises -> programs -> exercises -> settings. Insert in reverse order.
**Warning signs:** IntegrityError on delete or insert.

### Pitfall 5: Null Weight/Reps in Calculations
**What goes wrong:** TypeError when multiplying None by a number.
**Why it happens:** WorkoutSet.weight_kg and .reps are nullable (bodyweight exercises, incomplete sets).
**How to avoid:** Filter out sets where weight_kg is None or reps is None for 1RM and volume calculations. Or default to 0 for bodyweight.
**Warning signs:** TypeError in arithmetic operations.

### Pitfall 6: Period Boundary Edge Cases
**What goes wrong:** Off-by-one in date filtering, or "12w" giving unexpected date range.
**Why it happens:** Ambiguity in whether boundary date is inclusive.
**How to avoid:** Use `>=` for the cutoff date (inclusive start). Calculate cutoff as `datetime.now() - timedelta(days=N)`.

## Code Examples

### Rich Table Output
```python
from rich.console import Console
from rich.table import Table

console = Console()

def print_1rm_table(data: list[dict], weight_unit: str):
    table = Table(title="Estimated 1RM", show_header=True, header_style="bold cyan")
    table.add_column("Exercise", style="white")
    table.add_column(f"Current 1RM ({weight_unit})", justify="right", style="green")
    table.add_column(f"Best 1RM ({weight_unit})", justify="right", style="yellow")
    table.add_column("Trend", justify="center")

    trend_symbols = {"up": "[green]^[/green]", "down": "[red]v[/red]", "flat": "[dim]-[/dim]"}

    for row in data:
        table.add_row(
            row["exercise"],
            f"{row['current_1rm']:.1f}",
            f"{row['best_1rm']:.1f}",
            trend_symbols.get(row["trend"], "-"),
        )

    console.print(table)
```

### SQLAlchemy Analytics Query (Volume by Muscle Group)
```python
from sqlalchemy import func
from gymcoach_scripts.db.models import WorkoutSet, Exercise, Workout

def get_volume_by_muscle_group(session, cutoff_date=None) -> list[dict]:
    query = (
        session.query(
            Exercise.muscle_group,
            func.count(WorkoutSet.id).label("total_sets"),
            func.sum(WorkoutSet.weight_kg * WorkoutSet.reps).label("total_volume"),
        )
        .join(Exercise, WorkoutSet.exercise_id == Exercise.id)
        .join(Workout, WorkoutSet.workout_id == Workout.id)
        .filter(WorkoutSet.is_warmup == False)  # noqa: E712
        .filter(WorkoutSet.weight_kg.isnot(None))
        .filter(WorkoutSet.reps.isnot(None))
    )
    if cutoff_date:
        query = query.filter(Workout.completed_at >= cutoff_date)

    results = query.group_by(Exercise.muscle_group).all()

    total = sum(r.total_volume or 0 for r in results)
    return [
        {
            "muscle_group": r.muscle_group,
            "total_sets": r.total_sets,
            "total_volume_kg": r.total_volume or 0,
            "percentage": round((r.total_volume or 0) / total * 100, 1) if total > 0 else 0,
        }
        for r in results
    ]
```

### JSON Export Structure
```python
def export_all_json(session) -> dict:
    """Export all data as nested JSON structure."""
    exercises = session.query(Exercise).all()
    programs = session.query(Program).all()
    workouts = session.query(Workout).all()
    settings = session.query(Setting).all()

    return {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "exercises": [
            {"id": e.id, "name": e.name, "muscle_group": e.muscle_group,
             "equipment": e.equipment, "is_custom": e.is_custom}
            for e in exercises
        ],
        "programs": [
            {
                "id": p.id, "name": p.name, "created_at": p.created_at.isoformat(),
                "rest_timer_disabled": p.rest_timer_disabled,
                "exercises": [
                    {
                        "id": pe.id, "exercise_id": pe.exercise_id, "order": pe.order,
                        "sets": [
                            {"set_number": s.set_number, "target_reps": s.target_reps,
                             "target_weight_kg": s.target_weight_kg, "is_warmup": s.is_warmup}
                            for s in pe.sets
                        ]
                    }
                    for pe in p.exercises
                ]
            }
            for p in programs
        ],
        "workouts": [
            {
                "id": w.id, "program_id": w.program_id,
                "started_at": w.started_at.isoformat(),
                "completed_at": w.completed_at.isoformat() if w.completed_at else None,
                "sets": [
                    {"exercise_id": s.exercise_id, "set_number": s.set_number,
                     "weight_kg": s.weight_kg, "reps": s.reps, "is_warmup": s.is_warmup}
                    for s in w.sets
                ]
            }
            for w in workouts
        ],
        "settings": [{"key": s.key, "value": s.value} for s in settings],
    }
```

### Click Confirmation for Import
```python
@click.command("import")
@click.argument("file", type=click.Path(exists=True))
def import_cmd(file):
    """Import data from a JSON backup file. Replaces all existing data."""
    data = json.loads(Path(file).read_text())

    # Show what will be imported
    console.print(f"[bold]Import summary:[/bold]")
    console.print(f"  Exercises: {len(data.get('exercises', []))}")
    console.print(f"  Programs:  {len(data.get('programs', []))}")
    console.print(f"  Workouts:  {len(data.get('workouts', []))}")
    console.print(f"  Settings:  {len(data.get('settings', []))}")
    console.print()
    console.print("[bold red]WARNING: This will replace ALL existing data.[/bold red]")

    if not click.confirm("Continue?"):
        raise SystemExit("Aborted.")

    session = SessionLocal()
    try:
        backup_path = Path(f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
        counts = import_data(session, data, backup_path)
        console.print(f"[bold green]Import complete.[/bold green] Backup saved to {backup_path}")
    finally:
        session.close()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `print()` with ANSI codes | `rich.table.Table` + `Console` | Rich 10+ (2020+) | Automatic column sizing, color, borders |
| `@click.group()` only | Nested groups with `add_command` | Click 7+ | Clean subcommand hierarchies |
| SQLAlchemy 1.x Query API | SQLAlchemy 2.0 `select()` / `session.query()` | SA 2.0 (2023) | Both patterns work; project uses `session.query()` consistently |

**Note:** The project already uses `session.query()` style (legacy query API in SQLAlchemy 2.0). Continue using this pattern for consistency rather than switching to `select()` style mid-project.

## Open Questions

1. **Trend calculation window**
   - What we know: Need up/down/flat indicator for 1RM
   - Recommendation: Compare last 3 sessions' average 1RM to previous 3 sessions. If <2% change = flat, higher = up, lower = down. Require minimum 2 sessions for any trend (otherwise show "-").

2. **Minimum data threshold for 1RM**
   - What we know: Exercises with only 1 set ever shouldn't show misleading trends
   - Recommendation: Require at least 2 sessions with non-warmup sets to show 1RM. Show "insufficient data" for exercises below threshold.

3. **Export file default location**
   - What we know: `-o` flag specified for output path
   - Recommendation: Default to current working directory with filename `gymcoach-export-{date}.{format}`.

4. **Incomplete workouts in analytics**
   - What we know: Workouts have completed_at which can be None
   - Recommendation: Include all workouts with at least one logged set in analytics, regardless of completed_at. For frequency, only count workouts where completed_at is not None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=9.0.2 |
| Config file | None (pytest auto-discovers in tests/) |
| Quick run command | `cd ../scripts && uv run pytest tests/ -x -q` |
| Full suite command | `cd ../scripts && uv run pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCRP-03a | 1RM calculation returns correct Epley values | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_1rm_calculation -x` | No - Wave 0 |
| SCRP-03b | Volume aggregation by muscle group | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_volume_by_muscle_group -x` | No - Wave 0 |
| SCRP-03c | Frequency weekly breakdown | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_frequency_report -x` | No - Wave 0 |
| SCRP-03d | Period filtering (30d, 12w, 6m, all) | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_period_parsing -x` | No - Wave 0 |
| SCRP-03e | Warmup sets excluded from analytics | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_warmup_exclusion -x` | No - Wave 0 |
| SCRP-03f | Weight unit conversion in display | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_weight_unit_conversion -x` | No - Wave 0 |
| SCRP-04a | JSON export contains all entities | unit | `cd ../scripts && uv run pytest tests/test_export_import.py::test_json_export -x` | No - Wave 0 |
| SCRP-04b | CSV export contains workout log rows | unit | `cd ../scripts && uv run pytest tests/test_export_import.py::test_csv_export -x` | No - Wave 0 |
| SCRP-04c | JSON import replaces all data | unit | `cd ../scripts && uv run pytest tests/test_export_import.py::test_json_import -x` | No - Wave 0 |
| SCRP-04d | Import creates backup before replacing | unit | `cd ../scripts && uv run pytest tests/test_export_import.py::test_import_creates_backup -x` | No - Wave 0 |
| SCRP-04e | Round-trip: export then import preserves data | integration | `cd ../scripts && uv run pytest tests/test_export_import.py::test_roundtrip -x` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `cd ../scripts && uv run pytest tests/ -x -q`
- **Per wave merge:** `cd ../scripts && uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_analytics.py` -- covers SCRP-03 (1RM, volume, frequency query logic)
- [ ] `tests/test_export_import.py` -- covers SCRP-04 (export formats, import with backup)
- [ ] Test fixtures: add workout/exercise seed data helpers to `tests/conftest.py`

## Sources

### Primary (HIGH confidence)
- Existing codebase: `scripts/gymcoach_scripts/` -- CLI structure, models, engine, seed pattern
- Existing codebase: `scripts/pyproject.toml` -- confirmed Rich >=14.3.3, Click >=8.3.1, SQLAlchemy >=2.0.48 already installed
- Existing codebase: `scripts/tests/conftest.py` -- in-memory SQLite test pattern

### Secondary (MEDIUM confidence)
- Rich library table API -- well-documented, Console and Table classes used in existing seed.py
- Click nested groups -- standard Click pattern, well-documented

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already installed and in use
- Architecture: HIGH - follows existing patterns in the codebase
- Pitfalls: HIGH - derived from concrete model analysis (nullable fields, FK constraints, warmup flag)

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable domain, no moving parts)
