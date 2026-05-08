---
phase: 3
slug: workout-logging
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend), Vitest (frontend -- if configured) |
| **Config file** | pytest: ../backend/pyproject.toml; vitest: ../frontend/vitest.config.ts |
| **Quick run command** | `cd ../backend && uv run pytest tests/test_workouts.py -x --tb=short` |
| **Full suite command** | `cd ../backend && uv run pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd ../backend && uv run pytest tests/test_workouts.py -x --tb=short`
- **After every plan wave:** Run `cd ../backend && uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | LOG-01 | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_start_workout -x` | Wave 0 | pending |
| 3-01-02 | 01 | 1 | LOG-01 | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_active_workout -x` | Wave 0 | pending |
| 3-01-03 | 01 | 1 | LOG-02 | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_log_set -x` | Wave 0 | pending |
| 3-01-04 | 01 | 1 | LOG-02 | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_prefill_last_session -x` | Wave 0 | pending |
| 3-01-05 | 01 | 1 | LOG-03 | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_update_set -x` | Wave 0 | pending |
| 3-01-06 | 01 | 1 | LOG-03 | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_delete_set -x` | Wave 0 | pending |
| 3-01-07 | 01 | 1 | LOG-03 | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_delete_exercise_sets -x` | Wave 0 | pending |
| 3-01-08 | 01 | 1 | LOG-03 | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_discard_workout -x` | Wave 0 | pending |
| 3-01-09 | 01 | 1 | LOG-04 | integration | `cd ../backend && uv run pytest tests/test_workouts.py::test_settings_crud -x` | Wave 0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `../backend/tests/test_workouts.py` — stubs for LOG-01, LOG-02, LOG-03, LOG-04
- [ ] `../backend/tests/conftest.py` — workout/program fixtures (extend if exists)
- [ ] Verify pytest is in backend dev dependencies

*Wave 0 creates test stubs that initially fail, then pass as implementation lands.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rest timer UI countdown | LOG-04 | Visual timer + browser notification | 1. Log a set 2. Verify floating bar appears with countdown 3. Wait for completion, check browser notification 4. Test skip button |
| Tap-to-complete UX | LOG-02 | Touch interaction | 1. Tap set row to complete with pre-filled values 2. Tap weight/reps to edit before completing |
| Swipe-to-edit/delete | LOG-03 | Touch interaction | 1. Swipe left on logged set (mobile) 2. Verify edit/delete actions appear |
| Undo toast on delete | LOG-03 | Visual + timing | 1. Delete a set 2. Verify undo toast appears 3. Tap undo within timeout 4. Verify set restored |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
