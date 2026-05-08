# Feature Research

**Domain:** Gym training app v1.1 -- MongoDB migration, Telegram auth, multi-user, program versioning, Docker deployment
**Researched:** 2026-03-09
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features that are non-negotiable for this milestone. Without them the upgrade from v1.0 is incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| MongoDB document storage replacing SQLite | Core migration goal; all existing CRUD must keep working identically | HIGH | Requires rewriting all SQLAlchemy models to Beanie documents, replacing all repository/query code, and migrating existing data. 6 SQLAlchemy tables (exercises, programs, program_exercises, program_sets, workouts, workout_sets) collapse into 3 MongoDB collections with embedded sub-documents. |
| Telegram Login Widget authentication | Only auth mechanism planned; without it multi-user is impossible | MEDIUM | Widget is a simple script tag on frontend. Backend verifies HMAC-SHA-256 hash using bot token. Data returned: id, first_name, last_name, username, photo_url, auth_date, hash. Requires a Telegram bot created via @BotFather with `/setdomain` configured. No OAuth flow -- custom verification. |
| Long-lived JWT sessions (1 year) | Users should not re-login constantly for a personal gym app used daily | LOW | Standard PyJWT encode/decode. Token contains telegram_id + expiry. Stored in localStorage on frontend. Auto-create user document on first login. |
| Multi-user data isolation via user_id | Fundamental requirement once auth exists; data leakage is unacceptable | MEDIUM | Every document gets a `user_id` field. Every query filters by `user_id`. Compound indexes with `user_id` as prefix for performance. Must be enforced at the repository/service layer -- MongoDB has no row-level security, so this is purely application-enforced. |
| Docker Compose deployment (nginx + backend + MongoDB) | Deployment target for VPS; without it there is no way to run in production | MEDIUM | Three services: nginx (reverse proxy + serves SPA static files), FastAPI backend (uvicorn), MongoDB. Volumes for MongoDB data persistence. Environment variables for config. |
| Data migration from SQLite to MongoDB | Existing v1.0 data must not be lost | MEDIUM | One-time migration script. Read from SQLite, transform relational rows into MongoDB documents with embedded sub-documents, insert into MongoDB. Must handle ID mapping (SQLite integer IDs to MongoDB ObjectIds or string IDs). |
| Exercise library with user scoping | Exercises need to work per-user; seed exercises shared, custom exercises per-user | LOW | Seed exercises can be global (no user_id) or duplicated per user. Custom exercises get user_id. Queries return global + user's custom exercises. |

### Differentiators (Competitive Advantage)

Features that add value beyond the basic migration. Not strictly required but make the upgrade worthwhile.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Program versioning with workout history binding | Workouts reference the exact program version used, so history stays accurate even after program edits | MEDIUM | MongoDB Document Versioning Pattern: programs collection holds current version, program_versions collection holds snapshots. Each workout document stores a `program_version_id` reference. When a program is edited, version number increments and a snapshot is saved. Existing workouts still reference the old version. |
| Self-contained workout documents | Workout documents embed all exercise names, set targets, and logged data -- no joins needed for history display | LOW | MongoDB strength: denormalize at write time. When starting a workout, snapshot the program's exercises/sets into the workout document. History queries hit one collection with no lookups. Already partially how the frontend works. |
| Automated dev pipeline (docker-compose up + tests) | One command to build and verify everything works | LOW | `docker-compose up --build` plus a test runner. Backend pytest, frontend vitest, integration tests against the running stack. Makefile or shell script wrapper. |
| Nginx reverse proxy with SPA routing | Single port serves both API and frontend; no CORS issues in production | LOW | Nginx serves `/api/*` to backend upstream, everything else to SPA static files with `try_files $uri /index.html`. Standard pattern, well-documented. |
| Auto-create user on first Telegram login | Zero-friction onboarding -- no registration form, no email verification | LOW | On first valid Telegram auth, create user document with telegram_id, first_name, username, photo_url. Return JWT immediately. Subsequent logins just return new JWT. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems for this project scope.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full OAuth2 / OpenID Connect for Telegram | "Proper" auth standard | Telegram Login Widget is NOT OAuth2. Forcing it into an OAuth flow adds complexity with zero benefit. The widget's HMAC verification is simpler and equally secure for this use case. | Use Telegram's native HMAC-SHA-256 verification directly. |
| Refresh token rotation | Security best practice for short-lived tokens | Overengineered for a personal gym app. Refresh tokens add token storage, rotation logic, and revocation handling. A 1-year JWT is fine when the threat model is "personal VPS, trusted users." | Single long-lived JWT. If compromised, user re-authenticates via Telegram (takes 2 seconds). |
| MongoDB Atlas / cloud hosting | Managed database, no ops burden | Adds cost and network latency for a self-hosted personal app. Docker MongoDB container with volume mount is simpler, free, and keeps data local. | Self-hosted MongoDB in Docker with volume persistence and periodic backup script. |
| Role-based access control (RBAC) | Multi-user implies roles | This is a personal tool shared with a few friends at most. Admin/user roles add complexity with no value. All authenticated users have identical permissions over their own data. | Flat user model -- everyone is equal, data isolated by user_id. |
| Real-time sync / WebSockets | Keep multiple devices in sync | Only one device is typically used at a time (phone at the gym). HTTP request/response is sufficient. WebSockets add connection management complexity. | Standard REST API. Frontend fetches fresh data on navigation. |
| SSL/TLS termination in this milestone | Security requirement for production | PROJECT.md explicitly defers SSL/domain to a future milestone. Adding it now complicates Docker setup and requires domain ownership. | Deploy on bare IP first. Add SSL via Let's Encrypt + certbot in a future milestone. |
| Per-collection database separation for multi-tenancy | Database-per-user isolation | Massive overkill for <100 users. Creates operational burden (backups, migrations per DB). | Single database, shared collections, user_id field on every document, compound indexes. |
| Bidirectional program version diff | Show what changed between program versions | Complex UI work with limited value. Users just want to see what a program looked like when they did a workout, not a side-by-side diff. | Store full program snapshots as versions. Display the version as-is in workout history. |

