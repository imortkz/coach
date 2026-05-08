# M001: GymCoach v1.1 — MongoDB Migration & Deployment — Context

**Gathered:** 2026-03-09
**Status:** Ready for planning (S07 next)

## Background

v1.0 MVP shipped 2026-03-07 with ~8,310 LOC across 3 repos: Python FastAPI + SQLAlchemy + SQLite backend (15 endpoints), Vue 3 + Vite + Tailwind frontend, and Python CLI scripts (Alembic migrations, seed, analytics). v1.1 migrates to MongoDB, adds Telegram auth + multi-user, program versioning, and Docker deployment.

## Implementation Decisions

- **ODM:** Beanie 2.0 (uses PyMongo Async internally — not deprecated Motor)
- **Auth tokens:** PyJWT (replaces outdated python-jose recommended in old FastAPI tutorials)
- **Auth provider:** Telegram Login Widget — HMAC-SHA-256 verification, no bot logic needed
- **Dev auth:** Env-guarded dev-mode bypass for localhost (Telegram widget requires registered domain)
- **Schema:** 6 SQL tables → 4 MongoDB collections (users, exercises, programs, workouts)
- **Embedding:** Exercises/sets embedded in program documents; sets embedded in workout documents
- **Versioning:** Embedded `versions[]` array in program documents (MongoDB document versioning pattern)
- **Docker:** MongoDB 8.0 LTS, nginx 1.28-alpine, 3-service Docker Compose

## Key Risks

1. **SQL-style schema mapping** — Highest-cost mistake. Design documents around access patterns, not SQL tables. Recovery: full restart.
2. **Missing user_id filtering** — Data leakage between users. Build access layer that always injects user_id.
3. **Telegram HMAC verification** — Entire security boundary. Must unit test with known vectors.
4. **Program versioning retrofit** — Must bake into schema from day one; can't reconstruct historical data later.

## Multi-Repo Structure

- `../backend/` — Python FastAPI REST API (code changes here)
- `../frontend/` — Vue 3 SPA (code changes here)
- `../scripts/` — Python CLI tools (to be archived in S10)
- `gsd/` — Planning only (this repo, never source code)

## Reference Files

- Research: `.gsd/milestones/M001/M001-RESEARCH.md` (comprehensive stack, architecture, pitfalls research)
- Old planning: `.planning/` (v1.0 phase plans, summaries, context — reference for understanding existing codebase patterns)
- Requirements: `.gsd/REQUIREMENTS.md` (27 active requirements mapped to S07–S10)

## Depends On

No upstream milestones. S01–S06 (v1.0 MVP) are complete — all existing functionality works.
