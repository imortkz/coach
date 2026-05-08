---
id: T01
parent: S10
milestone: M001
provides:
  - passlib removed from backend/pyproject.toml and uv.lock
  - backend/Dockerfile base image updated to python:3.13-slim
  - scripts/ directory deleted from disk
  - 59 backend tests still passing
  - Docker backend image builds successfully on Python 3.13
requires:
  - slice: S09
    provides: docker-compose.yml, docker-compose.prod.yml, nginx proxy, seed.py, 59 passing tests
key_files:
  - ../backend/pyproject.toml
  - ../backend/Dockerfile
key_decisions:
  - "Deleted scripts/ entirely (no tag, no archive) per user instruction"
  - "Dockerfile base image changed from python:3.12-slim to python:3.13-slim; uv resolves Python 3.13 correctly inside the container"
patterns_established: []
drill_down_paths:
  - .gsd/milestones/M001/slices/S10/S10-PLAN.md
duration: ~10min
verification_result: pass
completed_at: 2026-03-13
---

# T01: Remove passlib, fix Dockerfile, delete scripts/

**passlib removed from pyproject.toml (unused dep), Dockerfile base image fixed to python:3.13-slim, scripts/ directory deleted — 59 tests pass, Docker build confirmed on Python 3.13.**

## What Happened

Three mechanical changes with no behavior impact:

1. `uv remove passlib` — passlib was listed in pyproject.toml but never imported anywhere in app code. Likely added speculatively during S08 auth planning before Telegram HMAC (stdlib) replaced any password hashing need. `uv remove` updated both pyproject.toml and uv.lock cleanly.

2. Dockerfile base image `python:3.12-slim` → `python:3.13-slim` — pyproject.toml has required `>=3.13` since S07, but the Dockerfile pulled a 3.12 base. uv's resolver was already fetching Python 3.13 at install time (confirmed via `docker run python --version` → 3.13.12), so this was always cosmetically wrong. Now the base image and the project requirement agree.

3. `rm -rf ../scripts/` — entire scripts repo deleted. Seed data is authoritative in `backend/app/seed.py` (S09). Analytics/export/import are deferred to a future milestone.

## Deviations

None — executed exactly as scoped in S10-CONTEXT.md.

## Files Created/Modified

- `../backend/pyproject.toml` — passlib removed from dependencies
- `../backend/uv.lock` — regenerated without passlib
- `../backend/Dockerfile` — base image changed to python:3.13-slim
- `../scripts/` — deleted
