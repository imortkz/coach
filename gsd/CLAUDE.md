# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL: Multi-repo directory discipline

This is a planning-only meta repo. All source code lives in sibling directories.

| Repo | Path | Purpose |
|------|------|---------|
| gsd/ | `.` (this repo) | Planning files only (.planning/, .gsd/) — NEVER put source code here |
| backend/ | `../backend/` | Python FastAPI REST API + MongoDB (Beanie ODM) + Telegram auth |
| frontend/ | `../frontend/` | Vue 3 + Vite + Tailwind SPA |

> **Note:** The `scripts/` repo (Python CLI for SQLite Alembic migrations / seed / analytics) was **deleted in M001 (S10)** as part of the SQLite → MongoDB migration. Beanie handles schema natively at startup; seed lives in `backend/app/seed.py`. Do not recreate scripts/ or reference it in new plans.

Each directory is an independent git repository with `main` as the default branch.

### Rules for all agents (orchestrators, planners, executors)

1. **File writes:** Use relative paths. Source code MUST target `../backend/` or `../frontend/`. Never write `.py`, `.ts`, `.vue`, `.js` files in gsd/.
2. **Git operations:** Always `cd` into the target repo first. Each repo has its own git history.
3. **Commit convention:** Tag every commit with the GSD plan ID `[P{phase}-{plan}]` for cross-repo traceability.
   ```bash
   # Example: plan 01-01 touches backend and frontend
   cd ../backend && git add -A && git commit -m "feat: add exercise models and endpoints [P1-01]"
   cd ../frontend && git add -A && git commit -m "feat: wire exercise list to new endpoint [P1-01]"
   cd ../gsd
   # gsd/ planning commits use gsd-tools as usual (tag is optional here since plan ID is in the message)
   ```
   Search across repos: `git log --grep="P1-01"` in any repo.
4. **Package manager commands:** Run in the correct repo (`cd ../backend && uv ...`, `cd ../frontend && npm ...`).
5. **Reading cross-repo files:** Use relative paths from gsd/ (`../backend/app/...`, `../frontend/src/...`).

### For GSD executor subagents specifically

- You run from gsd/ but your code targets a sibling repo. Every task in a plan specifies which repo to work in.
- Before writing ANY file, confirm the absolute path points to the correct repo.
- After completing work in a sibling repo, commit there (not in gsd/). Always include the `[P{phase}-{plan}]` tag.
- Planning doc updates (.planning/) commit in gsd/ as usual.

## Project: GymCoach

Personal gym training companion — multi-user web app (single-user in v1.0, multi-user since M001/v1.1) for creating exercise programs, logging workouts, getting auto weight progression suggestions, and browsing an EN/RU localized exercise library.

- **Stack:** Python FastAPI + Beanie ODM + MongoDB 8.0 (backend); Vue 3 + Vite + Tailwind + vue-i18n v9 (frontend); nginx multi-stage build (serves SPA + reverse-proxies `/api/*`)
- **DB:** MongoDB with named volume `mongodb_data`. 4 document collections: users, exercises, programs (with embedded `versions[]` snapshots), workouts (denormalized exercise fields per WorkoutSet), settings. Compound indexes + idempotent seed (~150 exercises) created at FastAPI startup via `_startup_tasks()`.
- **Auth:** Telegram Login Widget (HMAC-SHA-256) → JWT in localStorage (365-day expiry). `DEV_MODE=true` bypasses auth for localhost development. Production requires registered domain via `@BotFather /setdomain` and HTTPS (M004 will add Let's Encrypt).
- **Localization:** EN/RU via vue-i18n v9. Language preference persisted via `PUT/GET /api/settings/language`. Use `useDisplayName(exercise)` composable for exercise names; `t('muscle_groups.X')` for muscle group labels.

## Build & Run

The full stack runs via Docker Compose at the parent directory level (the only supported dev mode after M001):

```bash
# From the parent directory (one level up from gsd/, backend/, frontend/, nginx/):
docker compose up --build
# Reaches: http://localhost (nginx serves Vue SPA + proxies /api/* to FastAPI)
# DEV_MODE=true by default — Telegram auth bypassed; dev-login button on login screen.
# MongoDB is exposed on host port 27018 (not 27017) to avoid conflict with any local MongoDB instance.
```

Per-repo development without Docker (rare; the dev path is `docker compose up`):

```bash
# Backend (requires MongoDB running locally on 27017 or container on 27018):
cd ../backend && uv run uvicorn app.main:app --reload

# Frontend (separate Vite dev server; expects backend at default base URL):
cd ../frontend && npm run dev
```

Backend test suite (after `docker compose up -d mongodb` or local mongod running):

```bash
cd ../backend && uv run pytest tests/ -q   # 64 passed at last clean run (M003 completion)
```

Frontend build smoke check:

```bash
cd ../frontend && npm run build            # Should be clean: 110 modules, 0 errors
```

Production deployment lives in `../docker-compose.prod.yml` and `../DEPLOYMENT.md` — domain + Telegram bot setup + JWT_SECRET required. SSL/HTTPS not yet automated (deferred to M004 with Let's Encrypt + Certbot sidecar).
