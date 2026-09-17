# GymCoach documentation

GymCoach is a workout-tracking web application: authenticated users manage an
exercise library and training programs, log workouts, review history, and view
weekly volume, frequency, and personal-record reports. The current application
is a Vue single-page app backed by a FastAPI API and MongoDB.

## Document map

- [Architecture](architecture.md) — repository-confirmed components, flows,
  storage, integrations, and operational surfaces.
- [Deployment guide](../DEPLOYMENT.md) — local and production Compose usage,
  TLS bootstrap, backups, restores, and troubleshooting.
- [Environment example](../.env.example) — names and purposes of production
  configuration variables; copy it to an untracked `.env`, never commit values.
- [README](../README.md) — short project introduction and common commands.

The `gsd/` directory contains planning and historical delivery records, not
current operating documentation. In particular,
[`gsd/.planning/research/ARCHITECTURE.md`](../gsd/.planning/research/ARCHITECTURE.md)
describes a migration-era target architecture and must be checked against the
source before use.

## Start here by task

| Task | Read | Main code/config entry points |
| --- | --- | --- |
| Run locally | [README](../README.md#local-development), then [deployment guide](../DEPLOYMENT.md) | [docker-compose.yml](../docker-compose.yml), [nginx/Dockerfile](../nginx/Dockerfile) |
| Add or change an API feature | [Architecture](architecture.md#backend-api) | [backend/app/main.py](../backend/app/main.py), domain `models.py`, `schemas.py`, and `routes.py` files under [backend/app](../backend/app) |
| Change a screen or client data flow | [Architecture](architecture.md#frontend) | [frontend/src/router/index.ts](../frontend/src/router/index.ts), [frontend/src/views](../frontend/src/views), [frontend/src/stores](../frontend/src/stores) |
| Change auth or user isolation | [Architecture](architecture.md#authentication-and-authorisation) | [backend/app/auth](../backend/app/auth), [frontend/src/stores/auth.ts](../frontend/src/stores/auth.ts) |
| Change workout logging or reports | [Architecture](architecture.md#main-flows) | [backend/app/workouts](../backend/app/workouts), [frontend/src/components/workout](../frontend/src/components/workout), [frontend/src/views/ReportView.vue](../frontend/src/views/ReportView.vue) |
| Deploy, renew TLS, or restore data | [deployment guide](../DEPLOYMENT.md) | [docker-compose.prod.yml](../docker-compose.prod.yml), [nginx](../nginx), [backup](../backup) |
| Run checks | [README](../README.md#tests), [Architecture](architecture.md#tests-and-quality-checks) | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml), [backend/tests](../backend/tests), [frontend package scripts](../frontend/package.json) |

## Code and configuration map

- `backend/app/main.py` wires the FastAPI lifespan, routers, CORS, and health
  endpoint. `backend/app/database.py` initializes Beanie and performs the
  program-version startup migration steps.
- `backend/app/{auth,exercises,programs,workouts}/` keep each API domain's
  models, request/response schemas, and routes together.
- `frontend/src/main.ts` installs Pinia, vue-i18n, and Vue Router;
  `frontend/src/App.vue` provides the application shell and navigation.
- `frontend/src/lib/apiFetch.ts` is the authenticated fetch wrapper used by
  Pinia stores. `frontend/src/locales/` supplies English and Russian strings.
- `docker-compose.yml` is the development stack; `docker-compose.prod.yml`
  defines the production stack. `.env.example` enumerates production settings.
- `nginx/` builds and serves the SPA and selects HTTP-only or HTTPS config at
  container start. `backup/` contains the production backup sidecar and manual
  restore scripts.

## Documentation gaps and material that may be stale

- No generated API reference or endpoint contract documentation is committed;
  FastAPI's runtime OpenAPI surface is not represented as a versioned artifact.
- The data model has no diagram or collection/index reference beyond the source
  and [architecture guide](architecture.md).
- The README says local MongoDB is exposed on port `27017`, while
  [`docker-compose.yml`](../docker-compose.yml) maps host port `27018` to the
  container's `27017`; use the Compose file as the current source.
- Historical files under `gsd/.planning/` and `gsd/.gsd/` contain superseded
  SQLite/Motor and milestone statements. They are useful provenance but are not
  maintained as current documentation.
