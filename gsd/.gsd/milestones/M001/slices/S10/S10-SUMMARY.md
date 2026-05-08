---
id: S10
parent: M001
milestone: M001
provides:
  - passlib removed from backend/pyproject.toml (unused dep)
  - backend/Dockerfile base image corrected to python:3.13-slim
  - scripts/ directory deleted from disk entirely
  - Clean MongoDB-only backend with no legacy SQLite/Alembic artifacts
requires:
  - slice: S09
    provides: docker-compose stack, nginx proxy, seed.py, compound indexes, 59 passing tests
affects: []
key_files:
  - ../backend/pyproject.toml
  - ../backend/Dockerfile
key_decisions:
  - scripts/ deleted entirely (no tag, no archive) — user decision
  - analytics/export functionality deferred to a future milestone
  - python-dotenv retained (harmless, cost-free to leave)
patterns_established: []
observability_surfaces:
  - uv run pytest tests/ -q → 59 passed
  - docker build ./backend → python:3.13-slim confirmed
drill_down_paths:
  - .gsd/milestones/M001/slices/S10/tasks/T01-SUMMARY.md
duration: ~15min
verification_result: passed
completed_at: 2026-03-13
---

# S10: Cleanup

**passlib removed, Dockerfile base fixed to python:3.13-slim, scripts/ deleted — clean MongoDB-only codebase, 59 tests pass, M001 complete.**

## What Happened

Final cleanup sweep for M001. Three targeted changes, no behavior impact:

- **`passlib` removed** via `uv remove passlib`. It was listed in pyproject.toml from S08 auth planning but never imported in any app code (Telegram HMAC uses stdlib `hashlib`/`hmac`; JWT uses `python-jose`). Clean removal, uv.lock regenerated.

- **Dockerfile base image fixed**: `python:3.12-slim` → `python:3.13-slim`. pyproject.toml has required `>=3.13` since S07; the base image mismatch was cosmetic but misleading. Docker build confirmed Python 3.13.12 in the resulting container.

- **`scripts/` deleted**: `rm -rf ../scripts/`. The repo contained SQLAlchemy-based Alembic migrations, Click CLI tools, and analytics/export/import scripts — all SQLite-dependent and superseded. Seed data now lives in `backend/app/seed.py` (S09). Analytics and export are deferred.

## Verification

- `uv run pytest tests/ -q` → **59 passed** (no regressions)
- `docker build ./backend` → success; `python --version` inside container → Python 3.13.12
- `grep passlib backend/pyproject.toml` → no output
- `ls ../scripts/` → no such directory

## Requirements Validated

- CLN-01 — SQLAlchemy/Alembic absent from backend/pyproject.toml ✓ (was already clean from S07; verified)
- CLN-02 — Scripts repo deleted from disk ✓

## Deviations

None.

## Known Limitations

- `python-dotenv` remains in deps — it's harmless and used by `python-dotenv` conventions even though `config.py` uses `os.environ` directly. Not worth the risk of removing.
- Analytics/export/import functionality from the scripts repo is not yet available as backend endpoints. Deferred to a future milestone.

## Files Created/Modified

- `../backend/pyproject.toml` — passlib removed
- `../backend/uv.lock` — regenerated
- `../backend/Dockerfile` — base image python:3.13-slim
- `../scripts/` — deleted
