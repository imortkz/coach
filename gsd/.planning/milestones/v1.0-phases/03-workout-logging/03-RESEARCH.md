# Phase 3: Workout Logging - Research

**Researched:** 2026-03-06
**Domain:** Workout session management (FastAPI + Vue 3 + SQLite), real-time timer, touch-first UX
**Confidence:** HIGH

## Summary

Phase 3 builds the core gym-floor experience: starting a workout from a program template, logging sets with pre-filled values, editing/deleting logged data, and a floating rest timer. The existing codebase provides strong foundations -- `Workout`, `WorkoutSet`, and `Setting` SQLAlchemy models already exist, frontend types are defined, and the `/workout` route stub is in place. No schema migration is needed for core logging; the `settings` table can store `rest_timer_seconds`.

The backend work follows the established domain-grouped pattern (add `routes.py` to `app/workouts/`, register router in `main.py`). The key complexity is the "last session pre-fill" query (finding the most recent completed workout containing each exercise and returning its actual weight/reps). The frontend work is substantial: a multi-screen workout flow (program picker, active workout with set logging, summary), a floating rest timer with browser notifications, swipe/tap interactions, and undo toast for destructive actions.

**Primary recommendation:** Structure this phase as backend API first (workout CRUD + pre-fill endpoint + settings), then core workout UI (picker + set logging), then timer and edit/delete interactions. Keep all workout state server-side -- auto-save on each set log, resume on page reload via "active workout" detection.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Landing on /workout shows a program picker -- tap a program to start a session with its exercises pre-loaded
- Active workout shows a scrollable list of all exercises with their sets -- user can jump to any exercise and log sets in any order
- Workout state auto-saves to the server as sets are logged -- returning to /workout resumes the active session (survives browser close)
- Explicit "Finish Workout" button -- tapping it shows a quick summary (exercises done, total sets, duration) before confirming to save and set completed_at
- Tap-to-complete interaction: each set row shows pre-filled weight/reps -- tap the row or a checkmark to log it as-is; tap weight/reps fields to edit before completing
- Pre-fill values from last session's actuals for this exercise (most recent completed workout with that exercise_id). If no prior session exists, fall back to program targets
- Warmup sets shown with a subtle "W" badge and lighter text/background -- clearly secondary but still loggable
- "+Add Set" button below the last set for each exercise -- allows adding extra sets beyond program definition during a workout
- Floating countdown bar positioned above the mobile tab bar -- always visible while scrolling through exercises
- Auto-starts after logging a set
- Default duration: 120 seconds, stored in settings table (user-configurable)
- Per-program option to disable the rest timer entirely
- Browser notification when rest period completes (requires notification permission)
- Skip button on the floating bar to dismiss/end rest early
- Editing a logged set: tap the set row on desktop, swipe left on mobile to reveal edit/delete actions -- adaptive interaction based on viewport
- Deleting a single logged set: delete immediately, show bottom undo toast (5-10s timeout) before permanent deletion
- Removing an exercise from active workout: swipe or menu action on exercise header, confirmation required, removes exercise and all its logged sets
- Discarding entire workout: button in workout header (desktop) or right swipe (mobile), with bottom undo toast (5-10s timeout) before permanent deletion

### Claude's Discretion
- Exact layout spacing, typography, and color within the minimal aesthetic (Linear/Notion style from Phase 2)
- Loading states and empty states for the workout screen
- Program picker UI design (card list, simple list, etc.)
- Summary screen layout and content details
- How the undo toast looks and animates
- Notification permission request flow
- How per-program timer disable is exposed in the UI (may touch Program model -- can be a settings-level or program-level flag)

