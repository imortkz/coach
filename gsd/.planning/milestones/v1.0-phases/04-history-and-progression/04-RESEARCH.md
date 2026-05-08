# Phase 4: History and Progression - Research

**Researched:** 2026-03-07
**Domain:** Workout history views, per-exercise charting, linear progression algorithm
**Confidence:** HIGH

## Summary

Phase 4 adds two read-only history views (workout list, per-exercise detail with charts) and a server-side progression algorithm that extends the existing pre-fill endpoint. No schema migrations are needed -- all data already exists in the `workouts`, `workout_sets`, `exercises`, and `settings` tables. The progression logic is straightforward: compare last session's non-warmup sets against program target reps, and if all hit target, suggest weight + equipment-based increment.

The charting requirement introduces the only new dependency: Chart.js via vue-chartjs. This is the standard choice for Vue 3 projects needing simple line charts without heavy visualization frameworks. The rest of the phase reuses established patterns (Pinia stores, Tailwind cards, FastAPI endpoints with selectinload).

**Primary recommendation:** Split into 3 plans: (1) backend history endpoints + progression algorithm, (2) frontend workout history list with expand/collapse cards, (3) per-exercise history page with charts + suggestion display integration into workout flow.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Summary cards in reverse chronological order, tap to expand/collapse inline (no page navigation)
- Each card shows: date, program name, exercise count, total sets, duration
- Program filter dropdown at top, load-more or infinite scroll
- Per-exercise history at /exercises/:id/history with chart on top, session table below
- Two entry points: tap exercise name in expanded history card, or tap exercise in exercise library
- Chart shows two lines: best set weight per session and total volume (sets x reps x weight)
- Session table shows last 10-20 sessions with date and all sets
- Progression suggestion shown at top of per-exercise history page
- Trigger: all non-warmup sets hit or exceeded target reps at current weight in last session
- Lookback: last session only (simple linear progression)
- Equipment-based increments: Barbell +2.5kg, Dumbbell +2.0kg, Cable/Machine +2.5kg, Bodyweight +1 rep, Kettlebell +4.0kg, Smith Machine +2.5kg, EZ Bar +2.5kg, Resistance Band +1 rep, Trap Bar +2.5kg, Landmine +2.5kg
- Runs server-side, extending pre-fill endpoint with `suggestions` field
- Suggested weight replaces pre-fill value with upward arrow indicator and accent color
- Override is silent, no tracking
- Exercises without enough history show normal pre-fill, no special indicator

### Claude's Discretion
- Chart library choice and styling
- Exact arrow/accent color for suggestion indicator
- Loading and empty states for history views
- Session table pagination or scroll behavior
- How progression increments are stored in settings (key naming, defaults)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HIST-01 | User can view chronological list of completed workouts with exercises and sets | Backend: paginated GET /api/workouts endpoint. Frontend: HistoryView with expandable workout cards |
| HIST-02 | User can view per-exercise history showing recent sessions with weight/reps | Backend: GET /api/exercises/:id/history endpoint returning session data. Frontend: ExerciseHistoryView with chart + table |
| PRGS-01 | User sees auto-suggested weight for next session based on past performance | Backend: extend WorkoutStartResponse with `suggestions` dict. Frontend: show suggestion indicator on SetRow |
| PRGS-02 | Progression algorithm uses simple linear model (hit all target reps -> increase weight) | Backend: progression function checking last session non-warmup sets vs program targets, applying equipment-based increment |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Chart.js | ^4.4 | Canvas-based charting | De facto standard for web charts, 60KB gzipped, well-maintained |
| vue-chartjs | ^5.3 | Vue 3 wrapper for Chart.js | Official Vue wrapper, reactive data binding, Composition API support |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none new on backend) | -- | All backend needs met by existing stack | SQLAlchemy queries suffice for history/progression |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Chart.js + vue-chartjs | Lightweight Charts (TradingView) | Overkill for 2 line charts, financial focus |
| Chart.js + vue-chartjs | Unovis | Newer/less community support, more complex API |
| Chart.js + vue-chartjs | Raw Canvas/SVG | Hand-rolling defeats purpose, Chart.js is small enough |

