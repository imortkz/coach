---
id: T01
parent: S01
milestone: M002
provides:
  - Edit button in swipe action panel is conditionally rendered only for logged sets
key_files:
  - ../frontend/src/components/workout/SetRow.vue
key_decisions:
  - none
patterns_established:
  - none
observability_surfaces:
  - none
duration: ~5 minutes
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T01: Guard Edit button on isLogged and fix action panel conditions

**Added `v-if="isLogged"` to the Edit button in SetRow.vue's swipe action panel so it only renders for logged sets.**

## What Happened

Located the Edit button in the swipe action panel (line ~304 of SetRow.vue). Added `v-if="isLogged"` attribute to the button element. The action panel container already had `v-if="showActions && (isLogged || isExtra)"`, but the Edit button inside was rendered unconditionally — meaning for extra (unlogged) sets the Edit button would appear even though `enterEditMode()` silently no-ops when `!isLogged`.

## Verification

- `cd ../frontend && npm run build` — passed, no errors (✓ built in 1.16s)
- Grep confirmed: Edit button element in SetRow.vue now has `v-if="isLogged"` guard

## Diagnostics

none

## Deviations

none

## Known Issues

none

## Files Created/Modified

- `../frontend/src/components/workout/SetRow.vue` — Added `v-if="isLogged"` to Edit button in swipe action panel
