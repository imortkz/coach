---
id: S09
milestone: M001
status: ready
---

# S09: Docker Deployment — Context

## Goal

Ship a `docker-compose up` command at the repo parent directory that starts nginx + FastAPI + MongoDB with MongoDB data persisting across restarts, the app accessible in a browser, and production auth enabled.

## Why this Slice

S08 completed the auth and multi-user layer. S09 is the packaging step that takes the working application and makes it deployable. It unblocks S10 (cleanup) and is the first time the full stack runs as a unit — nginx, backend, and MongoDB — in a reproducible environment. The VPS deployment target requires this before the milestone is considered shipped.

## Scope

### In Scope

- Two docker-compose files: `docker-compose.yml` (local dev) and `docker-compose.prod.yml` (VPS/production) at the parent directory (`../`)
- nginx reverse proxy config: `/api/*` proxied to FastAPI, everything else serves the built Vue SPA with `try_files $uri $uri/ /index.html`
- MongoDB 8.0 container with a named volume for data persistence; no MongoDB credentials (internal Docker network only, port not exposed to host)
- Backend container wired to MongoDB via `mongodb://mongodb:27017`; `DEV_MODE=false` in production compose, `DEV_MODE=true` in local dev compose
- Frontend built inside Docker (multi-stage) — nginx serves the compiled `dist/` output
- Stable `JWT_SECRET` via `.env` file (not committed); `.env.example` template committed
- `VITE_TELEGRAM_BOT_NAME` passed as build arg to the frontend image so the Telegram widget renders
- Auto-seed exercise library on first backend startup if the exercises collection is empty
- Compound MongoDB indexes created at startup: `(user_id, completed_at)` on workouts, `(user_id, key)` on settings
- Telegram bot setup documented as a deployment prerequisite in a `DEPLOYMENT.md` or README section
- Health check on the MongoDB service so the backend waits for it before starting (`depends_on: condition: service_healthy`)
- `docker compose up --build` from `../` starts everything cleanly from scratch

### Out of Scope

- SSL/TLS — deferred to a future milestone (bare IP deployment only)
- MongoDB authentication/credentials — Docker network isolation is sufficient for now
- CI/CD pipeline — after manual deployment is proven
- MongoDB backup/restore scripts — deferred post-deployment
- Admin dashboard or user management
- Automated integration test pipeline running inside Docker (add later)

## Constraints

- Docker compose files live at the **parent directory** (`../`), not inside any individual repo. This is where `backend/`, `frontend/`, `gsd/` all sit as siblings.
- Both Dockerfiles already exist: `../backend/Dockerfile` (Python/uvicorn) and `../frontend/Dockerfile` (node build + nginx static serve). S09 should reuse and refine them, not replace them wholesale.
- The frontend Dockerfile currently embeds a minimal nginx config for SPA routing only. In S09 the nginx reverse proxy responsibility belongs to a **separate dedicated nginx container**, not the frontend container. The frontend container may become just a build artifact provider, or the frontend Dockerfile nginx config is replaced with the full reverse proxy config.
- `DEV_MODE` must be `false` in the production compose. `JWT_SECRET` must be a stable value from `.env` — the current code defaults to a random secret on each restart which would invalidate all tokens.
- The frontend build requires `VITE_TELEGRAM_BOT_NAME` at build time (Vite bakes env vars into the bundle). This must be passed as a `--build-arg` in the compose file.
- Seed exercises must be idempotent — running the seed on a non-empty collection should be a no-op (check count before inserting).
- Existing backend tests (`uv run pytest`) must continue to pass after any changes made in this slice.

## Integration Points

### Consumes

- `../backend/Dockerfile` — existing Python/uvicorn backend container definition
- `../frontend/Dockerfile` — existing multi-stage frontend build; nginx SPA routing config inside
- `../backend/app/config.py` — reads `MONGODB_URL`, `DEV_MODE`, `JWT_SECRET`, `TELEGRAM_BOT_TOKEN` from env
- `../backend/app/database.py` — `init_db()` called at startup; registers all Beanie document models
- `../backend/app/main.py` — FastAPI app entrypoint; lifespan handles DB init
- `../frontend/src/stores/auth.ts` — reads `VITE_TELEGRAM_BOT_NAME` baked in at build time for widget

### Produces

- `../docker-compose.yml` — local dev compose (DEV_MODE=true, ports exposed for debugging)
- `../docker-compose.prod.yml` — production compose (DEV_MODE=false, only port 80 exposed)
- `../nginx/nginx.conf` — nginx reverse proxy + SPA routing config
- `../.env.example` — template with all required env vars and comments
- `../DEPLOYMENT.md` (or section in a root README) — Telegram bot setup steps, VPS checklist, first-run instructions
- `../backend/app/seed.py` (if not already present) — exercise seed data, idempotent, called at startup if collection empty
- Compound MongoDB indexes added to Beanie model `Settings` classes or created programmatically in `database.py`

## Open Questions

- **nginx architecture**: The frontend Dockerfile currently embeds a minimal nginx that only does SPA routing. S09 needs a single nginx container that does both reverse proxy and SPA serving. Options: (a) keep frontend Dockerfile as pure build stage and copy `dist/` into a separate dedicated nginx container defined in docker-compose, (b) replace the frontend Dockerfile's nginx config with the full reverse proxy + SPA config. Option (a) is cleaner — the frontend Dockerfile becomes a pure builder, and nginx config lives in `../nginx/nginx.conf`. Current thinking: go with (a).
- **Seed data location**: No `seed.py` currently exists in the backend. It needs to be created. The seed should run during the FastAPI lifespan `startup` event if the exercises collection is empty. This is a small addition to `database.py` or `main.py`.
- **Local dev compose behaviour**: In the local compose, should MongoDB port 27017 be exposed to the host (so developers can connect with Compass/mongosh directly)? Current thinking: yes, expose it in the dev compose only, not in prod.