**Installation:**
```bash
cd ../frontend && npm install chart.js vue-chartjs
```

## Architecture Patterns

### Backend: New Endpoints

```
GET /api/workouts?limit=20&offset=0&program_id=X
  -> paginated list of completed workouts with nested sets + exercise info
  -> includes computed fields: exercise_count, total_sets, duration_minutes

GET /api/exercises/{id}/history?limit=20
  -> recent sessions for this exercise: [{date, sets: [{set_number, weight_kg, reps, is_warmup}]}]
  -> includes progression suggestion: {suggested_weight_kg, increment, reason}
```

The existing `GET /api/workouts/{id}` already returns a full workout -- the new list endpoint just adds pagination and filtering for completed workouts.

### Backend: Progression Algorithm

```python
def compute_suggestion(
    db: Session,
    exercise_id: int,
    program_id: int | None,
) -> dict | None:
    """
    1. Find last completed workout with sets for this exercise
    2. Get non-warmup sets from that workout
    3. Look up target_reps from program template (if program_id provided)
    4. If ALL non-warmup sets have reps >= target_reps at same weight:
       -> suggest weight + equipment_increment
    5. Otherwise: suggest same weight (keep at X)
    6. For bodyweight/resistance band: suggest +1 rep instead
    """
```

Key integration: extend `_compute_prefill()` to also return a `suggestions` dict alongside `pre_fill`. The `WorkoutStartResponse` schema adds `suggestions: dict[int, SuggestionInfo]`.

### Frontend: New Routes and Views

```
/history                    -> HistoryView.vue (workout list)
/exercises/:id/history      -> ExerciseHistoryView.vue (chart + table + suggestion)
```

### Recommended Component Structure
```
src/
├── views/
│   ├── HistoryView.vue              # Workout history list (already exists as stub)
│   └── ExerciseHistoryView.vue      # Per-exercise history page (new)
├── components/
│   └── history/
│       ├── WorkoutCard.vue          # Expandable workout summary card
│       ├── ExerciseChart.vue        # Chart.js line chart (weight + volume)
│       └── SessionTable.vue         # Recent sessions table
├── stores/
│   └── history.ts                   # History data fetching store
```

### Pattern: Expandable Card (reuse from Phase 3)

The ExerciseCard in Phase 3 shows how to build interactive cards. WorkoutCard follows same structure:
- Click header to toggle expand
- `ref<Set<number>>` tracks expanded card IDs
- Transition for smooth expand/collapse
- Exercise names in expanded view are tappable links to /exercises/:id/history

### Pattern: Pagination with Load More

```typescript
// In history store
const workouts = ref<WorkoutSummary[]>([])
const hasMore = ref(true)
const offset = ref(0)
const LIMIT = 20

async function loadMore() {
  const res = await fetch(`/api/workouts?limit=${LIMIT}&offset=${offset.value}`)
  const data = await res.json()
  workouts.value.push(...data.items)
  hasMore.value = data.items.length === LIMIT
  offset.value += data.items.length
}
```

### Anti-Patterns to Avoid
- **N+1 queries on history list:** Use `selectinload` for sets and exercises in the paginated workout list query, same pattern as existing `_eager_load_workout`
- **Recomputing progression on every page load:** Compute progression only in `_compute_prefill` (workout start) and the exercise history endpoint -- not as a separate global computation
- **Storing suggestions client-side permanently:** Suggestions are ephemeral, computed per-request. Don't cache them in localStorage

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Line charts | Canvas drawing code | Chart.js + vue-chartjs | Responsive, tooltips, legend, animations free |
| Pagination | Custom offset tracking | Standard limit/offset pattern with `hasMore` flag | Simple, no cursor complexity needed for this scale |
| Date formatting | Manual date string manipulation | `Intl.DateTimeFormat` or `toLocaleDateString()` | Built into browser, handles locale |

