# Phase 6: Integration Fixes and Polish - Research

**Researched:** 2026-03-07
**Domain:** Bug fixes / integration gaps (Python scripts, Vue frontend)
**Confidence:** HIGH

## Summary

Phase 6 closes three specific integration gaps identified by the v1.0 milestone audit. All three issues are well-scoped, clearly understood, and involve small, targeted changes to existing code. No new libraries, patterns, or architecture decisions are needed.

**Issue 1 (INT-01): Import FK mapping for program_id.** The `importer.py` builds an `exercise_id_map` to remap exercise foreign keys after re-insertion (since new IDs are assigned), but fails to do the same for `program_id` on workouts. Line 124 simply copies the old `program_id` verbatim: `workout.program_id = w["program_id"]`. Since programs are deleted and re-inserted with new auto-increment IDs, the old program_id will reference a non-existent (or wrong) program. The fix is to build a `program_id_map` (analogous to `exercise_id_map`) during program insertion and use it when setting `workout.program_id`.

**Issue 2 (INT-02): Missing rest_timer_disabled toggle in program builder UI.** The backend fully supports `rest_timer_disabled` on programs (model, create/update schemas, API routes all handle it). The frontend `ActiveWorkout.vue` reads it correctly to suppress the rest timer. However, `ProgramEditView.vue` has no UI to set this field, and `ProgramCreatePayload` in `programs.ts` store does not include the field. The fix is to add a checkbox/toggle to the program builder form, add the field to the store payload type, and include it in `buildPayload()`.

**Issue 3: datetime.utcnow() deprecation.** Python 3.12+ deprecated `datetime.utcnow()` in favor of `datetime.now(timezone.utc)`. The scripts codebase has one production usage in `queries.py:64` and three test usages in `test_analytics.py` and `conftest.py`. The backend codebase has no occurrences. The fix is a simple find-and-replace.

**Primary recommendation:** All three fixes are small, independent changes that can be grouped into a single plan with three tasks (one per fix).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCRP-04 | Export/import scripts for JSON/CSV data backup | Fix 1: Import program_id remapping ensures round-trip data integrity |
| LOG-04 | User sees a rest timer that auto-starts after logging a set (configurable duration) | Fix 2: UI toggle for rest_timer_disabled makes the feature fully configurable per-program |
</phase_requirements>

## Standard Stack

No new libraries needed. All fixes use the existing stack:

### Core (already installed)
| Library | Version | Purpose | Repo |
|---------|---------|---------|------|
| SQLAlchemy | 2.0.x | ORM models and session operations | scripts |
| Vue 3 | 3.x | Frontend UI components | frontend |
| Pydantic | 2.x | Backend API schemas (already supports rest_timer_disabled) | backend |

### No Additions Required
All three fixes modify existing files with existing imports. No `npm install` or `uv add` needed.

## Architecture Patterns

### Pattern 1: FK ID Remapping on Import
**What:** When re-inserting entities with auto-increment PKs, build an `old_id -> new_id` map and apply it to all FK references.
**Already used for:** `exercise_id_map` in `importer.py` lines 68-78
**Must extend to:** `program_id_map` for workout.program_id

**Current pattern (exercises):**
```python
# importer.py lines 68-78 -- existing working pattern
exercise_id_map = {}
for e in data.get("exercises", []):
    ex = Exercise(name=e["name"], ...)
    session.add(ex)
    session.flush()  # triggers auto-increment, assigns ex.id
    exercise_id_map[e["id"]] = ex.id
```

**Must replicate for programs:**
```python
program_id_map = {}
for p in data.get("programs", []):
    prog = Program(name=p["name"], ...)
    session.add(prog)
    session.flush()
    program_id_map[p["id"]] = prog.id
    # ... existing nested exercise/set insertion
```

Then at workout insertion (currently line 124):
```python
# BEFORE (broken):
workout.program_id = w["program_id"]

# AFTER (fixed):
workout.program_id = program_id_map.get(w["program_id"], w["program_id"])
```

### Pattern 2: Program Builder Form Field + Store Payload
**What:** Adding a new field to the program builder follows the existing pattern: ref in component, v-model in template, include in payload, include in type.
**Existing pattern:** The `programName` ref is bound via v-model, included in `buildPayload()`, and the `ProgramCreatePayload` type defines the shape sent to the API.

**Must add:**
1. `programs.ts`: Add `rest_timer_disabled?: boolean` to `ProgramCreatePayload`
2. `ProgramEditView.vue`: Add `const restTimerDisabled = ref(false)`, load from program in edit mode, include in `buildPayload()`, add toggle UI

### Pattern 3: datetime.utcnow() Replacement
**What:** Replace deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`
**Scope:** 4 occurrences across 3 files in scripts repo only

**Replacement:**
```python
# BEFORE:
from datetime import datetime
datetime.utcnow()

