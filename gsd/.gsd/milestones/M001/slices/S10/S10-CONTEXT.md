---
id: S10
milestone: M001
status: ready
---

# S10: Cleanup — Context

## Goal

Remove unused backend dependencies, fix the Dockerfile base image, and delete the scripts repo — leaving a clean MongoDB-only codebase with no SQLite/legacy artifacts.

## Why this Slice

S09 proved the Docker stack works end-to-end. S10 is the final sweep: the milestone's success criteria include "legacy SQLite/SQLAlchemy dependencies removed; scripts repo archived." Without it, M001 is incomplete and the codebase carries dead weight that will confuse future work.

## Scope

### In Scope

- Remove `passlib` from `backend/pyproject.toml` (unused — no password hashing in a Telegram-auth app)
- Fix `backend/Dockerfile` base image: `python:3.12-slim` → `python:3.13-slim` (pyproject.toml requires `>=3.13`; mismatch is cosmetic but misleading)
- Delete the `scripts/` repo directory from disk entirely — all its functionality is either superseded (seed data now in backend/app/seed.py) or deferred (analytics, export/import to a future milestone)
- Verify `backend/pyproject.toml` has no SQLAlchemy/Alembic references (expected: already clean since S07)
- Rebuild and verify Docker stack still passes after changes (`docker compose up --build`, 59 tests pass)
- Update M001 roadmap, STATE.md, REQUIREMENTS.md to reflect milestone completion

### Out of Scope

- Porting analytics reports to the web app — deferred to a future milestone
- Porting JSON/CSV export/import to backend endpoints — deferred to a future milestone
- python-dotenv removal — it's in deps and harmless; not worth the risk of breaking anything
- Any new features or behavior changes
- SSL/TLS, CI/CD, MongoDB auth credentials — all deferred

## Constraints

- Must not change any behavior — this is purely cleanup
- 59 backend tests must still pass after every change
- `docker compose up --build` must still produce a working stack
- `DEV_MODE=true` default behavior must be preserved in dev compose
- The authoritative exercise seed is now `backend/app/seed.py` — deleting scripts/ must not break seeding

## Integration Points

### Consumes

- `../backend/pyproject.toml` — source of truth for backend dependencies; passlib to be removed
- `../backend/Dockerfile` — base image to be updated to python:3.13-slim
- `../scripts/` — entire directory to be deleted from disk
- `../backend/app/seed.py` — confirm it is the authoritative seed source before scripts/ is deleted

### Produces

- `../backend/pyproject.toml` — passlib removed, regenerated uv.lock
- `../backend/Dockerfile` — python:3.13-slim base image
- `../scripts/` — deleted (no longer exists)
- M001 marked complete in roadmap and STATE.md

## Open Questions

- None — all decisions resolved in interview.
  - "Archive" means delete scripts/ from disk entirely (user confirmed)
  - analytics/export functionality is deferred, not ported (user confirmed)
  - backend cleanup scope is passlib + Dockerfile base image only (user confirmed)