### Deferred Ideas (OUT OF SCOPE)
- Per-program rest timer duration (different rest times for different programs) -- keep simple with global default for now
- Add exercises to a workout that aren't in the program (ad-hoc exercises) -- Phase 3 only covers adding extra sets, not extra exercises
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LOG-01 | User can start a workout from a program template | Backend: POST /api/workouts creates Workout from program_id, populates initial sets from program template. Frontend: program picker on /workout, start creates session. |
| LOG-02 | User can log each set with actual weight and reps (pre-filled from last session) | Backend: pre-fill endpoint returns last-session actuals per exercise_id. Frontend: tap-to-complete UX with editable weight/reps fields, PUT to update set. |
| LOG-03 | User can edit or delete any logged set, exercise, or workout | Backend: PUT/DELETE for individual sets, DELETE for exercise-group and full workout. Frontend: swipe/tap interactions, undo toast with delayed permanent delete. |
| LOG-04 | User sees a rest timer that auto-starts after logging a set (configurable duration) | Backend: GET/PUT /api/settings for rest_timer_seconds. Frontend: floating timer component, browser Notification API, per-program disable flag. |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.100+ | Backend API | Already in use, established pattern |
| SQLAlchemy | 2.0+ | ORM, queries | Already in use, sync sessions |
| Pydantic | 2.0+ | Request/response validation | Already in use, from_attributes |
| Vue 3 | 3.4+ | Frontend framework | Already in use, Composition API |
| Pinia | 2.1+ | State management | Already in use, composition stores |
| Tailwind CSS | 4.0 | Styling | Already in use, v4 @import syntax |
| Vue Router | 4.x | Routing | Already in use, lazy-loaded routes |

### Supporting (no new dependencies needed)
| Library | Purpose | Notes |
|---------|---------|-------|
| Browser Notification API | Rest timer alerts | Built-in, no library needed |
| Browser `setInterval` | Timer countdown | Built-in, no library needed |
| CSS transitions/animations | Undo toast, timer bar | Tailwind transition classes |
| Touch events | Swipe detection | Can be implemented with native touch events (touchstart/touchmove/touchend) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Native touch events for swipe | Hammer.js or @vueuse/gesture | Adds dependency for a simple left-swipe; native is sufficient for single-direction swipe |
| setInterval for timer | @vueuse/core `useInterval` | VueUse adds a dependency; raw setInterval with ref is trivial |
| Custom undo toast | vue-toastification | Adds dependency for one component; custom is simpler and matches existing no-library approach |

**No new packages required.** This phase uses only what is already installed plus browser APIs.

## Architecture Patterns

### Backend: Workout Routes Structure
```
app/workouts/
  __init__.py      # exists
  models.py        # exists (Workout, WorkoutSet, Setting)
  schemas.py       # exists (needs expansion)
  routes.py        # NEW - all workout CRUD endpoints
```

### Backend API Design

```
POST   /api/workouts              # Start workout from program_id
GET    /api/workouts/active        # Get active workout (completed_at IS NULL) or 404
GET    /api/workouts/:id           # Get workout with nested sets + exercise info
PATCH  /api/workouts/:id/complete  # Set completed_at = now()

POST   /api/workouts/:id/sets      # Log a new set (or batch from template)
PUT    /api/workouts/:id/sets/:sid  # Edit a logged set
DELETE /api/workouts/:id/sets/:sid  # Delete a logged set

DELETE /api/workouts/:id/exercises/:eid  # Remove all sets for exercise from workout
DELETE /api/workouts/:id            # Discard entire workout

GET    /api/settings/:key           # Get a setting value
PUT    /api/settings/:key           # Set a setting value
```

### Pattern 1: Active Workout Detection
**What:** On page load, check for an in-progress workout (completed_at IS NULL). Resume if found, show program picker if not.
**When to use:** Every time the user navigates to /workout.
**Example:**
```python
# Backend: GET /api/workouts/active
def get_active_workout(db: Session = Depends(get_db)):
    workout = (
        db.query(Workout)
        .filter(Workout.completed_at.is_(None))
        .options(
            selectinload(Workout.sets).selectinload(WorkoutSet.exercise)
        )
        .first()
    )
    if not workout:
        raise HTTPException(status_code=404, detail="No active workout")
    return workout
```