# AFTER:
from datetime import datetime, timezone
datetime.now(timezone.utc)
```

Note: `conftest.py` and `test_analytics.py` use naive datetimes for test data. Since SQLite stores datetimes as strings and the app uses naive datetimes throughout (no timezone-aware comparison), test fixtures should use `datetime.now(timezone.utc).replace(tzinfo=None)` to avoid mixing aware and naive datetimes, OR simply use `datetime.now(tz=None)` / `datetime.utcnow()` alternative. The cleanest approach: use `datetime.now(timezone.utc)` everywhere and ensure the comparison in `_cutoff_date` matches what the database stores. Since the production code in `queries.py` only uses the cutoff for `>=` comparison with `Workout.started_at` (which is stored as naive UTC in SQLite), the safest fix is:
- Production: `datetime.now(timezone.utc).replace(tzinfo=None)` to stay consistent with naive storage
- Tests: Same pattern

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FK remapping | Custom tracking logic | Dict map (already used for exercises) | Proven pattern in same file |
| Toggle UI | Custom toggle component | HTML checkbox with Tailwind styling (already used for is_warmup) | Consistent with existing UI |

## Common Pitfalls

### Pitfall 1: Timezone-Aware vs Naive Datetime Mismatch
**What goes wrong:** Replacing `datetime.utcnow()` (returns naive) with `datetime.now(timezone.utc)` (returns aware) can break SQLAlchemy comparisons if existing stored datetimes are naive.
**Why it happens:** SQLite stores datetimes as ISO strings without timezone info. Comparing an aware datetime to a naive one raises a TypeError in Python.
**How to avoid:** Use `datetime.now(timezone.utc).replace(tzinfo=None)` to get a naive UTC datetime, maintaining consistency with existing storage. OR use `datetime.now(timezone.utc)` and ensure all comparisons are timezone-consistent.
**Recommendation:** Use `datetime.now(timezone.utc)` in production code. SQLAlchemy 2.0 handles the comparison correctly when filtering against SQLite columns. The test fixtures should also switch to timezone-aware for consistency.

### Pitfall 2: program_id_map Must Be Built Before Workouts
**What goes wrong:** If program_id_map is referenced before programs are inserted, the map will be empty and workouts will get null program_ids.
**How to avoid:** The existing code already inserts in order (exercises, programs, workouts). Just build the map during program insertion, before the workout loop.

### Pitfall 3: ProgramEditView Must Load rest_timer_disabled in Edit Mode
**What goes wrong:** Adding the toggle but not loading the existing value in edit mode means editing a program always resets rest_timer_disabled to false.
**How to avoid:** In the `onMounted` edit-mode branch (line 151), set `restTimerDisabled.value = program.rest_timer_disabled` alongside `programName.value = program.name`.

## Code Examples

### Fix 1: Import Program ID Remapping

```python
# In importer.py, modify the programs loop to build a map:
program_id_map = {}
for p in data.get("programs", []):
    prog = Program(
        name=p["name"],
        rest_timer_disabled=p.get("rest_timer_disabled", False),
    )
    session.add(prog)
    session.flush()
    program_id_map[p["id"]] = prog.id  # NEW: track old->new ID
    counts["programs"] += 1
    # ... existing nested exercise/set insertion (unchanged)

# In the workouts loop, use the map:
if w.get("program_id") is not None:
    workout.program_id = program_id_map.get(w["program_id"])  # NEW: remap
```

### Fix 2: Rest Timer Disabled Toggle in Program Builder

```vue
<!-- In ProgramEditView.vue, after program name input -->
<label class="flex items-center gap-2 cursor-pointer">
  <input
    v-model="restTimerDisabled"
    type="checkbox"
    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
  />
  <span class="text-sm text-gray-700">Disable rest timer for this program</span>
</label>
```

```typescript
// In programs.ts ProgramCreatePayload:
export interface ProgramCreatePayload {
  name: string
  rest_timer_disabled?: boolean
  exercises: { /* ... existing */ }[]
}
```

### Fix 3: datetime Deprecation Fix

```python
# queries.py line 64
# BEFORE:
return datetime.utcnow() - timedelta(days=period_days)
# AFTER:
from datetime import datetime, timedelta, timezone
return datetime.now(timezone.utc) - timedelta(days=period_days)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Python 3.12 (Oct 2023) | DeprecationWarning in 3.12+, removal planned for 3.14 |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | scripts/pyproject.toml (implicit) |
| Quick run command | `cd ../scripts && uv run pytest tests/test_export_import.py -x` |
| Full suite command | `cd ../scripts && uv run pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCRP-04 | Import remaps program_id so workout-to-program links survive round-trip | unit | `cd ../scripts && uv run pytest tests/test_export_import.py::TestImportData::test_round_trip_preserves_program_links -x` | No -- Wave 0 |
| LOG-04 | rest_timer_disabled toggle visible and functional in program builder | manual-only | Visual check in browser | N/A |
| N/A | No datetime.utcnow() deprecation warnings | unit | `cd ../scripts && uv run python -W error::DeprecationWarning -m pytest tests/ -x` | Existing tests cover (just need the fix) |

### Sampling Rate
- **Per task commit:** `cd ../scripts && uv run pytest tests/test_export_import.py -x`
- **Per wave merge:** `cd ../scripts && uv run pytest`
- **Phase gate:** Full suite green + no deprecation warnings

### Wave 0 Gaps
- [ ] `tests/test_export_import.py::TestImportData::test_round_trip_preserves_program_links` -- test that imported workouts reference the correct re-inserted program (not the old program_id)
- No framework install needed (pytest already configured and working)

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection of `scripts/gymcoach_scripts/export_import/importer.py` -- confirmed FK mapping bug at line 124
- Direct codebase inspection of `frontend/src/views/ProgramEditView.vue` -- confirmed no rest_timer_disabled UI
- Direct codebase inspection of `frontend/src/stores/programs.ts` -- confirmed ProgramCreatePayload missing field
- Direct codebase inspection of `backend/app/programs/schemas.py` -- confirmed API already accepts rest_timer_disabled
- `grep datetime.utcnow` across scripts/ -- 4 occurrences in 3 files

### Secondary (MEDIUM confidence)
- Python 3.12 changelog for datetime.utcnow() deprecation (well-documented, widely known)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries, all existing
- Architecture: HIGH - all fixes follow existing patterns already in the codebase
- Pitfalls: HIGH - issues are clearly scoped with obvious solutions

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable, no external dependencies)
