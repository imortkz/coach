# Project Research Summary

**Project:** GymCoach v1.1
**Domain:** MongoDB migration, Telegram authentication, Docker deployment for existing gym training app
**Researched:** 2026-03-09
**Confidence:** HIGH

## Executive Summary

GymCoach v1.1 is a migration-and-infrastructure milestone for an existing single-user gym training app (FastAPI + Vue 3 + SQLite). The goal is to replace SQLite with MongoDB, add Telegram-based authentication for multi-user support, introduce program versioning so workout history stays accurate across program edits, and containerize everything with Docker Compose (nginx + FastAPI + MongoDB). The existing v1.0 codebase has 6 SQLAlchemy tables, 15 sync endpoints, and real workout data that must be preserved. This is not a greenfield build -- it is a controlled migration with zero data loss tolerance.

The recommended approach is: use Beanie 2.0 ODM (which runs on PyMongo Async internally, not the deprecated Motor driver) for the MongoDB layer, PyJWT for authentication tokens, and Telegram's native HMAC-SHA-256 widget for identity. The 6 SQL tables collapse into 4 MongoDB collections (users, exercises, programs, workouts) with embedded sub-documents replacing join tables. All endpoints must convert from sync to async. The key architectural decisions are: embed program exercises/sets directly in program documents, embed workout sets in workout documents, and use an embedded versions array for program versioning. Docker Compose orchestrates nginx (reverse proxy + SPA), FastAPI, and MongoDB 8.0.

The primary risks are: (1) mirroring SQL tables as separate MongoDB collections instead of designing document-native schemas -- this is the highest-cost mistake with a full-restart recovery; (2) missing user_id filtering on any query, causing data leakage between users; (3) losing existing workout data during migration; and (4) getting Telegram's HMAC verification wrong, which is the entire security boundary. All four are preventable with upfront schema design, a data access layer that enforces user scoping, a validated migration script, and unit-tested hash verification.

## Key Findings

### Recommended Stack

The existing stack (FastAPI, Pydantic v2, Vue 3, Tailwind, Vite) is retained. New additions are minimal and targeted.

**Note on MongoDB driver choice:** STACK.md recommends Beanie 2.0 ODM (which uses PyMongo Async internally). ARCHITECTURE.md recommends raw Motor. PITFALLS.md warns that Motor is deprecated and recommends PyMongo Async directly. **Recommendation: Use Beanie 2.0.** It provides the cleanest migration path from SQLAlchemy (Beanie Documents are Pydantic models, eliminating model-schema duplication), it already uses PyMongo Async under the hood (so no Motor dependency), and the app's CRUD patterns map perfectly to an ODM. If Beanie proves limiting for aggregation pipelines, drop to raw PyMongo Async for those specific queries.

**Core new technologies:**
- **Beanie 2.0.1** (ODM): Async MongoDB ODM with native Pydantic v2 models -- Documents double as API schemas, eliminating model-schema duplication
- **PyJWT 2.11.0**: JWT token creation/validation -- lightweight, actively maintained, replaces the outdated python-jose
- **MongoDB 8.0** (Docker `mongo:8.0`): LTS release with long support window -- pinned tag, not `latest`
- **nginx 1.28-alpine**: Reverse proxy + SPA static serving -- ~45MB image, standard Docker pattern

**Packages to remove after migration:** SQLAlchemy, Alembic (aiosqlite also no longer needed)

### Expected Features

**Must have (table stakes):**
- MongoDB document storage replacing SQLite -- 6 tables collapse to 4 collections with embedded sub-documents
- Telegram Login Widget authentication with HMAC-SHA-256 verification
- JWT sessions with 1-year expiry and auto-create user on first login
- Multi-user data isolation via user_id on every document and every query
- Data migration script from SQLite to MongoDB preserving all workout history
- Docker Compose deployment (nginx + FastAPI + MongoDB)

**Should have (differentiators):**
- Program versioning with embedded version snapshots -- workouts reference the exact version used
- Self-contained workout documents with all exercise/set data denormalized at write time
- Auto-create user on first Telegram login (zero-friction onboarding)

**Defer (v2+):**
- SSL/TLS with Let's Encrypt (requires domain purchase)
- CI/CD pipeline (after manual deployment is proven)
- Admin dashboard, exercise sharing between users
- Automated test pipeline (add after Docker works)
- MongoDB backup/restore scripts (add after production deployment)

### Architecture Approach

