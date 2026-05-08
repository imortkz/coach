# Phase 5: Analytics and Data Tools - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

CLI analytics commands for progress reports (estimated 1RM trends, volume per muscle group, workout frequency) and data export/import for backup. Covers SCRP-03, SCRP-04. All commands live in the scripts/ repo using the existing Click CLI. No web UI analytics — this is CLI-only.

</domain>

<decisions>
## Implementation Decisions

### Analytics output style
- Rich tables with color for human-readable output (Rich library)
- `--json` flag on all analytics subcommands for machine-readable structured output
- Respect user's weight_unit setting from settings table for display (data stays in kg internally)

### CLI command structure
- Analytics as subcommand group: `gymcoach analytics 1rm`, `gymcoach analytics volume`, `gymcoach analytics frequency`
- Export/import as top-level commands: `gymcoach export`, `gymcoach import`
- Consistent flag naming across subcommands

### 1RM calculation
- Epley formula: 1RM = weight x (1 + reps/30)
- Default view: all exercises with data in a table showing current estimated 1RM, best ever 1RM, and trend direction (up/down/flat)
- `--exercise "Name"` flag to zoom into a single exercise

### Volume report
- Default view: by muscle group (total sets, total volume in kg, percentage of total)
- `--by-exercise` flag for per-exercise breakdown
- Volume = sets x reps x weight

### Frequency report
- Weekly breakdown: workouts per week over the period with programs used
- Shows average workouts/week at bottom

### Export format
- JSON: nested by entity (exercises, programs with nested sets, workouts with nested sets, settings) in one file
- CSV: workout log only (date, exercise, muscle_group, set_number, weight_kg, reps, is_warmup, program)
- `--format json|csv` flag, `-o` for output path
- Export always includes all data (no date filtering)

### Import behavior
- JSON import only (CSV is log-only, not suitable for full restore)
- Replace-all strategy: import replaces all existing data
- Auto-creates backup export before replacing (backup-{timestamp}.json)
- Interactive confirmation prompt before proceeding
- Reports count of imported entities on completion

### Filtering and date ranges
- Default lookback: 90 days for all analytics commands
- `--period` shorthand: 30d, 12w, 6m, all (days, weeks, months, all-time)
- `--exercise "Name"` and `--muscle-group "Name"` flags where relevant
- No date filtering on export (always full data)

### Claude's Discretion
- Rich table styling details (colors, borders, alignment)
- Trend calculation logic (how many sessions to compare for up/down/flat)
- Exercises with insufficient data handling (minimum sessions threshold)
- JSON export field naming and exact nesting structure
- CSV column ordering
- Backup file naming format
- Error messages and edge case handling

</decisions>

<specifics>
## Specific Ideas

- Separate subcommands keep each report focused and discoverable (`gymcoach analytics --help` lists all)
- `--json` flag enables scripting and piping to jq or other tools
- Nested JSON export mirrors the data model — readable and self-contained for backup
- CSV export is log-only because that's what's useful for spreadsheet analysis (programs are metadata)
- Import auto-backup prevents accidental data loss — user always has a way back

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli.py`: Click group with `migrate` and `seed` commands — add `analytics`, `export`, `import` commands here
- `db/models.py`: Full SQLAlchemy model set (Exercise, Program, ProgramExercise, ProgramSet, Workout, WorkoutSet, Setting)
- `db/engine.py`: SessionLocal factory, GYMCOACH_DB env var support, WAL mode + FK enforcement
- Rich library available in Python ecosystem (add to dependencies)

### Established Patterns
- Click CLI with `@click.group()` and `cli.add_command()` pattern
- SQLAlchemy 2.0 mapped columns with type annotations
- GYMCOACH_DB env var for database path
- uv for package management

### Integration Points
- Settings table for weight_unit preference and progression increment defaults
- All models accessible via `db.models` and `db.engine.SessionLocal`
- Exercise.muscle_group and Exercise.equipment fields for grouping/filtering
- Workout.completed_at for date filtering, Workout.program_id for program association
- WorkoutSet.weight_kg, .reps, .is_warmup for analytics calculations

</code_context>

<deferred>
## Deferred Ideas

- PDF export of analytics reports — separate feature, adds significant dependency (report generation library)

</deferred>

---

*Phase: 05-analytics-and-data-tools*
*Context gathered: 2026-03-07*
