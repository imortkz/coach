# GymCoach

[![CI](https://github.com/imortkz/coach/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/imortkz/coach/actions/workflows/ci.yml)
[![Deploy](https://github.com/imortkz/coach/actions/workflows/deploy.yml/badge.svg?branch=master)](https://github.com/imortkz/coach/actions/workflows/deploy.yml)

A personal gym training companion: program planning, workout logging, and weekly progress reports (volume, frequency, PRs).

## Stack

- **Backend** — FastAPI + Beanie + MongoDB, Python 3.13 (uv-managed)
- **Frontend** — Vue 3 + Vite + Tailwind, TypeScript
- **Edge** — nginx (multi-stage; SPA + `/api/*` proxy)
- **Auth** — Telegram Login Widget in production, dev-mode bypass for local
- **Prod** — `coach.imort.kz`, single-VPS Docker Compose stack with Let's Encrypt

## Local development

```bash
docker compose up --build
```

App at `http://localhost`. Dev-mode auto-login, no Telegram setup required. MongoDB is exposed on `27017` for Compass / `mongosh`.

## Tests

```bash
cd backend && uv sync --frozen && uv run pytest      # backend
cd frontend && npm ci && npm run type-check && npm run build   # frontend
```

CI runs the same commands on every PR and push to `master`.

## Production deploy

Pushes to `master` that pass CI deploy automatically to the VPS via [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). Manual deploy and SSL bootstrap are documented in [DEPLOYMENT.md](./DEPLOYMENT.md).
