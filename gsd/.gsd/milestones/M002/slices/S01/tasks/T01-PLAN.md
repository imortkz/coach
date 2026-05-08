---
estimated_steps: 3
estimated_files: 1
---

# T01: Guard Edit button on isLogged and fix action panel conditions

**Slice:** S01 — Fix swipe actions and add template set skipping
**Milestone:** M002

## Description

The Edit button in the swipe action panel calls `enterEditMode()` which silently no-ops when the set isn't logged (`if (!isLogged.value || !props.loggedSet) return`). The button should not be rendered at all for unlogged sets. Add a `v-if="isLogged"` guard on the Edit button element.

## Steps

1. Read `../frontend/src/components/workout/SetRow.vue` and locate the Edit button in the swipe action panel
2. Add `v-if="isLogged"` to the Edit button element
3. Verify the build passes

## Must-Haves

- [ ] Edit button has `v-if="isLogged"` or equivalent conditional
- [ ] Build passes without errors

## Verification

- `cd ../frontend && npm run build` — no errors
- Grep: Edit button element in SetRow.vue has `v-if` guard referencing `isLogged`

## Inputs

- `../frontend/src/components/workout/SetRow.vue` — existing swipe action panel with Edit and Delete buttons

## Expected Output

- `../frontend/src/components/workout/SetRow.vue` — Edit button conditionally rendered only for logged sets
