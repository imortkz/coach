---
phase: 4
slug: history-and-progression
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (backend), vitest 4.x (frontend) |
| **Config file** | backend: pyproject.toml, frontend: vitest.config.ts |
| **Quick run command** | `cd ../backend && uv run pytest tests/test_workouts.py -x` |
| **Full suite command** | `cd ../backend && uv run pytest tests/ -x` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd ../backend && uv run pytest tests/test_workouts.py -x`
- **After every plan wave:** Run `cd ../backend && uv run pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | HIST-01 | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestListWorkouts -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | HIST-01 | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestListWorkouts::test_filter_by_program -x` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | HIST-02 | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestExerciseHistory -x` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | PRGS-01 | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestProgression::test_suggestion_in_prefill -x` | ❌ W0 | ⬜ pending |
| 04-01-05 | 01 | 1 | PRGS-02 | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestProgression::test_suggest_increase -x` | ❌ W0 | ⬜ pending |
| 04-01-06 | 01 | 1 | PRGS-02 | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestProgression::test_keep_weight -x` | ❌ W0 | ⬜ pending |
| 04-01-07 | 01 | 1 | PRGS-02 | unit | `cd ../backend && uv run pytest tests/test_workouts.py::TestProgression::test_bodyweight_rep_increase -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_workouts.py::TestListWorkouts` — stubs for HIST-01 (paginated list, program filter)
- [ ] `tests/test_workouts.py::TestExerciseHistory` — stubs for HIST-02 (per-exercise session data)
- [ ] `tests/test_workouts.py::TestProgression` — stubs for PRGS-01, PRGS-02 (suggestion computation, equipment increments, edge cases)

*Existing test infrastructure (conftest.py, fixtures) covers all needs. No new dependencies required.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| History card expand/collapse | HIST-01 | Visual UI interaction | Open /history, tap a card, verify it expands with exercise details |
| Chart rendering (weight + volume) | HIST-02 | Visual chart display | Navigate to /exercises/:id/history, verify chart shows two lines |
| Progression arrow indicator | PRGS-01 | Visual UI indicator | Start workout after hitting all reps, verify ↑ arrow on suggested weight |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
