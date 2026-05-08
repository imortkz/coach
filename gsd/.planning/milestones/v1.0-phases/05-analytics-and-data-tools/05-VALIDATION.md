---
phase: 5
slug: analytics-and-data-tools
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.0.2 |
| **Config file** | none — pytest auto-discovers in tests/ |
| **Quick run command** | `cd ../scripts && uv run pytest tests/ -x -q` |
| **Full suite command** | `cd ../scripts && uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd ../scripts && uv run pytest tests/ -x -q`
- **After every plan wave:** Run `cd ../scripts && uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 0 | SCRP-03, SCRP-04 | unit | `cd ../scripts && uv run pytest tests/test_analytics.py tests/test_export_import.py -x -q` | No — W0 | pending |
| 05-01-02 | 01 | 1 | SCRP-03a | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_1rm_calculation -x` | No — W0 | pending |
| 05-01-03 | 01 | 1 | SCRP-03b | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_volume_by_muscle_group -x` | No — W0 | pending |
| 05-01-04 | 01 | 1 | SCRP-03c | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_frequency_report -x` | No — W0 | pending |
| 05-01-05 | 01 | 1 | SCRP-03d | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_period_parsing -x` | No — W0 | pending |
| 05-01-06 | 01 | 1 | SCRP-03e | unit | `cd ../scripts && uv run pytest tests/test_analytics.py::test_warmup_exclusion -x` | No — W0 | pending |
| 05-02-01 | 02 | 1 | SCRP-04a | unit | `cd ../scripts && uv run pytest tests/test_export_import.py::test_json_export -x` | No — W0 | pending |
| 05-02-02 | 02 | 1 | SCRP-04b | unit | `cd ../scripts && uv run pytest tests/test_export_import.py::test_csv_export -x` | No — W0 | pending |
| 05-02-03 | 02 | 1 | SCRP-04c | unit | `cd ../scripts && uv run pytest tests/test_export_import.py::test_json_import -x` | No — W0 | pending |
| 05-02-04 | 02 | 1 | SCRP-04d | unit | `cd ../scripts && uv run pytest tests/test_export_import.py::test_import_creates_backup -x` | No — W0 | pending |
| 05-02-05 | 02 | 1 | SCRP-04e | integration | `cd ../scripts && uv run pytest tests/test_export_import.py::test_roundtrip -x` | No — W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_analytics.py` — stubs for SCRP-03 (1RM, volume, frequency query logic)
- [ ] `tests/test_export_import.py` — stubs for SCRP-04 (export formats, import with backup, round-trip)
- [ ] `tests/conftest.py` — add workout/exercise seed data helpers for analytics test fixtures

*Existing conftest.py provides in-memory SQLite pattern; extend with analytics-specific fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rich table visual formatting | SCRP-03 | Visual output styling | Run `gymcoach analytics 1rm` and verify table renders with colors and alignment |
| Import confirmation prompt | SCRP-04 | Interactive CLI prompt | Run `gymcoach import file.json` and verify confirmation prompt appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
