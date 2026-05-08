# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-07
**Phases:** 6 | **Plans:** 16 | **LOC:** ~8,310

### What Was Built
- Full-stack gym training app with exercise library, program builder, and workout logging
- Tap-to-complete workout flow with rest timer, swipe gestures, and undo interactions
- Workout history with expandable cards, per-exercise charts, and progression suggestions
- CLI analytics (1RM trends, volume by muscle group, workout frequency) and JSON/CSV export/import
- Multi-repo architecture: FastAPI backend, Vue 3 frontend, Python scripts

### What Worked
- Multi-repo GSD orchestration: parallel subagent execution across backend/frontend/scripts repos worked cleanly
- Phase dependency chain (schema → CRUD → logging → history → analytics) avoided integration issues until the final polish phase
- TDD approach in scripts repo caught the import FK mapping bug before it hit production
- Z suffix normalization pattern (discovered in WorkoutSummary.vue) was reusable across components

### What Was Inefficient
- Milestone audit found integration gaps (import FK mapping, missing UI toggle) that could have been caught earlier with cross-phase integration tests
- Naive UTC datetime decision caused frontend parsing bugs in multiple components — same fix applied 3 times
- Phase 6 was entirely gap closure that could have been avoided with better Phase 3/5 planning

### Patterns Established
- `[P{phase}-{plan}]` commit tags for cross-repo traceability
- `[PQ-{num}]` tags for quick task commits
- Z suffix normalization for naive UTC datetimes from backend
- Quick task workflow for post-milestone bug fixes

### Key Lessons
1. Naive UTC datetimes without timezone info cause JavaScript Date parsing issues — always append Z suffix or use timezone-aware datetimes
2. Cross-phase integration testing (especially import/export round-trips) should be part of the phase that implements the feature, not deferred
3. UI toggles for backend-supported features should be included in the same phase as the backend work

### Cost Observations
- Model mix: ~30% opus (orchestration), ~70% sonnet (research, execution, verification)
- Sessions: 4 (new-project, phases 1-3, phases 4-6 + audit, phase 6 + quick tasks + milestone)
- Notable: 16 plans across 6 phases completed in 2 days — multi-repo parallelization effective

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 4 | 6 | Initial baseline — multi-repo orchestration established |

### Cumulative Quality

| Milestone | Tests | Coverage | Integration Gaps |
|-----------|-------|----------|-----------------|
| v1.0 | ~30 | Partial | 2 (closed in Phase 6) |

### Top Lessons (Verified Across Milestones)

1. Always normalize datetime serialization at the boundary (backend → frontend)
2. Include integration tests in the phase that implements the feature
