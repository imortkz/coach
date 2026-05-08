---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - ../frontend/src/components/workout/ActiveWorkout.vue
  - ../frontend/src/components/history/WorkoutCard.vue
autonomous: true
must_haves:
  truths:
    - "Active workout header shows correct elapsed time (minutes since start, not offset by timezone)"
    - "Workout history cards show correct duration"
  artifacts:
    - path: "../frontend/src/components/workout/ActiveWorkout.vue"
      provides: "Fixed UTC datetime parsing for elapsed time"
      contains: "endsWith.*Z"
    - path: "../frontend/src/components/history/WorkoutCard.vue"
      provides: "Fixed UTC datetime parsing for duration display"
      contains: "endsWith.*Z"
  key_links: []
---

<objective>
Fix workout elapsed time displaying ~5h offset instead of actual duration.

Purpose: The backend stores naive UTC datetimes and FastAPI serializes them without a "Z" suffix (e.g., "2026-03-07T10:30:00"). JavaScript's `new Date()` treats strings without "Z" as local time, causing a timezone offset error. WorkoutSummary.vue already has the correct fix — apply the same pattern to the two other files that parse `started_at`.

Output: Corrected elapsed time in active workout header and workout history cards.
</objective>

<execution_context>
@/Users/vjkim/.claude/get-shit-done/workflows/execute-plan.md
@/Users/vjkim/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
**Root cause:** Backend uses `datetime.now(timezone.utc).replace(tzinfo=None)` (Phase 06 decision) producing naive UTC datetimes. FastAPI/Pydantic serializes these as `"2026-03-07T10:30:00"` (no Z suffix). JavaScript `new Date("2026-03-07T10:30:00")` treats this as local time, adding the local UTC offset (e.g., UTC-5 = 5 hours ahead).

**Existing fix pattern (from WorkoutSummary.vue:18):**
```typescript
const start = new Date(raw.endsWith('Z') ? raw : raw + 'Z').getTime()
```

**Files to fix:**
- `../frontend/src/components/workout/ActiveWorkout.vue` line 239: `new Date(workoutsStore.activeWorkout.started_at).getTime()` -- missing Z suffix
- `../frontend/src/components/history/WorkoutCard.vue` lines 28-29: `new Date(props.workout.started_at)` and `new Date(props.workout.completed_at)` -- missing Z suffix on both
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix UTC datetime parsing in ActiveWorkout.vue and WorkoutCard.vue</name>
  <files>../frontend/src/components/workout/ActiveWorkout.vue, ../frontend/src/components/history/WorkoutCard.vue</files>
  <action>
Repo: ../frontend/

In `src/components/workout/ActiveWorkout.vue`, fix the `durationText` computed (around line 239):
- Change: `const start = new Date(workoutsStore.activeWorkout.started_at).getTime()`
- To: `const raw = workoutsStore.activeWorkout.started_at; const start = new Date(raw.endsWith('Z') ? raw : raw + 'Z').getTime()`
This matches the existing pattern in WorkoutSummary.vue.

In `src/components/history/WorkoutCard.vue`, fix the `durationDisplay` computed (around lines 28-29):
- Change line 28: `const start = new Date(props.workout.started_at)`
- To: `const startRaw = props.workout.started_at; const start = new Date(startRaw.endsWith('Z') ? startRaw : startRaw + 'Z')`
- Change line 29: `const end = new Date(props.workout.completed_at)`
- To: `const endRaw = props.workout.completed_at!; const end = new Date(endRaw.endsWith('Z') ? endRaw : endRaw + 'Z')`

After editing, run `cd ../frontend && npx vue-tsc --noEmit` to verify no type errors.
  </action>
  <verify>
    <automated>cd /Users/vjkim/Code/TEST_GSD/frontend && npx vue-tsc --noEmit 2>&1 | tail -5</automated>
  </verify>
  <done>Both files parse started_at/completed_at with Z-suffix normalization. Type check passes. Elapsed time will show actual duration instead of timezone-offset value.</done>
</task>

</tasks>

<verification>
- grep for `endsWith.*Z` in both modified files confirms the fix is present
- grep for `new Date(props.workout.started_at)` and `new Date(workoutsStore.activeWorkout.started_at)` returns NO matches (old pattern removed)
- `npx vue-tsc --noEmit` passes
</verification>

<success_criteria>
- ActiveWorkout.vue elapsed time calculation uses Z-suffix normalization
- WorkoutCard.vue duration calculation uses Z-suffix normalization on both started_at and completed_at
- No TypeScript errors
</success_criteria>

<output>
After completion, create `.planning/quick/1-fix-workout-elapsed-time-showing-5h-inst/1-SUMMARY.md`
</output>