## Feature Dependencies

```
[Telegram Bot Setup (@BotFather)]
    └──requires──> [Telegram Login Widget (frontend)]
                       └──requires──> [Auth Verification Endpoint (backend)]
                                          └──requires──> [JWT Session Management]
                                                             └──requires──> [Multi-user Data Isolation (user_id)]

[MongoDB Setup (Docker container)]
    └──requires──> [Document Schema Design (Beanie models)]
                       └──requires──> [Repository Layer Rewrite]
                                          └──requires──> [API Route Updates]

[Document Schema Design]
    └──requires──> [Program Versioning Schema]

[MongoDB Setup] + [Auth + Multi-user]
    └──requires──> [Data Migration Script (SQLite -> MongoDB)]

[Docker Compose]
    └──requires──> [Backend Dockerfile]
    └──requires──> [Frontend Build (static files)]
    └──requires──> [Nginx Config]
    └──requires──> [MongoDB container config]

[All above complete]
    └──requires──> [Automated Dev Pipeline]
```

### Dependency Notes

- **Telegram Bot Setup is the only external dependency:** Requires creating a bot via @BotFather and running `/setdomain`. This is a manual step that blocks frontend widget integration. Takes 2 minutes but must happen before any auth work.
- **MongoDB schema design blocks everything else:** The document structure (what gets embedded vs. referenced) determines the repository layer, API shapes, and migration script. Must be decided first.
- **Program versioning depends on schema design:** The versioning pattern (separate collection vs. embedded) is a schema-level decision that affects how workouts reference programs.
- **Data migration requires both MongoDB and auth to be ready:** Migration script needs to know the document schema AND whether to assign a default user_id to existing data.
- **Docker Compose is the final integration step:** All individual components (backend, frontend build, MongoDB, nginx) must work before composing them.

## MVP Definition

### Launch With (v1.1)

Minimum viable set for this milestone -- what must ship together.

- [ ] MongoDB document storage with 3 collections (exercises, programs, workouts) -- replaces SQLite entirely
- [ ] Telegram Login Widget on frontend with HMAC verification on backend
- [ ] JWT session tokens (1 year expiry) with auto-create user on first login
- [ ] user_id on all documents with query-level isolation
- [ ] Program versioning: version number + snapshot on edit, workout references version
- [ ] Self-contained workout documents (embedded exercise/set data)
- [ ] Data migration script (SQLite to MongoDB, assigns default user for existing data)
- [ ] Docker Compose with nginx + backend + MongoDB
- [ ] Frontend Dockerfile (multi-stage build: npm build -> nginx static serve)
- [ ] Backend Dockerfile (Python + uvicorn)

### Add After Validation (v1.1.x)

Features to add once the core migration is stable.

