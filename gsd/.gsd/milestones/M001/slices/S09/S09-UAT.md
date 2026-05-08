# S09: Docker Deployment — UAT

**Milestone:** M001
**Written:** 2026-03-13

## UAT Type

- UAT mode: live-runtime
- Why this mode is sufficient: Docker Compose is an integration concern — the only meaningful test is actually running `docker compose up` and verifying the full stack works end-to-end in a browser.

## Preconditions

- Docker Engine installed (`docker --version` → 24+, `docker compose version` → v2+)
- Running from the parent directory (`TEST_GSD/` — where `backend/`, `frontend/`, `gsd/` are siblings)
- Port 80 is free on the host (or adjust nginx port mapping)
- No `.env` file required for the dev compose (defaults are sufficient)

## Smoke Test

```bash
cd /path/to/TEST_GSD
docker compose up --build
# Wait ~2 minutes for build + startup
curl http://localhost/api/health
# Expected: {"status":"ok","database":"connected"}
```

## Test Cases

### 1. All 3 containers start and stay healthy

```bash
docker compose up --build -d
sleep 30
docker compose ps
```
**Expected:** All 3 services show `running` status. `mongodb` shows `(healthy)`.

### 2. Exercise library seeded on first startup

```bash
curl -L http://localhost/api/exercises/
```
**Expected:** JSON array with 50 exercises (Barbell Bench Press, Pull-Up, etc.)

### 3. Dev login and auth flow through nginx proxy

```bash
# Get a token via dev login
TOKEN=$(curl -s -X POST http://localhost/api/auth/dev-login | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

# Use token to call protected endpoint
curl -s -H "Authorization: Bearer $TOKEN" http://localhost/api/auth/me
```
**Expected:** JSON with `{"id":"dev-user-000","first_name":"Dev",...}` — full round-trip through nginx proxy to backend to MongoDB.

### 4. Vue SPA served and client-side routing works

1. Open `http://localhost` in a browser
2. **Expected:** GymCoach app loads (login page or main app in dev mode)

3. Navigate directly to `http://localhost/programs` in the browser address bar
4. **Expected:** HTTP 200, app loads (not a 404) — SPA fallback routing works

### 5. MongoDB data persists across restarts

```bash
# Create a program via API
TOKEN=$(curl -s -X POST http://localhost/api/auth/dev-login | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
curl -s -X POST http://localhost/api/programs/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Persistence","exercises":[]}'

# Restart the stack (NOT docker compose down -v)
docker compose restart

# Re-fetch programs
sleep 15
curl -sL -H "Authorization: Bearer $TOKEN" http://localhost/api/programs/ | python3 -c "import json,sys; d=json.load(sys.stdin); print([p['name'] for p in d])"
```
**Expected:** `['Test Persistence']` — data survived the restart.

### 6. Seed is idempotent (does not re-seed on second startup)

```bash
# Restart backend only
docker compose restart backend
sleep 10

# Exercise count should still be 50, not 100
curl -sL http://localhost/api/exercises/ | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
```
**Expected:** `50` — not doubled.

## Edge Cases

### JWT_SECRET placeholder in dev mode

```bash
TOKEN=$(curl -s -X POST http://localhost/api/auth/dev-login | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
docker compose restart backend
sleep 10
curl -s -H "Authorization: Bearer $TOKEN" http://localhost/api/auth/me
```
**Expected in dev:** May return 401 (dev secret is consistent within a single docker compose session but changes on full `down`+`up`). This is expected and documented — production must use a stable `JWT_SECRET` in `.env`.

### docker compose down preserves volume

```bash
docker compose down    # no -v flag
docker compose up -d
sleep 20
curl -sL http://localhost/api/exercises/ | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
```
**Expected:** `50` — volume survived `down`. (Use `down -v` only when you want to wipe data.)

## Failure Signals

- `docker compose ps` shows a container in `exited` state — check `docker compose logs <service>`
- `curl http://localhost/api/health` returns `{"database":"disconnected"}` — backend can't reach MongoDB
- `curl http://localhost/` returns nginx 502 Bad Gateway — backend container not running
- Exercise count is 0 — seed failed; check `docker compose logs backend` for startup errors
- Deep route (e.g. `http://localhost/programs`) returns nginx 404 — `try_files` fallback not working (check `nginx/nginx.conf`)

## Requirements Proved By This UAT

- DOCK-01 — 3 services confirmed running via `docker compose ps`
- DOCK-02 — nginx proxies /api/* (health + exercises verified) and serves SPA (browser test)
- DOCK-03 — MongoDB data survives `docker compose restart` (named volume)
- DOCK-04 — `docker compose up --build` starts everything cleanly from scratch
- DOCK-05 — docker-compose.prod.yml validated via `docker compose config`
- DOCK-06 — DEPLOYMENT.md exists with Telegram bot setup steps
- USER-03 — Compound indexes confirmed in MongoDB logs at startup

## Not Proven By This UAT

- Production Telegram auth (requires a real bot token and registered domain)
- SSL/TLS — deferred to a future milestone
- MongoDB authentication/credentials — not implemented (Docker network isolation only)
- VPS deployment — requires an actual VPS; the compose files are validated but not live-tested on remote hardware
- `docker-compose.prod.yml` full run — validated syntactically; production-mode end-to-end test requires real `TELEGRAM_BOT_TOKEN`

## Notes for Tester

- The dev compose uses `DEV_MODE=true` — the login page will show a "Dev Login" button instead of the Telegram widget. This is expected.
- MongoDB warnings in `docker compose logs mongodb` about deprecated SSL parameters are cosmetic — they come from the MongoDB 8.0 image defaults and do not affect functionality.
- First `docker compose up --build` takes 3–5 minutes (downloading base images, npm install, Python deps). Subsequent runs with no code changes are fast (~10s) due to Docker layer caching.
- If port 80 is busy, change `"80:80"` to `"8080:80"` in `docker-compose.yml` and access via `http://localhost:8080`.