The architecture moves from a direct browser-to-FastAPI-to-SQLite stack to a Docker Compose topology: nginx serves the built Vue SPA and proxies `/api/*` to FastAPI, which connects to MongoDB via Beanie/PyMongo Async. All endpoints convert from `def` (sync, SQLAlchemy) to `async def` (async, Beanie). Authentication is injected via a FastAPI dependency (`get_current_user`) on every route except `/api/auth/telegram` and `/api/health`. The scripts repo is eliminated -- seed data moves to the backend, and analytics/export are deferred.

**Major components:**
1. **nginx container** -- reverse proxy (`/api/*` to backend) + static SPA serving (`try_files` for client-side routing)
2. **FastAPI backend** -- async endpoints, Beanie ODM, JWT auth dependency, Telegram HMAC verification
3. **MongoDB 8.0 container** -- 4 collections (users, exercises, programs, workouts), compound indexes on user_id
4. **Frontend (Vue 3 SPA)** -- new LoginView, auth store, useApi composable for Bearer token injection, router auth guards

### Critical Pitfalls

1. **SQL-style schema mapping to MongoDB** -- Design documents around access patterns (embedded exercises/sets in programs, self-contained workouts), not around existing SQL tables. Recovery cost is HIGH (full restart of Phase 1).
2. **Missing user_id filtering on any query** -- Build a data access layer that always injects user_id. Write cross-user isolation tests for every endpoint. One missed filter = data leakage.
3. **Telegram HMAC verification done wrong** -- Follow the exact algorithm: sort fields, SHA-256 the bot token for the secret key, use `hmac.compare_digest()` for constant-time comparison, reject stale `auth_date`. Unit test with known vectors.
4. **Losing existing v1.0 workout data** -- Write a dedicated migration script with record count validation and embedded document integrity checks. Keep SQLite backup until MongoDB is verified.
5. **Program versioning not implemented from the start** -- Bake version snapshots into the schema from day one. If bolted on later, historical workout data cannot be reconstructed.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: MongoDB Migration and Schema Design
**Rationale:** Everything depends on the database layer. Schema design must happen before any code rewrite because the document structure determines the repository layer, API shapes, and migration script. This is the highest-risk phase (SQL-style mapping is the costliest mistake).
**Delivers:** Beanie document models for 4 collections, async database initialization, rewritten repository/route layer for exercises/programs/workouts, data migration script from SQLite.
**Addresses:** MongoDB document storage, self-contained workout documents, program versioning schema, data migration, exercise seed data migration from scripts repo.
**Avoids:** SQL-style schema mapping (Pitfall 2), data loss during migration (Pitfall 5), program versioning gaps (Pitfall 6).

### Phase 2: Authentication and Multi-User Support
**Rationale:** Depends on MongoDB being operational (users collection, user_id fields). Auth must be complete before multi-user isolation can be verified. This is the security boundary of the app.
**Delivers:** Telegram Login Widget on frontend, HMAC verification endpoint, JWT creation/validation, `get_current_user` dependency, user_id filtering on all queries, auth store + useApi composable + router guards on frontend.
**Addresses:** Telegram auth, JWT sessions, multi-user data isolation, auto-create user, frontend auth integration.
**Avoids:** Telegram hash verification errors (Pitfall 4), data leakage from missing user_id filters (Pitfall 3).

### Phase 3: Docker Deployment
**Rationale:** All application code must work before containerizing. Docker Compose is the integration layer that ties nginx, backend, and MongoDB together. This phase is lower risk because patterns are well-documented.
**Delivers:** Backend Dockerfile, frontend multi-stage Dockerfile, docker-compose.yml with 3 services, nginx reverse proxy config, environment variable management, MongoDB volume persistence.
**Addresses:** Docker Compose deployment, nginx reverse proxy + SPA routing.
**Avoids:** Docker networking issues (Pitfall 7), nginx SPA routing 404s, MongoDB data loss from missing volumes.

### Phase 4: Cleanup and Hardening
**Rationale:** After the system is running end-to-end, remove legacy dependencies and add production-readiness improvements.
**Delivers:** SQLAlchemy/Alembic removal from backend, scripts repo archival, MongoDB indexes verified, "looks done but isn't" checklist completion, dev-mode auth bypass for local development.
**Addresses:** Legacy cleanup, index creation, integration verification.

### Phase Ordering Rationale

