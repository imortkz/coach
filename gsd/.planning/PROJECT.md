# GymCoach

## What This Is

A personal gym training companion — a single-user web app for creating exercise programs, logging workouts at the gym, and getting automatic weight progression suggestions. Includes CLI tools for analytics reports and data backup. Built across a multi-repo setup: Python backend (FastAPI + SQLite), Vue 3 frontend, and utility scripts.

## Core Value

Log workouts quickly at the gym and see what weight to lift next based on past performance.

## Requirements

### Validated

- ✓ Create and manage exercise lists with sets/reps/weight targets — v1.0
- ✓ Log completed sets with actual weight and reps during a workout — v1.0
- ✓ Auto-suggest weight increases based on logged performance — v1.0
- ✓ View workout history and progress — v1.0
- ✓ Mobile-friendly web UI for use at the gym — v1.0
- ✓ SQLite storage for all data — v1.0
- ✓ DB schema migrations and seed data (scripts repo) — v1.0
- ✓ CLI analytics scripts for progress reports and stats — v1.0

### Active

- [ ] Migrate data storage from SQLite to MongoDB (Docker container)
- [ ] Telegram Login Widget authentication with long-lived sessions
- [ ] Multi-user data model (user_id on all documents)
- [ ] Program versioning (workouts reference specific program version)
- [ ] Docker Compose setup (nginx + backend + MongoDB)
- [ ] Automated dev setup with build, run, and test verification
- [ ] VPS deployment preparation (nginx reverse proxy, bare IP)
- [ ] Remove scripts repo SQLite dependencies, move functionality to webapp

## Current Milestone: v1.1 MongoDB Migration & Deployment

**Goal:** Replace SQLite with MongoDB, add Telegram auth with multi-user support, program versioning, and Docker-based deployment.

**Target features:**
- MongoDB data storage with document-based schema (exercises collection, programs with embedded exercises + versioning, self-contained workout documents)
- Telegram Login Widget authentication (requires bot via @BotFather — no bot logic, just identity provider)
- Long-lived sessions (1 year JWT) with automatic account creation on first login
- Multi-user data model with user_id on all documents
- Program versioning: workouts reference specific program version for history consistency
- Docker Compose: nginx (reverse proxy + SPA) + FastAPI backend + MongoDB
- Automated dev pipeline: docker-compose up, run tests (backend, frontend, integration)
- VPS deployment with nginx reverse proxy (SSL/domain deferred to future milestone)

### Out of Scope

- Multi-user / authentication — single user, no login
- Mobile native app — web only, mobile-responsive is sufficient
- Social features / sharing — personal tool
- Video / form tracking — just numbers
- Cloud sync — not needed with MongoDB on VPS
- Nutrition / calorie tracking — separate domain
- Complex periodization engine — simple linear progression sufficient

## Context

Shipped v1.0 with ~8,310 LOC across 3 repos (2,460 Python backend, 2,297 Python scripts, 3,553 TypeScript/Vue frontend). 16 plans executed across 6 phases in 2 days.

- **backend/** — Python FastAPI REST API with SQLite (15 endpoints, SQLAlchemy models)
- **frontend/** — Vue 3 + Vite + Tailwind SPA (exercise library, program builder, workout logging, history, charts)
- **scripts/** — Python CLI tools (Alembic migrations, exercise seed, analytics reports, JSON/CSV export/import)
- **gsd/** — Planning-only meta repo (this repo, no source code)

## Constraints

- **Stack**: Python (FastAPI) backend, VueJS frontend, SQLite database
- **Architecture**: Multi-repo — code lives in ../backend, ../frontend, ../scripts (never in gsd/)
- **Storage**: SQLite only, no external database services
- **Auth**: None — single-user, no authentication layer

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Multi-repo split | Test GSD subagent parallelism across repos | ✓ Good — worked well, clean separation |
| SQLite over Postgres | Simplicity, local-only, no server needed | ✓ Good — WAL mode handles concurrent reads |
| FastAPI over Flask | Modern async, auto OpenAPI docs, type hints | ✓ Good — auto docs useful for frontend dev |
| Vue 3 over React | User preference | ✓ Good — Composition API clean for this scale |
| No auth | Single-user personal tool, reduces complexity | ✓ Good — zero auth overhead |
| Tailwind CSS v4 | Modern utility-first CSS | ✓ Good — responsive design straightforward |
| Naive UTC datetimes | Store UTC without timezone info in SQLite | ⚠️ Revisit — caused frontend parsing bugs (fixed with Z suffix normalization) |

---
*Last updated: 2026-03-09 after v1.1 milestone start*
