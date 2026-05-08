---
phase: 6
slug: integration-fixes-and-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | scripts/pyproject.toml (implicit) |
| **Quick run command** | `cd ../scripts && uv run pytest tests/test_export_import.py -x` |
| **Full suite command** | `cd ../scripts && uv run pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd ../scripts && uv run pytest tests/test_export_import.py -x`
- **After every plan wave:** Run `cd ../scripts && uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green + no deprecation warnings
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-01-01 | 01 | 1 | SCRP-04 | unit | `cd ../scripts && uv run pytest tests/test_export_import.py::TestImportData::test_round_trip_preserves_program_links -x` | ❌ W0 | ⬜ pending |
| 6-01-02 | 01 | 1 | LOG-04 | manual | Visual check in browser | N/A | ⬜ pending |
| 6-01-03 | 01 | 1 | N/A | unit | `cd ../scripts && uv run python -W error::DeprecationWarning -m pytest tests/ -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_export_import.py::TestImportData::test_round_trip_preserves_program_links` — test that imported workouts reference the correct re-inserted program (not the old program_id)

*Existing infrastructure covers all other phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| rest_timer_disabled toggle visible and functional in program builder | LOG-04 | UI visual check requires browser | 1. Open program builder 2. Verify rest_timer_disabled toggle is visible 3. Toggle it and save 4. Reopen and verify state persisted |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