- **Phase 1 before Phase 2:** Auth requires MongoDB (users collection). The data access layer established in Phase 1 makes adding user_id filtering in Phase 2 a clean extension rather than a retrofit.
- **Phase 2 before Phase 3:** Auth endpoints and frontend changes must work before containerizing, otherwise debugging auth issues through nginx adds unnecessary complexity.
- **Phase 3 after code is stable:** Docker Compose is a packaging concern. Testing the app directly (Vite dev server + FastAPI + local MongoDB) during Phases 1-2 gives faster iteration cycles.
- **Phase 4 last:** Cleanup is safe only after everything is verified working. Removing SQLAlchemy before migration is verified risks losing the fallback path.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Beanie ODM patterns for embedded documents and the `versions[]` array -- verify how Beanie handles nested model updates and array push operations. Also research the exact SQLite-to-MongoDB data transformation for the 6-table-to-4-collection collapse.
- **Phase 2:** Telegram Login Widget integration specifics -- the `data-onauth` JS callback pattern for localhost development, popup blocker handling, and the exact frontend-to-backend data flow.

Phases with standard patterns (skip research-phase):
- **Phase 3:** Docker Compose + nginx reverse proxy is extremely well-documented. Standard patterns from FastAPI and nginx official docs are sufficient.
- **Phase 4:** Cleanup tasks are mechanical (remove packages, archive repo, verify indexes).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations verified against official docs and PyPI. Motor deprecation confirmed. Beanie 2.0 compatibility verified. |
| Features | HIGH | Feature set is well-scoped and matches the existing codebase structure. Dependencies clearly mapped. |
| Architecture | HIGH | Patterns verified against MongoDB and FastAPI official documentation. One conflict resolved (Motor vs PyMongo Async -- resolved in favor of Beanie which uses PyMongo Async internally). |
| Pitfalls | HIGH | All pitfalls verified against official sources. Recovery costs accurately assessed. |

**Overall confidence:** HIGH

### Gaps to Address

- **Beanie vs raw PyMongo Async vs Motor:** Research files disagreed on MongoDB driver choice. Resolved above in favor of Beanie 2.0 (uses PyMongo Async internally). During Phase 1 planning, verify Beanie's handling of embedded document updates and the `$push` operator for the versions array. If Beanie is awkward for these operations, fall back to raw PyMongo Async for those specific queries.
- **Telegram widget on localhost:** The widget requires a registered domain via @BotFather `/setdomain`. During Phase 2, implement a dev-mode auth bypass (env-guarded) so development is not blocked on domain setup.
- **MongoDB authentication in Docker:** Research mentions enabling MongoDB auth for production but does not specify the exact Docker configuration. During Phase 3 planning, decide whether to add MongoDB credentials or rely on Docker network isolation for the initial deployment.
- **Scripts repo migration scope:** Research says "eliminate scripts repo" but analytics and export functionality is deferred. During Phase 4, decide explicitly what to archive vs. what to rebuild as backend endpoints.

## Sources

### Primary (HIGH confidence)
- [Beanie ODM documentation](https://beanie-odm.dev/) -- async MongoDB ODM, v2.0 changelog, PyMongo Async migration
- [PyMongo Async Migration Guide](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/) -- Motor deprecation and replacement
- [Motor Deprecation Notice](https://www.mongodb.com/docs/drivers/motor/) -- EOL May 2026
- [Telegram Login Widget](https://core.telegram.org/widgets/login) -- HMAC-SHA256 verification spec
- [PyJWT 2.11.0 docs](https://pyjwt.readthedocs.io/en/latest/) -- JWT implementation
- [MongoDB Document Versioning Pattern](https://www.mongodb.com/docs/manual/data-modeling/design-patterns/data-versioning/document-versioning/) -- embedded versioning
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/) -- container patterns
- [FastAPI Security - OAuth2 with JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) -- PyJWT recommendation
- [MongoDB Docker Hub](https://hub.docker.com/_/mongo) -- official image, 8.0 LTS tag
- [nginx Docker Hub](https://hub.docker.com/_/nginx/) -- 1.28-alpine

### Secondary (MEDIUM confidence)
- [FastAPI-Telegram-Auth example](https://github.com/pavel-glukhov/FastAPI-Telegram-Auth) -- reference implementation
- [3 Pitfalls Migrating to MongoDB](https://medium.com/mongodb/3-pitfalls-to-avoid-when-migrating-postgresql-to-mongodb-f40ef2f7cf15) -- schema design anti-patterns
- [FastAPI Proxy Headers Discussion](https://github.com/fastapi/fastapi/discussions/7541) -- ROOT_PATH issues behind nginx

---
*Research completed: 2026-03-09*
*Ready for roadmap: yes*
