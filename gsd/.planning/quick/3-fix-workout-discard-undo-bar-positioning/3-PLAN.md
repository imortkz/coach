---
phase: quick
plan: 3
type: execute
wave: 1
depends_on: []
files_modified:
  - ../frontend/src/components/workout/UndoToast.vue
  - ../frontend/src/components/workout/ActiveWorkout.vue
autonomous: true
requirements: []
must_haves:
  truths:
    - "Undo bar sits snugly just above the bottom nav bar on mobile"
    - "Programs list is visible behind the undo bar during discard countdown"
    - "Undo button still restores the discarded workout"
  artifacts:
    - path: "../frontend/src/components/workout/UndoToast.vue"
      provides: "Repositioned undo toast"
      contains: "bottom-20"
    - path: "../frontend/src/components/workout/ActiveWorkout.vue"
      provides: "ProgramPicker visible during discard"
  key_links:
    - from: "ActiveWorkout.vue discarding state"
      to: "ProgramPicker display"
      via: "v-if discarding shows ProgramPicker"
---

<objective>
Fix two issues with the workout discard undo bar:
1. Position the undo bar just above the bottom nav bar (currently has excessive gap)
2. Show the programs list behind the undo bar during the undo countdown instead of a blank page

Purpose: Better mobile UX -- user sees useful content during undo countdown and the toast doesn't float awkwardly.
Output: Updated UndoToast.vue and ActiveWorkout.vue
</objective>

<execution_context>
@/Users/vjkim/.claude/get-shit-done/workflows/execute-plan.md
@/Users/vjkim/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@../frontend/src/components/workout/UndoToast.vue
@../frontend/src/components/workout/ActiveWorkout.vue
@../frontend/src/views/WorkoutView.vue
@../frontend/src/components/workout/ProgramPicker.vue
@../frontend/src/App.vue
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix undo toast positioning and show programs list during discard</name>
  <files>../frontend/src/components/workout/UndoToast.vue, ../frontend/src/components/workout/ActiveWorkout.vue</files>
  <action>
Two changes:

**UndoToast.vue** -- Fix the bottom positioning class:
- Change `bottom-32 sm:bottom-16` to `bottom-20 sm:bottom-4` on the outer fixed div (line 16).
- The mobile bottom nav is `h-16` (64px). `bottom-20` = 80px, which places the toast 16px above the nav bar. On desktop (sm+), the nav is hidden so `bottom-4` gives standard spacing.

**ActiveWorkout.vue** -- Show ProgramPicker when discarding instead of blank page:
- Add `import ProgramPicker from './ProgramPicker.vue'` to the imports.
- In the template, the `<template v-if="!discarding">` block (line 277) hides all content during discard. Add a sibling block after it: `<ProgramPicker v-else class="pointer-events-none opacity-75" />` -- this shows the programs list in a non-interactive, slightly faded state so the user sees content behind the undo bar but can't accidentally start a new workout. The `@select` event is not bound so clicks do nothing, but `pointer-events-none` prevents interaction entirely.
- The UndoToast at line 339-343 is already outside the `v-if="!discarding"` block, so it will continue to render on top of the ProgramPicker content.
  </action>
  <verify>
    <automated>cd ../frontend && npx vue-tsc --noEmit 2>&1 | head -20</automated>
  </verify>
  <done>
    - UndoToast uses `bottom-20 sm:bottom-4` positioning (sits just above mobile nav)
    - When discarding, ProgramPicker renders (non-interactive, slightly faded) instead of blank page
    - Undo button still works to restore the workout (existing logic unchanged)
  </done>
</task>

</tasks>

<verification>
1. Type check passes: `cd ../frontend && npx vue-tsc --noEmit`
2. Visual: Start a workout, click Discard -- should see programs list (faded) with undo bar sitting just above bottom nav
3. Functional: Clicking Undo restores the workout as before
</verification>

<success_criteria>
- Undo toast positioned just above the bottom nav bar on mobile (no excessive gap)
- Programs list visible (non-interactive) behind the undo bar during discard countdown
- Undo functionality unchanged -- clicking Undo restores the workout
</success_criteria>

<output>
After completion, create `.planning/quick/3-fix-workout-discard-undo-bar-positioning/3-SUMMARY.md`
</output>
