# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL: Multi-repo directory discipline

This is a planning-only meta repo. All source code lives in sibling directories.

| Repo | Path | Purpose |
|------|------|---------|
| gsd/ | `.` (this repo) | Planning files only (.planning/) — NEVER put source code here |
| backend/ | `../backend/` | Python FastAPI REST API |
| frontend/ | `../frontend/` | VueJS SPA |
| scripts/ | `../scripts/` | Python CLI tools (migrations, seed, analytics) |

Each directory is an independent git repository with `main` as the default branch.

### Rules for all agents (orchestrators, planners, executors)

1. **File writes:** Use relative paths. Source code MUST target `../backend/`, `../frontend/`, or `../scripts/`. Never write `.py`, `.ts`, `.vue`, `.js` files in gsd/.
2. **Git operations:** Always `cd` into the target repo first. Each repo has its own git history.
3. **Commit convention:** Tag every commit with the GSD plan ID `[P{phase}-{plan}]` for cross-repo traceability.
   ```bash
   # Example: plan 01-01 touches backend and scripts
   cd ../backend && git add -A && git commit -m "feat: add exercise models and endpoints [P1-01]"
   cd ../scripts && git add -A && git commit -m "feat: add migration and seed scripts [P1-01]"
   cd ../gsd
   # gsd/ planning commits use gsd-tools as usual (tag is optional here since plan ID is in the message)
   ```
   Search across repos: `git log --grep="P1-01"` in any repo.
4. **Package manager commands:** Run in the correct repo (`cd ../backend && uv ...`, `cd ../frontend && npm ...`).
5. **Reading cross-repo files:** Use relative paths from gsd/ (`../backend/src/...`, `../frontend/src/...`, `../scripts/...`).

### For GSD executor subagents specifically

- You run from gsd/ but your code targets a sibling repo. Every task in a plan specifies which repo to work in.
- Before writing ANY file, confirm the absolute path points to the correct repo.
- After completing work in a sibling repo, commit there (not in gsd/). Always include the `[P{phase}-{plan}]` tag.
- Planning doc updates (.planning/) commit in gsd/ as usual.

## Project: GymCoach

Personal gym training companion — single-user web app for creating exercise programs, logging workouts, and getting auto weight progression suggestions.

- **Stack:** Python FastAPI + SQLAlchemy + SQLite (backend), Vue 3 + Vite + Tailwind (frontend), Click + Rich CLI (scripts)
- **DB:** SQLite with WAL mode, schema managed by Alembic migrations in scripts/
- **Auth:** None (single-user)

## Build & Run (update as repos are scaffolded)

```bash
# Backend
cd ../backend && uv run uvicorn app.main:app --reload

# Frontend
cd ../frontend && npm run dev

# Scripts (migrations)
cd ../scripts && uv run python -m gymcoach_scripts.migrate

# Scripts (seed)
cd ../scripts && uv run python -m gymcoach_scripts.seed
```