### Pattern 2: Pre-fill from Last Session
**What:** For each exercise in the program, find the most recent completed workout that logged that exercise, and return its actual weight/reps per set_number.
**When to use:** When starting a new workout or displaying unfilled sets.
**Example:**
```python
# Backend: subquery approach for last-session pre-fill
from sqlalchemy import and_, desc

def get_last_session_data(db: Session, exercise_ids: list[int]) -> dict:
    """Returns {exercise_id: [{set_number, weight_kg, reps, is_warmup}, ...]}"""
    results = {}
    for ex_id in exercise_ids:
        # Find most recent completed workout with this exercise
        last_sets = (
            db.query(WorkoutSet)
            .join(Workout, WorkoutSet.workout_id == Workout.id)
            .filter(
                WorkoutSet.exercise_id == ex_id,
                Workout.completed_at.isnot(None),
            )
            .order_by(Workout.completed_at.desc(), WorkoutSet.set_number)
            .all()
        )
        if last_sets:
            # Group by the most recent workout only
            latest_workout_id = last_sets[0].workout_id
            results[ex_id] = [
                s for s in last_sets if s.workout_id == latest_workout_id
            ]
    return results
```

### Pattern 3: Start Workout from Program Template
**What:** POST /api/workouts with program_id creates a Workout row, then for each ProgramExercise/ProgramSet, creates corresponding WorkoutSet rows with weight_kg/reps set to NULL (to be filled by pre-fill or user input). Or, create sets lazily on first log.
**Decision:** Create workout row immediately but populate sets lazily (on log). This avoids orphan sets if user doesn't complete exercises. The frontend holds template data from the program and sends individual set logs as the user completes them.

### Pattern 4: Undo Toast with Delayed Delete
**What:** Delete from UI immediately, show undo toast with timeout. If user doesn't undo, send DELETE to server. If user undoes, restore from local state.
**When to use:** Set deletion, exercise removal, workout discard.
**Example:**
```typescript
// Frontend pattern: optimistic delete with undo
function deleteSetWithUndo(setId: number) {
  const removedSet = { ...sets.value.find(s => s.id === setId)! }
  // Remove from local state immediately
  sets.value = sets.value.filter(s => s.id !== setId)

  const timeoutId = setTimeout(async () => {
    await fetch(`/api/workouts/${workoutId}/sets/${setId}`, { method: 'DELETE' })
    undoToast.value = null
  }, 7000) // 7 seconds

  undoToast.value = {
    message: 'Set deleted',
    undo: () => {
      clearTimeout(timeoutId)
      sets.value.push(removedSet)
      sets.value.sort((a, b) => a.set_number - b.set_number)
      undoToast.value = null
    }
  }
}
```

### Pattern 5: Floating Rest Timer (Vue composable)
**What:** A `useRestTimer` composable managing countdown state, auto-start on set completion, browser notifications.
**Example:**
```typescript
// Frontend: composable pattern
function useRestTimer(defaultSeconds: number) {
  const remaining = ref(0)
  const isRunning = ref(false)
  let intervalId: number | null = null

  function start(seconds?: number) {
    remaining.value = seconds ?? defaultSeconds
    isRunning.value = true
    intervalId = window.setInterval(() => {
      remaining.value--
      if (remaining.value <= 0) {
        stop()
        notifyRestComplete()
      }
    }, 1000)
  }

  function skip() {
    stop()
  }

  function stop() {
    if (intervalId) clearInterval(intervalId)
    isRunning.value = false
    remaining.value = 0
  }

  function notifyRestComplete() {
    if (Notification.permission === 'granted') {
      new Notification('Rest Complete', { body: 'Time for next set!' })
    }
  }

  return { remaining, isRunning, start, skip }
}
```

