---
id: S09
parent: M001
milestone: M001
provides:
  - docker-compose.yml (dev, DEV_MODE=true, MongoDB port 27018 exposed)
  - docker-compose.prod.yml (production, DEV_MODE=false, MongoDB internal only)
  - nginx/Dockerfile (multi-stage: Vue SPA build + nginx reverse proxy)
  - nginx/nginx.conf (reverse proxy /api/* to backend, SPA try_files fallback)
  - .env.example (JWT_SECRET, TELEGRAM_BOT_TOKEN, VITE_TELEGRAM_BOT_NAME documented)
  - DEPLOYMENT.md (Telegram bot setup, VPS steps, backup/restore, troubleshooting)
  - backend/app/seed.py (50 exercises, idempotent startup seed)
  - Compound indexes (workouts: user_id+completed_at, settings: user_id+key unique) created at startup
requires:
  - slice: S08
    provides: Auth layer, JWT, DEV_MODE bypass, user_id on all documents, 59 passing tests
affects:
  - S10
key_files:
  - ../docker-compose.yml
  - ../docker-compose.prod.yml
  - ../nginx/Dockerfile
  - ../nginx/nginx.conf
  - ../.env.example
  - ../DEPLOYMENT.md
  - ../backend/app/seed.py
  - ../backend/app/main.py
key_decisions:
  - nginx/Dockerfile uses parent-directory build context (context: .) so frontend/ and nginx/ are both accessible in a single multi-stage build
  - Dev compose exposes MongoDB on host port 27018 (not 27017) to avoid conflict with local MongoDB instance
  - Prod compose does NOT expose MongoDB port — Docker network isolation only
  - Seed runs at FastAPI startup via lifespan; idempotent (checks count before inserting)
  - Compound indexes created programmatically in _startup_tasks() at every startup (idempotent via MongoDB create_index)
patterns_established:
  - Single nginx container owns both reverse proxy and SPA serving (not frontend Dockerfile)
  - _startup_tasks() in main.py lifespan for one-time DB setup work (seed + indexes)
observability_surfaces:
  - GET /api/health — {"status":"ok","database":"connected"} through nginx proxy
  - docker compose logs backend — see seed count and startup errors
  - docker compose ps — verify all 3 containers running
drill_down_paths:
  - .gsd/milestones/M001/slices/S09/tasks/
duration: ~1 session
verification_result: passed
completed_at: 2026-03-13
---

# S09: Docker Deployment

**`docker compose up --build` from the parent directory starts nginx + FastAPI + MongoDB as 3 containers; nginx serves the Vue SPA and proxies /api/* to backend; MongoDB data persists in a named volume; 50 exercises seeded on first startup; 59 backend tests still passing.**

## What Happened

S09 created all Docker deployment infrastructure at the parent directory (`../`) level, producing a working 3-service stack from a single `docker compose up --build`.

**nginx/Dockerfile (multi-stage):** The nginx container now owns both the SPA build and the reverse proxy. Stage 1 uses `node:20-slim` to `npm run build` the Vue frontend with `VITE_TELEGRAM_BOT_NAME` as a build arg. Stage 2 copies the `dist/` output into `nginx:1.28-alpine` alongside `nginx/nginx.conf`. This keeps the frontend Dockerfile unchanged (it still works as a standalone SPA server) while the Docker Compose stack uses the dedicated nginx container for the full reverse proxy + SPA setup.

**nginx.conf:** `/api/*` proxied to `http://backend:8000` with forwarding headers. All other routes use `try_files $uri $uri/ /index.html` for SPA client-side routing.

**docker-compose.yml (dev):** MongoDB 8.0 with named volume, MongoDB healthcheck using `mongosh ping`, backend `depends_on: service_healthy`, nginx builds from `nginx/Dockerfile` with `VITE_TELEGRAM_BOT_NAME` build arg. MongoDB port exposed on host 27018 (not 27017 — local MongoDB already binds that port). `DEV_MODE=true`.

**docker-compose.prod.yml (production):** Same structure, `DEV_MODE=false`, MongoDB port NOT exposed, `JWT_SECRET`/`TELEGRAM_BOT_TOKEN`/`VITE_TELEGRAM_BOT_NAME` required from `.env` (no defaults).

**backend/app/seed.py:** 50 exercises extracted from the legacy `scripts/` repo seed file. `seed_exercises_if_empty()` is async, checks count of shared exercises (user_id=None) before inserting — no-op if data already exists.

**backend/app/main.py `_startup_tasks()`:** Called from the FastAPI lifespan after `init_db()`. Seeds exercises if empty. Creates compound indexes `workouts_user_completed (user_id, completed_at)` and `settings_user_key (user_id, key)` — both idempotent.

**.env.example + DEPLOYMENT.md:** Full Telegram bot setup walkthrough (BotFather `/newbot`, `/setdomain` for bare IP), VPS deployment steps, JWT_SECRET generation command, backup/restore via mongodump, troubleshooting guide.

## Verification

- `uv run pytest tests/ -q` → **59 passed** (no regressions from startup task additions)
- `docker compose up --build` from `../` → all 3 containers start, MongoDB health check passes, backend reaches "Application startup complete"
- `curl http://localhost/api/health` → `{"status":"ok","database":"connected"}`
- `curl -L http://localhost/api/exercises/` → 50 exercises returned (seed confirmed)
- `POST http://localhost/api/auth/dev-login` + `GET /api/auth/me` with JWT → returns dev user (end-to-end proxy confirmed)
- `curl -I http://localhost/workouts/some-route` → HTTP 200 (SPA fallback routing confirmed)
- `docker compose down` → all containers removed cleanly, named volume preserved
- Both compose files pass `docker compose config --quiet` validation

## Requirements Advanced

- USER-03 — Compound indexes `(user_id, completed_at)` on workouts and `(user_id, key)` on settings now created at startup

## Requirements Validated

- DOCK-01 — docker-compose.yml defines 3 services: nginx, backend, mongodb ✓
- DOCK-02 — nginx serves Vue SPA and reverse proxies /api/* to backend ✓
- DOCK-03 — MongoDB data persists via named Docker volume `mongodb_data` ✓
- DOCK-04 — `docker compose up --build` starts everything cleanly; 59 tests pass ✓
- DOCK-05 — docker-compose.prod.yml for VPS with bare IP, DEV_MODE=false ✓
- DOCK-06 — Telegram bot setup documented in DEPLOYMENT.md ✓
- USER-03 — Compound indexes on user_id prefix created at startup ✓

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- **Host port 27018 for MongoDB dev:** Dev compose uses `27018:27017` host mapping instead of `27017:27017` because the development machine runs a local MongoDB instance that already binds 27017. Production compose doesn't expose the port at all, so this is dev-only.
- **nginx/Dockerfile at parent level:** Context option uses the parent directory (`.`) as build context instead of `./frontend`. This was needed so the multi-stage build can copy both `frontend/` source and `nginx/nginx.conf` into the image. The frontend's own `Dockerfile` remains unchanged.

## Known Limitations

- No SSL/TLS — bare IP HTTP only. Deferred to a future milestone per scope.
- No MongoDB authentication credentials — Docker network isolation only. Sufficient for personal VPS; add auth in a future hardening milestone.
- The `docker compose up --build` dev flow rebuilds the frontend on every run. Could be optimized with a separate dev server setup but not needed for this milestone.
- Exercise seed is checked by counting exercises with `user_id=None`. If someone manually deletes all shared exercises, re-running the backend will re-seed them (correct behavior).

## Follow-ups

- S10: Remove SQLAlchemy/Alembic from backend pyproject.toml (already absent, verify clean)
- S10: Archive scripts repo
- Future: Add MongoDB credentials to Docker Compose for hardened production deployments
- Future: Add SSL/TLS via Let's Encrypt + certbot

## Files Created/Modified

- `../docker-compose.yml` — 3-service dev stack, DEV_MODE=true, MongoDB on host port 27018
- `../docker-compose.prod.yml` — 3-service production stack, DEV_MODE=false, required env vars
- `../nginx/Dockerfile` — multi-stage: node build + nginx:1.28-alpine with reverse proxy config
- `../nginx/nginx.conf` — /api/* proxy_pass to backend:8000, try_files SPA fallback
- `../.env.example` — JWT_SECRET, TELEGRAM_BOT_TOKEN, VITE_TELEGRAM_BOT_NAME with guidance
- `../DEPLOYMENT.md` — Telegram bot setup, VPS deployment steps, backup, troubleshooting
- `../backend/app/seed.py` — 50 exercises, idempotent async seed function
- `../backend/app/main.py` — added `_startup_tasks()` for seed + compound index creation

## Forward Intelligence

### What the next slice should know
- `DEV_MODE` defaults to `"true"` in both `config.py` and the dev compose. Production compose explicitly sets `"false"`. S10 should verify this distinction is preserved after any cleanup.
- The backend Dockerfile uses `python:3.12-slim` even though `pyproject.toml` requires `>=3.13`. The container actually runs Python 3.14 (from uv's resolution) — this mismatch in the base image is cosmetic but worth fixing in S10.
- `scripts/` repo seed data was manually transcribed to `backend/app/seed.py`. The authoritative copy is now in the backend. Scripts repo can be archived.
- MongoDB volume is named `mongodb_data` (prefixed as `test_gsd_mongodb_data` by Docker Compose project name). On VPS, ensure compose project name is consistent to avoid orphaned volumes.

### What's fragile
- `JWT_SECRET` defaults to a dev placeholder in the dev compose — any data created in dev mode with this secret will be invalid if the secret changes. Fine for dev; production must use a stable value from `.env`.
- The `depends_on: service_healthy` for MongoDB requires the `mongosh` binary to be available in the `mongo:8.0` image. This is true for official MongoDB images but would break with custom/minimal MongoDB images.

### Authoritative diagnostics
- `docker compose logs backend` — see seed count, index creation, startup errors
- `curl http://localhost/api/health` — first signal for stack health
- `docker compose ps` — verify all containers in "running" state (not "exited")

### What assumptions changed
- S09 context assumed the frontend Dockerfile would be modified to become a pure builder. Instead, the cleaner approach was a new `nginx/Dockerfile` with parent-dir build context — the frontend Dockerfile is untouched and still works standalone.