- [ ] Automated test pipeline (docker-compose test profile) -- after Docker Compose works
- [ ] Backup/restore script for MongoDB data -- after production deployment
- [ ] User profile page (display Telegram name/photo) -- after auth works

### Future Consideration (v2+)

Features to defer until the app is running in production.

- [ ] SSL/TLS with Let's Encrypt -- requires domain purchase
- [ ] CI/CD pipeline -- after manual deployment is proven
- [ ] Admin dashboard (view all users) -- only if user count grows
- [ ] Exercise sharing between users -- social feature, separate domain

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| MongoDB document storage | HIGH | HIGH | P1 |
| Telegram auth + JWT sessions | HIGH | MEDIUM | P1 |
| Multi-user data isolation (user_id) | HIGH | MEDIUM | P1 |
| Program versioning | MEDIUM | MEDIUM | P1 |
| Self-contained workout documents | HIGH | LOW | P1 |
| Data migration script | HIGH | MEDIUM | P1 |
| Docker Compose deployment | HIGH | MEDIUM | P1 |
| Nginx reverse proxy + SPA | MEDIUM | LOW | P1 |
| Auto-create user on first login | MEDIUM | LOW | P1 |
| Automated dev pipeline | MEDIUM | LOW | P2 |
| MongoDB backup script | MEDIUM | LOW | P2 |
| User profile page | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for v1.1 launch
- P2: Should have, add shortly after launch
- P3: Nice to have, future consideration

## Existing Feature Impact Analysis

How v1.1 features affect already-built v1.0 functionality.

| Existing Feature | Impact | Migration Notes |
|-----------------|--------|-----------------|
| Exercise library CRUD | Schema change (SQLAlchemy -> Beanie), add user_id field | Exercises become MongoDB documents. Seed exercises can be global or per-user. API endpoints keep same routes, change internal implementation. |
| Program builder | Schema change + versioning added | Programs embed exercises and sets (no more join tables). Version field added. On edit, snapshot old version. Frontend program builder UI unchanged. |
| Workout logging with pre-fill | Schema change, workouts become self-contained | Workout document embeds exercise names + set targets at start time. Pre-fill from last workout queries workouts collection directly. No joins needed. |
| Weight progression suggestions | Query pattern changes (MongoDB aggregation vs SQL) | Progression logic stays the same, but queries use MongoDB aggregation pipeline instead of SQLAlchemy joins. Filter by user_id. |
| Workout history + charts | Query pattern changes | History queries filter by user_id. Self-contained workout documents make history queries simpler (no joins). Charts use same data shape. |
| CLI analytics + export/import | Must be rewritten or removed | Scripts repo currently uses SQLAlchemy + SQLite. Options: (a) rewrite scripts to use MongoDB, (b) move analytics into the web app, (c) remove scripts repo. PROJECT.md says "Remove scripts repo SQLite dependencies, move functionality to webapp." |
| Settings (rest timer) | Becomes per-user setting in user document or settings collection | Currently a key-value table. In MongoDB, store as fields on the user document or a per-user settings document. |

## Sources

- [Telegram Login Widget official docs](https://core.telegram.org/widgets/login) -- widget integration, hash verification algorithm (HIGH confidence)
- [MongoDB Document Versioning Pattern](https://www.mongodb.com/blog/post/building-with-patterns-the-document-versioning-pattern) -- versioning with separate history collection (HIGH confidence)
- [MongoDB Multi-Tenant Architecture](https://www.mongodb.com/docs/atlas/build-multi-tenant-arch/) -- single-database, shared-collection with tenant_id (HIGH confidence)
- [FastAPI MongoDB Best Practices](https://www.mongodb.com/developer/products/mongodb/8-fastapi-mongodb-best-practices/) -- schema separation, connection pooling, indexing (HIGH confidence)
- [Beanie ODM GitHub](https://github.com/BeanieODM/beanie) -- async MongoDB ODM for Python, Pydantic-based, actively maintained as of March 2026 (HIGH confidence)
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/) -- official Dockerfile patterns (HIGH confidence)
- [Motor Deprecation Notice](https://www.mongodb.com/docs/languages/python/) -- Motor end-of-life May 2026, PyMongo async API as replacement (HIGH confidence)
- [FastAPI-Telegram-Auth example](https://github.com/pavel-glukhov/FastAPI-Telegram-Auth) -- reference implementation for Telegram auth with FastAPI (MEDIUM confidence)

---
*Feature research for: GymCoach v1.1 MongoDB Migration and Deployment*
*Researched: 2026-03-09*
