---
phase: quick
plan: 2
type: execute
wave: 1
depends_on: []
files_modified:
  - ../frontend/src/components/workout/ActiveWorkout.vue
autonomous: true
requirements: [QUICK-2]

must_haves:
  truths:
    - "Elapsed time in workout header ticks live, updating every minute"
    - "Timer shows correct elapsed time immediately on mount"
    - "Interval is cleaned up when component unmounts (no memory leak)"
  artifacts:
    - path: "../frontend/src/components/workout/ActiveWorkout.vue"
      provides: "Reactive elapsed timer with setInterval"
      contains: "setInterval"
  key_links:
    - from: "setInterval tick"
      to: "durationText computed"
      via: "reactive ref that increments each minute"
      pattern: "setInterval.*60000"
---

<objective>
Make the workout elapsed timer tick live instead of showing a stale value.

Purpose: The `durationText` computed in ActiveWorkout.vue uses `Date.now()` but has no reactive dependency that changes over time, so it only evaluates once on mount. Adding a reactive "now" ref that updates via setInterval will cause the computed to re-evaluate every minute.

Output: ActiveWorkout.vue with a live-ticking elapsed time display.
</objective>

<execution_context>
@/Users/vjkim/.claude/get-shit-done/workflows/execute-plan.md
@/Users/vjkim/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@../frontend/src/components/workout/ActiveWorkout.vue
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add reactive timer tick to ActiveWorkout.vue</name>
  <files>../frontend/src/components/workout/ActiveWorkout.vue</files>
  <action>
  In ActiveWorkout.vue (repo: ../frontend/):

  1. Add `onUnmounted` to the import from 'vue' (line 2 already imports `ref, computed, onMounted, provide`).

  2. Add a reactive `now` ref initialized to `Date.now()` and a `setInterval` that updates it every 60000ms. Also set up cleanup in `onUnmounted`:

  ```typescript
  const now = ref(Date.now())
  let tickInterval: ReturnType<typeof setInterval> | null = null

  onMounted(() => {
    // Update "now" every minute so durationText recomputes
    tickInterval = setInterval(() => {
      now.value = Date.now()
    }, 60000)
  })

  // Place the onMounted timer setup INSIDE or AFTER the existing onMounted block.
  // Actually, add a separate onMounted for clarity, OR merge into the existing one.
  // Preferred: add to the existing onMounted at line 61.

  onUnmounted(() => {
    if (tickInterval !== null) {
      clearInterval(tickInterval)
      tickInterval = null
    }
  })
  ```

  3. Update the `durationText` computed (lines 237-247) to use `now.value` instead of `Date.now()`:
  Change `const now = Date.now()` inside the computed to `const nowMs = now.value` (using the reactive ref).

  Key points:
  - The `now` ref is the reactive dependency that makes the computed re-evaluate.
  - The interval fires every 60 seconds (matching the minute-level display granularity).
  - `onUnmounted` clears the interval to prevent memory leaks.
  - Merge the setInterval setup into the existing `onMounted` callback at line 61 to keep things clean.
  </action>
  <verify>
    <automated>cd /Users/vjkim/Code/TEST_GSD/frontend && npx vue-tsc --noEmit 2>&1 | head -20</automated>
  </verify>
  <done>durationText uses a reactive `now` ref updated by setInterval every 60s. Interval cleared on unmount. Type-checks pass.</done>
</task>

</tasks>

<verification>
- `vue-tsc --noEmit` passes with no type errors
- ActiveWorkout.vue contains `setInterval` and `onUnmounted` with `clearInterval`
- `durationText` computed references the reactive `now` ref (not raw `Date.now()`)
</verification>

<success_criteria>
The elapsed time display in the active workout header updates every minute without requiring page refresh. The interval is properly cleaned up on component unmount.
</success_criteria>

<output>
After completion, create `.planning/quick/2-make-workout-elapsed-timer-reactive-with/2-SUMMARY.md`
</output>