**Key insight:** The progression algorithm itself IS the hand-built piece, but it's intentionally simple (last session check + increment table). Don't over-engineer it with rolling averages, deload detection, or plateau analysis -- those are v2 (PRGS-03, PRGS-04).

## Common Pitfalls

### Pitfall 1: Progression checks warmup sets
**What goes wrong:** Warmup sets typically use lighter weight and shouldn't count toward progression decisions
**Why it happens:** Forgetting to filter `is_warmup=False` in the progression query
**How to avoid:** Always filter `WorkoutSet.is_warmup == False` when computing progression
**Warning signs:** User gets suggested increases after hitting reps on warmup but failing work sets

### Pitfall 2: No program context for progression
**What goes wrong:** Exercise done ad-hoc (no program) has no target_reps to compare against
**Why it happens:** Progression requires knowing target reps, which come from ProgramSet
**How to avoid:** Only compute suggestions for exercises that belong to the current program. Return null suggestion for exercises without program context
**Warning signs:** KeyError or None when looking up target_reps

### Pitfall 3: Mixed weight across non-warmup sets
**What goes wrong:** User does 80kg for set 1-2 but drops to 75kg for set 3. Algorithm compares "all sets at current weight" but sets have different weights
**Why it happens:** Real-world lifting often involves drop sets or failing
**How to avoid:** Use the MOST COMMON weight among non-warmup sets (mode), or check if ALL non-warmup sets used the same weight. If weights vary, don't suggest increase
**Warning signs:** Progression triggered when user was actually struggling

### Pitfall 4: Chart.js registration
**What goes wrong:** "X is not a registered element" error at runtime
**Why it happens:** Chart.js v4 uses tree-shaking -- components must be explicitly registered
**How to avoid:** Register needed components: `Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)`
**Warning signs:** Blank canvas or console errors about unregistered elements

### Pitfall 5: Duration calculation with null completed_at
**What goes wrong:** Workout card shows NaN or error for duration
**Why it happens:** Active/incomplete workouts have `completed_at = null`
**How to avoid:** History list should only show completed workouts (`completed_at IS NOT NULL`). Filter in the query, not the template
**Warning signs:** NaN in duration display

### Pitfall 6: JSON key type mismatch for suggestions
**What goes wrong:** Suggestions dict keyed by exercise_id (int) but JSON serializes keys as strings
**Why it happens:** Same issue that exists with pre_fill -- JSON object keys are always strings
**How to avoid:** Frontend must access suggestions via `String(exerciseId)` or parse keys, matching existing pre_fill pattern
**Warning signs:** Suggestions showing as undefined for all exercises

## Code Examples

### Backend: Paginated Workout History Endpoint
```python
# Source: follows existing patterns in routes.py
@router.get("", response_model=WorkoutListResponse)
def list_workouts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    program_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Workout)
        .options(selectinload(Workout.sets).selectinload(WorkoutSet.exercise))
        .filter(Workout.completed_at.isnot(None))
        .order_by(Workout.completed_at.desc())
    )
    if program_id:
        query = query.filter(Workout.program_id == program_id)

    workouts = query.offset(offset).limit(limit).all()
    return {"items": workouts}
```