### Frontend Component Structure
```
src/
  views/
    WorkoutView.vue          # Main container: picker vs active workout
  components/
    workout/
      ProgramPicker.vue      # Program selection grid/list
      ActiveWorkout.vue      # Scrollable exercise list with sets
      ExerciseCard.vue       # Single exercise with its sets
      SetRow.vue             # Individual set row (tap-to-complete)
      RestTimer.vue          # Floating countdown bar
      WorkoutSummary.vue     # Finish confirmation/summary modal
      UndoToast.vue          # Reusable undo toast (bottom bar)
  composables/
    useRestTimer.ts          # Timer logic composable
  stores/
    workouts.ts              # Workout Pinia store
```

### Anti-Patterns to Avoid
- **Storing workout state only in frontend:** Browser close loses progress. All set logs must persist to server immediately.
- **N+1 queries for pre-fill:** Don't query last session per-set. Batch by exercise_id, single query per exercise at most.
- **Using confirm() for destructive actions:** Blocks UI thread, not mobile-friendly. Use undo toast pattern instead (except exercise removal which uses a confirmation as specified).
- **Timer drift with setInterval:** For a gym rest timer, 1-second granularity is sufficient. No need for drift correction -- the visual countdown is approximate. However, store the `endTime` timestamp and compute remaining from `Date.now()` for accuracy after tab switches.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Touch swipe detection | Full gesture library | Simple touchstart/touchmove/touchend with threshold | Only need left-swipe on set rows; 20 lines of code vs a library |
| Notification permissions | Complex permission flow | `Notification.requestPermission()` on first timer start | Browser API handles the prompt natively |
| Timer accuracy across tab switches | Complex web worker timer | Store `endTime = Date.now() + remainingMs`, recompute on visibility change | `document.visibilitychange` event handles tab-switch resume |

## Common Pitfalls

### Pitfall 1: Tab Switch Kills Timer
**What goes wrong:** `setInterval` slows or stops when tab is backgrounded. Timer shows wrong time when user switches back.
**Why it happens:** Browsers throttle intervals in background tabs to save battery.
**How to avoid:** Store absolute `endTime` timestamp. On `visibilitychange`, recompute `remaining = endTime - Date.now()`. If expired while backgrounded, trigger notification immediately.
**Warning signs:** Timer shows negative or wrong values after switching tabs.

### Pitfall 2: Race Condition on Rapid Set Logging
**What goes wrong:** User logs multiple sets quickly; concurrent API calls return stale workout state.
**Why it happens:** Mutation-then-re-fetch pattern races when two POSTs overlap.
**How to avoid:** Use optimistic local state updates. Each POST creates a set and returns it; append to local array without re-fetching entire workout. Reserve full re-fetch for page load only.

### Pitfall 3: Undo Toast Timing Edge Cases
**What goes wrong:** User deletes a set, then navigates away before timeout. Delete never fires. Or user deletes multiple sets rapidly -- only last undo is accessible.
**Why it happens:** Component unmount clears timeouts; multiple deletes overwrite single toast.
**How to avoid:** Fire DELETE immediately on navigation (use `onBeforeUnmount`). For multiple pending deletes, stack them or use a queue. Simpler: send DELETE immediately to server, undo re-creates the set via POST.

### Pitfall 4: Pre-fill Query Performance
**What goes wrong:** Querying last session for 8+ exercises on workout start is slow.
**Why it happens:** N separate queries, each scanning completed workouts.
**How to avoid:** Single query approach: find the most recent completed workout_id per exercise using a correlated subquery or window function, then batch-fetch all sets for those workout_ids.

### Pitfall 5: WorkoutSet Missing Exercise Name
**What goes wrong:** API returns workout sets but frontend can't display exercise names.
**Why it happens:** `WorkoutSet` has `exercise_id` FK but response schema doesn't include nested exercise.
**How to avoid:** Use `selectinload(WorkoutSet.exercise)` when querying. Expand `WorkoutSetRead` schema to include nested `ExerciseRead`.

## Code Examples

