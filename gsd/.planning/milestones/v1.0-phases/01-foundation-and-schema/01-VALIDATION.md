---
phase: 1
slug: foundation-and-schema
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (backend/scripts), Vitest 3.x (frontend) |
| **Config file** | None — Wave 0 must create pytest.ini / vitest.config.ts |
| **Quick run command** | `cd ../backend && uv run pytest -x -q` / `cd ../scripts && uv run pytest -x -q` / `cd ../frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd ../backend && uv run pytest` && `cd ../scripts && uv run pytest` && `cd ../frontend && npx vitest run` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command for affected repo
- **After every plan wave:** Run full suite across all repos
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | SCRP-01 | integration | `cd ../scripts && uv run pytest tests/test_migrations.py -x` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | SCRP-02 | integration | `cd ../scripts && uv run pytest tests/test_seed.py -x` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | HEALTH | smoke | `cd ../backend && uv run pytest tests/test_health.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `../scripts/tests/conftest.py` — shared fixtures (test DB engine, session)
- [ ] `../scripts/tests/test_migrations.py` — stubs for SCRP-01
- [ ] `../scripts/tests/test_seed.py` — stubs for SCRP-02
- [ ] `../backend/tests/conftest.py` — test client, test DB
- [ ] `../backend/tests/test_health.py` — covers health endpoint
- [ ] `../scripts/pyproject.toml` — pytest dependency
- [ ] `../backend/pyproject.toml` — pytest dependency

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Vue frontend renders a page | HEALTH | Browser-only render verification | Start `npm run dev`, open localhost, confirm page renders |
| SQLite WAL mode enabled | SCRP-01 | PRAGMA verification after migration | Run migration, then `sqlite3 ../data/gymcoach.db "PRAGMA journal_mode;"` — expect "wal" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
