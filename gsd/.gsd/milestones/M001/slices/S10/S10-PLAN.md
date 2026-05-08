# S10: Cleanup

**Goal:** Remove unused backend dependencies, fix Dockerfile base image, delete scripts repo — clean MongoDB-only codebase.
**Demo:** `uv run pytest` passes 59 tests; `docker compose up --build` works; scripts/ directory does not exist.

## Must-Haves
- `passlib` absent from `backend/pyproject.toml` and `uv.lock`
- `backend/Dockerfile` uses `python:3.13-slim` base image
- No SQLAlchemy or Alembic references anywhere in backend/
- `scripts/` directory deleted from disk
- 59 backend tests still pass
- M001 marked complete in roadmap

## Tasks

- [x] **T01: Remove passlib, fix Dockerfile, delete scripts/, verify**
  Remove passlib via `uv remove`, update Dockerfile base image, delete scripts/ directory, run tests, verify Docker build.