### Backend: Progression Logic
```python
# Source: designed from CONTEXT.md decisions
EQUIPMENT_INCREMENTS = {
    "Barbell": 2.5,
    "Dumbbell": 2.0,
    "Cable": 2.5,
    "Machine": 2.5,
    "Bodyweight": None,      # +1 rep instead
    "Kettlebell": 4.0,
    "Smith Machine": 2.5,
    "EZ Bar": 2.5,
    "Resistance Band": None, # +1 rep instead
    "Trap Bar": 2.5,
    "Landmine": 2.5,
}

def compute_progression(
    db: Session, exercise_id: int, program_id: int,
) -> dict | None:
    # 1. Get exercise equipment type
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        return None

    # 2. Get target reps from program
    pe = (
        db.query(ProgramExercise)
        .filter(ProgramExercise.program_id == program_id,
                ProgramExercise.exercise_id == exercise_id)
        .first()
    )
    if not pe:
        return None

    target_reps = max(ps.target_reps for ps in pe.sets if not ps.is_warmup)

    # 3. Get last completed session's non-warmup sets
    last_workout = (
        db.query(Workout)
        .filter(
            Workout.completed_at.isnot(None),
            Workout.id.in_(
                db.query(WorkoutSet.workout_id)
                .filter(WorkoutSet.exercise_id == exercise_id)
                .scalar_subquery()
            ),
        )
        .order_by(Workout.completed_at.desc())
        .first()
    )
    if not last_workout:
        return None

    work_sets = (
        db.query(WorkoutSet)
        .filter(
            WorkoutSet.workout_id == last_workout.id,
            WorkoutSet.exercise_id == exercise_id,
            WorkoutSet.is_warmup == False,
        )
        .all()
    )
    if not work_sets:
        return None

    # 4. Check if all work sets hit target reps at same weight
    weights = {ws.weight_kg for ws in work_sets}
    if len(weights) != 1:
        return None  # Mixed weights, don't suggest

    current_weight = weights.pop()
    all_hit = all(ws.reps is not None and ws.reps >= target_reps for ws in work_sets)

    # 5. Check for user-overridden increment in settings
    increment_key = f"progression_increment_{exercise.equipment.lower().replace(' ', '_')}"
    setting = db.query(Setting).filter(Setting.key == increment_key).first()

    equipment_key = exercise.equipment
    default_increment = EQUIPMENT_INCREMENTS.get(equipment_key)

    if all_hit:
        if default_increment is None:
            # Bodyweight/band: suggest +1 rep
            return {"type": "reps", "suggested_reps": target_reps + 1, "reason": "hit_target"}

        increment = float(setting.value) if setting else default_increment
        return {
            "type": "weight",
            "suggested_weight_kg": current_weight + increment,
            "increment": increment,
            "reason": "hit_target",
        }
    else:
        return {
            "type": "keep",
            "suggested_weight_kg": current_weight,
            "reason": "missed_reps",
        }
```

### Frontend: Chart.js Registration and Line Chart
```typescript
// Source: Chart.js v4 + vue-chartjs v5 pattern
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
)

// In component:
const chartData = computed(() => ({
  labels: sessions.value.map(s => formatDate(s.date)),
  datasets: [
    {
      label: 'Best Set Weight (kg)',
      data: sessions.value.map(s => s.best_weight),
      borderColor: '#3B82F6',
      tension: 0.3,
      yAxisID: 'y',
    },
    {
      label: 'Total Volume',
      data: sessions.value.map(s => s.total_volume),
      borderColor: '#10B981',
      tension: 0.3,
      yAxisID: 'y1',
    },
  ],
}))

const chartOptions = {
  responsive: true,
  interaction: { mode: 'index' as const, intersect: false },
  scales: {
    y: { type: 'linear' as const, position: 'left' as const, title: { display: true, text: 'kg' } },
    y1: { type: 'linear' as const, position: 'right' as const, grid: { drawOnChartArea: false } },
  },
}
```