### Backend: Expanded Workout Schemas
```python
# Schemas needed for full workout logging
class WorkoutSetCreate(BaseModel):
    exercise_id: int
    set_number: int
    weight_kg: float | None = None
    reps: int | None = None
    is_warmup: bool = False

class WorkoutSetUpdate(BaseModel):
    weight_kg: float | None = None
    reps: int | None = None

class WorkoutSetRead(BaseModel):
    id: int
    workout_id: int
    exercise_id: int
    set_number: int
    weight_kg: float | None
    reps: int | None
    is_warmup: bool
    exercise: ExerciseRead | None = None  # Include exercise name
    model_config = {"from_attributes": True}

class WorkoutRead(BaseModel):
    id: int
    program_id: int | None
    started_at: datetime
    completed_at: datetime | None
    sets: list[WorkoutSetRead] = []  # Include nested sets
    model_config = {"from_attributes": True}

class WorkoutCreate(BaseModel):
    program_id: int
```

### Backend: Register Router in main.py
```python
from app.workouts.routes import router as workouts_router
app.include_router(workouts_router, prefix="/api")
# Also need settings routes -- can be in workouts/routes.py or separate
```

### Frontend: Pinia Workout Store Pattern
```typescript
// Follow existing programs store pattern
export const useWorkoutsStore = defineStore('workouts', () => {
  const activeWorkout = ref<Workout | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchActiveWorkout(): Promise<boolean> {
    try {
      const res = await fetch('/api/workouts/active')
      if (res.status === 404) { activeWorkout.value = null; return false }
      if (!res.ok) throw new Error('Failed to fetch active workout')
      activeWorkout.value = await res.json()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error'
      return false
    }
  }

  async function startWorkout(programId: number): Promise<Workout> {
    const res = await fetch('/api/workouts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ program_id: programId }),
    })
    if (!res.ok) throw new Error('Failed to start workout')
    activeWorkout.value = await res.json()
    return activeWorkout.value!
  }

  async function logSet(data: WorkoutSetCreate): Promise<WorkoutSet> {
    const res = await fetch(`/api/workouts/${activeWorkout.value!.id}/sets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to log set')
    const newSet = await res.json()
    activeWorkout.value!.sets.push(newSet)  // Optimistic append
    return newSet
  }

  // ... updateSet, deleteSet, completeWorkout, discardWorkout
  return { activeWorkout, loading, error, fetchActiveWorkout, startWorkout, logSet }
})
```

### Frontend: Swipe Detection (minimal)
```typescript
// Composable: useSwipeLeft
function useSwipeLeft(el: Ref<HTMLElement | null>, onSwipe: () => void) {
  let startX = 0
  const threshold = 60

  function onTouchStart(e: TouchEvent) { startX = e.touches[0].clientX }
  function onTouchEnd(e: TouchEvent) {
    const diff = startX - e.changedTouches[0].clientX
    if (diff > threshold) onSwipe()
  }

  onMounted(() => {
    el.value?.addEventListener('touchstart', onTouchStart)
    el.value?.addEventListener('touchend', onTouchEnd)
  })
  onUnmounted(() => {
    el.value?.removeEventListener('touchstart', onTouchStart)
    el.value?.removeEventListener('touchend', onTouchEnd)
  })
}
```

### Per-Program Timer Disable
**Recommendation:** Add a boolean `rest_timer_disabled` column to the `programs` table (default false). This requires a migration in scripts/ and model update in both repos. Alternatively, store it in settings as `program:{id}:rest_timer_disabled`. The column approach is cleaner and queryable.

```python
# Migration needed in scripts/ repo
# Add to programs table:
rest_timer_disabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LocalStorage for workout state | Server-side persistence | N/A (design choice) | Survives browser close, device switch |
| window.confirm() for deletes | Undo toast pattern | UX best practice | Non-blocking, mobile-friendly, reversible |
| Polling for timer | visibilitychange + stored endTime | Browser API | Accurate timer even after tab switch |

## Open Questions

