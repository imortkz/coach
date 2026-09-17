# GymCoach architecture

This page describes the repository as inspected on 2026-08-24. It is a code
map, not a claim about a running production environment.

## Components and boundaries

```text
Browser (Vue 3 SPA)
  ├─ Pinia stores + authenticated fetch wrapper
  ├─ Vue Router + vue-i18n
  └─ Telegram Login Widget (non-development mode)
                 │ /api/*
                 ▼
nginx
  ├─ serves the compiled SPA
  └─ reverse-proxies /api/*
                 ▼
FastAPI / Beanie
  ├─ auth, exercises, programs, workouts, settings routes
  └─ startup seeding, indexes, and program-lineage migration steps
                 ▼
MongoDB 8.0
```

The development Compose file defines `mongodb`, `backend`, and `nginx` on an
internal `gymcoach` network. The production Compose file adds `certbot` and a
`backup` sidecar. These boundaries are defined in
[`docker-compose.yml`](../docker-compose.yml) and
[`docker-compose.prod.yml`](../docker-compose.prod.yml).

## Frontend

[`frontend/src/main.ts`](../frontend/src/main.ts) creates the Vue app and
installs Pinia, vue-i18n, and Vue Router. [`App.vue`](../frontend/src/App.vue)
is the shared desktop/mobile navigation shell. Routes are lazy-loaded in
[`frontend/src/router/index.ts`](../frontend/src/router/index.ts): login,
exercises, programs, workout, history, report, exercise history, and settings.

The route guard obtains a development token when development mode is enabled,
otherwise redirects unauthenticated users to login; it also loads the saved
language preference. Feature views call Pinia stores under
[`frontend/src/stores`](../frontend/src/stores), which use
[`frontend/src/lib/apiFetch.ts`](../frontend/src/lib/apiFetch.ts) to attach the
JWT stored in browser `localStorage`. `frontend/src/locales/en.ts` and `ru.ts`
provide the two UI locales.

Workout interaction is composed from `WorkoutView.vue` and components under
[`frontend/src/components/workout`](../frontend/src/components/workout).
History uses components under
[`frontend/src/components/history`](../frontend/src/components/history).
`ReportView.vue` uses Chart.js through vue-chartjs for volume and frequency
charts.

## Backend API

[`backend/app/main.py`](../backend/app/main.py) creates the FastAPI application,
uses a lifespan to initialize/close the database, registers public auth routes
and protected domain routes, and exposes `GET /api/health`. The domain layout
keeps Beanie documents, Pydantic schemas, and route handlers together:

| Domain | Responsibility | Entry point |
| --- | --- | --- |
| Auth | Telegram login verification, development login, JWT parsing, current-user dependency | [backend/app/auth](../backend/app/auth) |
| Exercises | Shared seeded and user-owned exercises; CRUD and per-exercise history | [backend/app/exercises/routes.py](../backend/app/exercises/routes.py) |
| Programs | User-owned programs, embedded exercises/set targets, version snapshots | [backend/app/programs/routes.py](../backend/app/programs/routes.py) |
| Workouts | Start/active/complete/discard workouts, set edits, prefill/progression, history and report | [backend/app/workouts/routes.py](../backend/app/workouts/routes.py) |
| Settings | Per-user key/value settings such as language and rest-timer duration | [backend/app/workouts/routes.py](../backend/app/workouts/routes.py) |

All domain routes depend on `get_current_user` except the Telegram and
development login routes. API contracts are defined in the adjacent `schemas.py`
files; no separate checked-in OpenAPI export exists.

## Authentication and authorisation

In normal mode, the client loads Telegram's Login Widget and posts its callback
data to `POST /api/auth/telegram`. The backend verifies its HMAC signature,
creates or updates the user document, then issues a one-year HS256 JWT. The
client stores that token in `localStorage` and sends it as a Bearer token.

`DEV_MODE=true` exposes `POST /api/auth/dev-login` and allows the current-user
dependency to create/use a development user when no token is present. The
backend refuses to start outside development mode without `JWT_SECRET`.

The dependency also supports an optional static agent token that maps to the
configured Telegram user. The feature is disabled when its environment token
is empty. It has the same access scope as that user; see `.env.example` for
variable names. This is a code-level capability, not confirmation that it is
enabled anywhere.

User-owned queries filter by the authenticated user's ID. Shared exercise
documents have `user_id: null`; custom exercises and the other user-scoped
documents carry an owner ID.