### Frontend: Suggestion Indicator in SetRow
```vue
<!-- Accent color and arrow for suggested weight -->
<span v-if="hasSuggestion" class="text-emerald-600 font-medium flex items-center gap-0.5">
  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
  </svg>
  {{ suggestedWeight }}
</span>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Chart.js v3 global register | Chart.js v4 tree-shakable register | 2023 | Must explicitly register chart components |
| vue-chartjs v4 (Options API) | vue-chartjs v5 (Composition API) | 2023 | Uses `<Line>` component directly, no mixins |

**Deprecated/outdated:**
- vue-chart-3 package: abandoned, use official vue-chartjs v5 instead
- Chart.js v3 auto-registration: v4 requires explicit `Chart.register(...)` calls

## Open Questions

1. **Session table row limit**
   - What we know: CONTEXT.md says "last 10-20 sessions"
   - What's unclear: Exact number
   - Recommendation: Default to 20 with load-more. Backend accepts `limit` parameter

2. **Progression increment storage key naming**
   - What we know: Settings table uses key-value strings. User said Claude's discretion
   - What's unclear: Whether to use one setting per equipment type or a JSON blob
   - Recommendation: One setting per equipment type: `progression_increment_barbell`, `progression_increment_dumbbell`, etc. Simple, queryable, matches existing settings pattern (e.g., `rest_timer_seconds`)

3. **Workout card program name**
   - What we know: Cards need program name, but Workout model only has `program_id`
   - What's unclear: Whether to join Program or denormalize
   - Recommendation: Join Program in the query (single query with selectinload). Add program relationship to Workout model or join in the list query. This is read-only, performance is fine

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x (backend), vitest 4.x (frontend) |
| Config file | backend: pyproject.toml, frontend: none (needs vitest.config.ts) |
| Quick run command | `cd ../backend && uv run pytest tests/test_workouts.py -x` |
| Full suite command | `cd ../backend && uv run pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HIST-01 | GET /api/workouts returns paginated completed workouts | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestListWorkouts -x` | No - Wave 0 |
| HIST-01 | Program filter on workout list | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestListWorkouts::test_filter_by_program -x` | No - Wave 0 |
| HIST-02 | GET /api/exercises/:id/history returns session data | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestExerciseHistory -x` | No - Wave 0 |
| PRGS-01 | WorkoutStartResponse includes suggestions dict | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestProgression::test_suggestion_in_prefill -x` | No - Wave 0 |
| PRGS-02 | Progression suggests increase when all reps hit | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestProgression::test_suggest_increase -x` | No - Wave 0 |
| PRGS-02 | Progression keeps weight when reps missed | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestProgression::test_keep_weight -x` | No - Wave 0 |
| PRGS-02 | Bodyweight exercises suggest +1 rep | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestProgression::test_bodyweight_rep_increase -x` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `cd ../backend && uv run pytest tests/test_workouts.py -x`
- **Per wave merge:** `cd ../backend && uv run pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_workouts.py::TestListWorkouts` -- covers HIST-01 (paginated list, program filter)
- [ ] `tests/test_workouts.py::TestExerciseHistory` -- covers HIST-02 (per-exercise session data)
- [ ] `tests/test_workouts.py::TestProgression` -- covers PRGS-01, PRGS-02 (suggestion computation, equipment increments, edge cases)

*(All new test classes go in existing `test_workouts.py` file. Existing conftest.py and fixtures are sufficient.)*

## Sources

### Primary (HIGH confidence)
- Codebase inspection: backend models, schemas, routes, tests, frontend stores/views/components
- CONTEXT.md: locked decisions from user discussion

### Secondary (MEDIUM confidence)
- [vue-chartjs official site](https://vue-chartjs.org/) - Vue 3 wrapper for Chart.js, Composition API support
- [Chart.js npm](https://www.npmjs.com/package/chart.js) - v4 tree-shaking, registration requirements
- [Vue chart libraries comparison 2026](https://weavelinx.com/best-chart-libraries-for-vue-projects-in-2026/) - ecosystem landscape

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Chart.js + vue-chartjs is the established Vue charting solution, well-documented
- Architecture: HIGH - follows existing codebase patterns exactly (Pinia stores, FastAPI routes, selectinload)
- Pitfalls: HIGH - identified from real codebase patterns (pre_fill key types, warmup filtering, Chart.js registration)
- Progression algorithm: HIGH - simple logic, well-defined rules from CONTEXT.md

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable domain, no fast-moving dependencies)
