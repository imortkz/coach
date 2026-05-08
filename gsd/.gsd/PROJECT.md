# GymCoach

## What This Is

A personal gym training companion — a single-user (v1.0) / multi-user (v1.1) web app for creating exercise programs, logging workouts at the gym, and getting automatic weight progression suggestions. Built across a multi-repo setup: Python backend (FastAPI + MongoDB/Beanie), Vue 3 frontend, and utility scripts.

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

- [x] Migrate data storage from SQLite to MongoDB — Beanie ODM, 4 collections, 49 tests pass (S07)
- [x] Program versioning — current_version + embedded ProgramVersion snapshots (S07)
- [x] Telegram Login Widget authentication with long-lived JWT sessions (S08)
- [x] Multi-user data model — user_id on Program, Workout, Setting; nullable on Exercise for shared seeds (S08)
- [x] Docker Compose setup (nginx + backend + MongoDB) — docker compose up --build works, 50 exercises seeded, compound indexes, data persists (S09)
- [x] VPS deployment preparation — docker-compose.prod.yml, nginx reverse proxy, DEPLOYMENT.md, .env.example (S09)
- [ ] Remove scripts repo SQLite dependencies (S10)
- [ ] Archive scripts repo (S10)

## Current Milestone: M003 — Localization, Expanded Exercise Library & Exercise GIFs

**Goal:** Users can switch between English and Russian UI, browse an expanded exercise library (~20–30 per muscle group), and see demonstration GIFs for exercises.

**Progress:**
- ✅ S01: Backend model + expanded seed with upsert — `name_ru`, `gif_url` fields added; ~150 exercises seeded via upsert-by-name; 59+ backend tests pass
- ✅ S02: vue-i18n infrastructure + Settings view with language toggle — i18n plugin, EN/RU locales, settings store, Settings view, gear nav tab, Exercise.id→string type fix
- ✅ S03: Exercise name localization + GIF display + type fix — useDisplayName composable; all 4 views localized; GIF display with null guard; Exercise.id/exerciseId types fixed to string throughout

**Target features:**
- Language toggle in Settings → all static UI strings switch reactively (EN ↔ RU)
- Language preference persists via backend `PUT/GET /api/settings/language`
- Exercise names use `name_ru` when language is Russian across ExercisesView, ExerciseCard, ExerciseHistoryView, WorkoutCard
- Exercise GIF displays inline with graceful null handling
- ~120–180 exercises seeded across 6 muscle groups

### Out of Scope

- Mobile native app — web only, mobile-responsive is sufficient
- Social features / sharing — personal tool
- Video / form tracking — just numbers
- Nutrition / calorie tracking — separate domain
- Complex periodization engine — simple linear progression sufficient
- SSL/TLS with Let's Encrypt — requires domain purchase, deferred
- CI/CD pipeline — after manual deployment is proven
- Admin dashboard — personal tool, not needed

## Context

Shipped v1.0 with ~8,310 LOC across 3 repos (2,460 Python backend, 2,297 Python scripts, 3,553 TypeScript/Vue frontend). 16 plans executed across 6 phases in 2 days.

- **backend/** — Python FastAPI REST API with SQLite (15 endpoints, SQLAlchemy models)
- **frontend/** — Vue 3 + Vite + Tailwind SPA (exercise library, program builder, workout logging, history, charts)
- **scripts/** — Python CLI tools (Alembic migrations, exercise seed, analytics reports, JSON/CSV export/import)
- **gsd/** — Planning-only meta repo (this repo, no source code)

## Constraints

- **Stack**: Python (FastAPI) backend, VueJS frontend, MongoDB database (migrating from SQLite)
- **Architecture**: Multi-repo — code lives in ../backend, ../frontend, ../scripts (never in gsd/)
- **Storage**: MongoDB via Docker container (replacing SQLite in v1.1)
- **Auth**: Telegram Login Widget + JWT (adding in v1.1, was single-user in v1.0)

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

## Milestone Sequence

| ID | Title | Status |
|----|-------|--------|
| M001 | GymCoach v1.1 — MongoDB Migration & Deployment | Complete |
| M002 | Workout Set UX Fixes | Complete |
| M003 | Localization, Expanded Exercise Library & Exercise GIFs | Complete |
| M004 | SSL/HTTPS with Let's Encrypt | Queued |
| M005 | Progress Report | Queued |
| M006 | MongoDB Backup & Restore | Queued |
| M007 | Localization Coverage Completion | Queued |

---
*Last updated: 2026-03-14 after M003 complete*