## Main flows

### Program editing and workout logging

1. The program routes resolve selected exercises and store their key display
   fields alongside embedded set targets. Program updates append a version
   snapshot and expose version reads.
2. `POST /api/workouts` creates a workout from a user-owned program. The API
   returns previous-set prefill data and progression suggestions.
3. The client logs, updates, removes, or adds workout sets via nested workout
   routes. The active-workout endpoint rebuilds prefill and suggestions after a
   browser reload.
4. Completing a workout timestamps it; completed workouts feed history,
   exercise history, progression, and reports. Discarding deletes the workout.

### Progress reporting

`GET /api/workouts/report?weeks=N` reads a user's completed workouts in the
requested window. The route calculates weekly volume by muscle group, weekly
workout counts, and non-warmup personal-record comparisons in application
code. [`ReportView.vue`](../frontend/src/views/ReportView.vue) requests 2, 4,
or 8 weeks and renders two bar charts plus the PR table.

## State and storage

[`backend/app/database.py`](../backend/app/database.py) initializes Beanie
against MongoDB and, before model initialization, applies idempotent
program-lineage/index compatibility work. Startup also upserts the seeded
exercise library and creates compound indexes for workouts and settings.

| Collection | Stored responsibility |
| --- | --- |
| `users` | Telegram identity/profile and login timestamps |
| `exercises` | Shared seed library and per-user custom exercises, with optional Russian name/GIF path |
| `programs` | User programs, embedded exercises/set targets, version snapshots, and lineage/version fields |
| `workouts` | User workouts and embedded, denormalized set details; completion status is `completed_at` |
| `settings` | Per-user string key/value preferences |

MongoDB data uses the named `mongodb_data` volume in both Compose files. The
frontend's persisted state is the JWT in `localStorage`; other store state is
in-memory and reloaded from the API.

## External integrations

- Telegram Login Widget is loaded by `LoginView.vue`; the server verifies the
  corresponding callback with the configured bot token.
- MongoDB 8.0 is the only database configured by Compose.
- The seeded exercise data includes optional GIF paths. The current seed
  mapping uses same-origin `/gifs/*` paths served with the frontend build.
- Production Compose includes Let's Encrypt Certbot. nginx serves the ACME
  challenge path and selects HTTP-only or HTTPS configuration based on the
  certificate file's presence.

## Build, deployment, and operations surfaces

The nginx Dockerfile first runs `npm ci` and `npm run build` for the frontend,
then copies the result into nginx. nginx's entrypoint renders an HTTP or HTTPS
template at startup and proxies `/api/` to the backend. Development Compose
sets development mode and maps host `27018` to MongoDB `27017`; production does
not expose MongoDB's port.

Production Compose defines a backup sidecar that runs `mongodump` immediately
on startup and then hourly, promotes the midnight-UTC archive to a daily copy,
and prunes according to environment-configured retention. The manual restore
scripts are [backup/restore-full.sh](../backup/restore-full.sh) and
[backup/restore-user.sh](../backup/restore-user.sh). They are operationally
destructive or data-changing when executed; this document does not validate a
live backup or restore.

GitHub Actions CI path-filters backend and frontend changes. Backend CI starts
MongoDB, installs with `uv`, and runs pytest. Frontend CI runs type checking,
a raw-fetch guard, Vitest, and a production build. The separate deployment
workflow is configured to run after successful CI on `master`; its actual
execution is outside repository evidence. See [DEPLOYMENT.md](../DEPLOYMENT.md)
for the documented operator flow.

## Tests and quality checks

- Backend tests live in [backend/tests](../backend/tests) and cover health,
  auth, configuration, seed behavior, exercises, programs/versioning, workouts,
  and reports. They need MongoDB (as configured in CI).
- Frontend tests are Vitest/jsdom specs alongside components, stores, views,
  and `frontend/src/test`; `npm run type-check`, `npm run check:no-raw-fetch`,
  and `npm run build` are configured checks.
- The exact CI commands and triggers are in
  [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## Confirmed unknowns

- The repository cannot establish which environment variables are set, whether
  optional agent access is enabled, or the state of any deployed service.
- It does not document database size, traffic, monitoring/alerting, backup
  restore drills, or an off-site backup implementation.
- It does not include a committed API compatibility policy, generated API
  reference, or a formal data-retention policy.
