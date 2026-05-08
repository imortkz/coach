---
estimated_steps: 6
estimated_files: 2
---

# T02: Enable swipe on unlogged template sets and route delete correctly

**Slice:** S01 — Fix swipe actions and add template set skipping
**Milestone:** M002

## Description

Unlogged template sets can't be swiped because the swipe guard (`if (isLogged.value || props.isExtra)`) and the action panel `v-if` both exclude them. Relax both guards to include all set rows. Add an `isTemplate` computed for the new case. Route the delete action correctly: template sets emit `removeTemplate` instead of `delete` or `removeExtra`. Bubble the event through ExerciseCard.

## Steps

1. Read `SetRow.vue` — locate the swipe guard in the `useSwipeLeft` callback and the action panel `v-if`
2. Add `isTemplate` computed: `!isLogged && !props.isExtra` (an unlogged, non-extra set is a template set)
3. Relax the swipe guard to allow all rows (remove the condition, or change to `true` / `isLogged || isExtra || isTemplate` which covers everything)
4. Update action panel `v-if` to match (remove the `isLogged || isExtra` restriction, keep `showActions`)
5. In `handleDelete`, add a branch before the existing ones: `if (isTemplate.value) { emit('removeTemplate', { exerciseId: props.exerciseId, setNumber: props.setNumber }); showActions.value = false; return; }`. Define the `removeTemplate` emit.
6. In `ExerciseCard.vue`, listen for `@removeTemplate` on `SetRow` and re-emit it: `emit('removeTemplate', payload)`

## Must-Haves

- [ ] Swipe guard allows unlogged template sets
- [ ] Action panel shows for unlogged template sets
- [ ] `isTemplate` computed exists
- [ ] `handleDelete` branches correctly for template sets (emits `removeTemplate`, not `delete`)
- [ ] `ExerciseCard` re-emits `removeTemplate`
- [ ] Build passes

## Verification

- `cd ../frontend && npm run build` — no errors
- Grep: `removeTemplate` emit defined in SetRow and handled in ExerciseCard

## Inputs

- `../frontend/src/components/workout/SetRow.vue` — T01 output (Edit button already guarded)
- `../frontend/src/components/workout/ExerciseCard.vue` — existing component that renders SetRow instances

## Expected Output

- `../frontend/src/components/workout/SetRow.vue` — swipe enabled for all rows, `removeTemplate` emit added, `isTemplate` computed added
- `../frontend/src/components/workout/ExerciseCard.vue` — `removeTemplate` event forwarded from SetRow
