---
phase: 2
slug: exercise-and-program-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.0 (backend), vitest ^4.0 (frontend) |
| **Config file** | backend: auto-discovers tests/, frontend: vite.config.ts |
| **Quick run command** | `cd ../backend && uv run pytest tests/ -x -q` |
| **Full suite command** | `cd ../backend && uv run pytest tests/ -v && cd ../frontend && npx vitest run` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd ../backend && uv run pytest tests/ -x -q`
- **After every plan wave:** Run `cd ../backend && uv run pytest tests/ -v && cd ../frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | EXER-01 | unit (API) | `cd ../backend && uv run pytest tests/test_exercises.py -x` | No — W0 | pending |
| 02-01-02 | 01 | 1 | EXER-02 | unit (API) | `cd ../backend && uv run pytest tests/test_exercises.py -x` | No — W0 | pending |
| 02-02-01 | 02 | 1 | PROG-01 | unit (API) | `cd ../backend && uv run pytest tests/test_programs.py -x` | No — W0 | pending |
| 02-02-02 | 02 | 1 | PROG-02 | unit (API) | `cd ../backend && uv run pytest tests/test_programs.py -x` | No — W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `../backend/tests/test_exercises.py` — stubs for EXER-01, EXER-02
- [ ] `../backend/tests/test_programs.py` — stubs for PROG-01, PROG-02
- [ ] `../backend/tests/conftest.py` — shared fixtures (test DB session, seed data)
- [ ] Frontend vitest config verification — ensure vitest runs from vite.config.ts

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Exercise grouped list UI with collapsible sections | EXER-01 | Visual layout verification | Open /exercises, verify exercises grouped by muscle group, expand/collapse sections |
| Inline custom exercise creation form | EXER-02 | Interactive UI flow | Click [+] on muscle group section, fill name + equipment, verify exercise appears |
| Program builder with per-set targets | PROG-01 | Complex interactive form | Create program at /programs/new, add exercises, configure per-set reps/weight/warmup |
| Responsive navigation (top navbar / bottom tab bar) | All | Viewport-dependent layout | Resize browser, verify navbar on desktop and tab bar on mobile |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