1. **Per-program timer disable: column vs settings key?**
   - What we know: User wants per-program disable. Adding a column requires migration.
   - What's unclear: Whether to add a column to `programs` or use a settings key pattern.
   - Recommendation: Add `rest_timer_disabled` boolean column to `programs` table. Cleaner, no string-key lookup. Requires Alembic migration in scripts/ and model duplication update in backend/.

2. **Pre-fill data endpoint design: dedicated endpoint vs inline in workout start?**
   - What we know: Pre-fill needs last-session actuals for each exercise.
   - What's unclear: Whether to return pre-fill data as part of POST /api/workouts response, or as a separate GET.
   - Recommendation: Return pre-fill data as part of the POST /api/workouts response (a `pre_fill` map keyed by exercise_id). Single round-trip, all data the UI needs at start.

3. **Set creation strategy: eager (create all sets on workout start) vs lazy (create on log)?**
   - What we know: Program defines target sets per exercise. User can add extra sets.
   - What's unclear: Whether to pre-create WorkoutSet rows or create on-demand.
   - Recommendation: Lazy creation. Frontend holds program template data. When user taps to complete a set, POST creates the WorkoutSet row. This avoids orphan incomplete sets and simplifies the "add extra set" flow.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend), Vitest (frontend -- if configured) |
| Config file | pytest: ../backend/pyproject.toml or pytest.ini; vitest: ../frontend/vitest.config.ts |
| Quick run command | `cd ../backend && uv run pytest tests/ -x --tb=short` |
| Full suite command | `cd ../backend && uv run pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LOG-01 | Start workout from program | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_start_workout -x` | Wave 0 |
| LOG-01 | Active workout detection | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_active_workout -x` | Wave 0 |
| LOG-02 | Log set with weight/reps | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_log_set -x` | Wave 0 |
| LOG-02 | Pre-fill from last session | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_prefill_last_session -x` | Wave 0 |
| LOG-03 | Edit logged set | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_update_set -x` | Wave 0 |
| LOG-03 | Delete set | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_delete_set -x` | Wave 0 |
| LOG-03 | Delete exercise from workout | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_delete_exercise_sets -x` | Wave 0 |
| LOG-03 | Discard workout | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_discard_workout -x` | Wave 0 |
| LOG-04 | Settings CRUD (rest timer) | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_settings_crud -x` | Wave 0 |
| LOG-04 | Rest timer UI | manual-only | Visual: timer starts after set log, counts down, notification fires | N/A |

### Sampling Rate
- **Per task commit:** `cd ../backend && uv run pytest tests/test_workouts.py -x --tb=short`
- **Per wave merge:** `cd ../backend && uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `../backend/tests/test_workouts.py` -- covers LOG-01, LOG-02, LOG-03, LOG-04 (settings)
- [ ] `../backend/tests/conftest.py` -- may need workout/program fixtures (check if exists)
- [ ] Verify pytest is in backend dev dependencies

## Sources

### Primary (HIGH confidence)
- Existing codebase: `app/workouts/models.py`, `app/programs/routes.py`, `frontend/src/stores/programs.ts` -- direct pattern reference
- SQLAlchemy 2.0 relationship loading: `selectinload` pattern used in programs routes (verified in codebase)
- Browser Notification API: standard web API, widely supported

### Secondary (MEDIUM confidence)
- Vue 3 Composition API patterns: `onMounted`, `onBeforeUnmount`, `ref`, `computed` -- used throughout existing codebase
- Pinia store patterns: established in exercises.ts and programs.ts

### Tertiary (LOW confidence)
- None -- all findings based on existing codebase patterns and standard web APIs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, all patterns established in codebase
- Architecture: HIGH - follows existing domain-grouped backend pattern, Pinia store pattern
- Pitfalls: HIGH - timer/tab-switch and optimistic update issues are well-documented browser behaviors
- Pre-fill query: MEDIUM - specific SQL approach needs validation during implementation

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable stack, no fast-moving dependencies)
