# Roadmap: GymCoach

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-03-07)
- 🚧 **v1.1 MongoDB Migration & Deployment** — Phases 7-10 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-6) — SHIPPED 2026-03-07</summary>

- [x] Phase 1: Foundation and Schema (3/3 plans) — completed 2026-03-06
- [x] Phase 2: Exercise and Program Management (4/4 plans) — completed 2026-03-06
- [x] Phase 3: Workout Logging (3/3 plans) — completed 2026-03-06
- [x] Phase 4: History and Progression (3/3 plans) — completed 2026-03-07
- [x] Phase 5: Analytics and Data Tools (2/2 plans) — completed 2026-03-07
- [x] Phase 6: Integration Fixes and Polish (1/1 plans) — completed 2026-03-07

</details>

### v1.1 MongoDB Migration & Deployment

**Milestone Goal:** Replace SQLite with MongoDB, add Telegram auth with multi-user support, program versioning, and Docker-based deployment.

**Phase Numbering:**
- Integer phases (7, 8, 9, 10): Planned v1.1 milestone work
- Decimal phases (e.g., 7.1): Urgent insertions (marked with INSERTED)

- [ ] **Phase 7: MongoDB Data Layer** - Replace SQLite with MongoDB document schemas, rewrite all endpoints to async, implement program versioning
- [ ] **Phase 8: Authentication and Multi-User** - Telegram Login Widget auth, JWT sessions, user-scoped data isolation on all documents
- [ ] **Phase 9: Docker Deployment** - Docker Compose with nginx reverse proxy, backend, and MongoDB for dev and production
- [ ] **Phase 10: Cleanup** - Remove SQLite/SQLAlchemy dependencies and archive scripts repo

## Phase Details

### Phase 7: MongoDB Data Layer
**Goal**: All application data is stored in MongoDB with document-native schemas, all endpoints are async, and program versioning preserves history across edits
**Depends on**: Phase 6 (v1.0 complete)
**Requirements**: DB-01, DB-02, DB-03, DB-04, DB-05, DB-06, VER-01, VER-02, VER-03, VER-04
**Success Criteria** (what must be TRUE):
  1. User can create, read, update, and delete exercises, programs, and workouts through the existing API (all endpoints return correct data from MongoDB)
  2. When a user edits a program, the previous version is preserved and the version number increments
  3. When a user starts a workout, the workout document captures the exact program version used (future program edits do not alter past workout records)
  4. User can view workout history and see the program configuration that was active when each workout was logged
  5. All backend endpoints are async (no sync SQLAlchemy code remains in route handlers)
**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD

### Phase 8: Authentication and Multi-User
**Goal**: Users authenticate via Telegram and all data is isolated per user, with dev-mode bypass for local development
**Depends on**: Phase 7
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, USER-01, USER-02, USER-03
**Success Criteria** (what must be TRUE):
  1. User sees a Telegram Login Widget on the login page and can authenticate to access the app
  2. On first login, the user's account is automatically created using their Telegram name and username (no registration form needed)
  3. User stays logged in across browser sessions (JWT valid for 1 year) and unauthenticated requests to protected endpoints are rejected with 401
  4. Each user sees only their own exercises, programs, and workouts (no data leakage between users)
  5. Developer can bypass Telegram auth on localhost using a dev-mode flag for local development without a Telegram bot
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD

### Phase 9: Docker Deployment
**Goal**: The entire application runs via Docker Compose with nginx reverse proxy, suitable for both local development and VPS deployment
**Depends on**: Phase 8
**Requirements**: DOCK-01, DOCK-02, DOCK-03, DOCK-04, DOCK-05, DOCK-06
**Success Criteria** (what must be TRUE):
  1. Running docker-compose up starts nginx, backend, and MongoDB as three containers, and the app is accessible in a browser
  2. nginx serves the Vue SPA for all non-API routes and proxies /api/* requests to the backend (client-side routing works without 404s)
  3. MongoDB data survives container restarts (Docker volume persistence verified)
  4. A documented dev pipeline exists: build, start, and run backend/frontend/integration tests from a single command sequence
  5. Production docker-compose config is ready for VPS deployment with bare IP access
**Plans**: TBD

Plans:
- [ ] 09-01: TBD
- [ ] 09-02: TBD

### Phase 10: Cleanup
**Goal**: Legacy SQLite dependencies are removed and the scripts repo is archived, leaving a clean MongoDB-only codebase
**Depends on**: Phase 9
**Requirements**: CLN-01, CLN-02
**Success Criteria** (what must be TRUE):
  1. Backend has no SQLAlchemy or Alembic imports or dependencies (clean install succeeds without them)
  2. Scripts repo is archived with a clear note that analytics and export functionality is deferred to a future milestone
**Plans**: TBD

Plans:
- [ ] 10-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 7 → 8 → 9 → 10

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation and Schema | v1.0 | 3/3 | Complete | 2026-03-06 |
| 2. Exercise and Program Management | v1.0 | 4/4 | Complete | 2026-03-06 |
| 3. Workout Logging | v1.0 | 3/3 | Complete | 2026-03-06 |
| 4. History and Progression | v1.0 | 3/3 | Complete | 2026-03-07 |
| 5. Analytics and Data Tools | v1.0 | 2/2 | Complete | 2026-03-07 |
| 6. Integration Fixes and Polish | v1.0 | 1/1 | Complete | 2026-03-07 |
| 7. MongoDB Data Layer | v1.1 | 0/? | Not started | - |
| 8. Authentication and Multi-User | v1.1 | 0/? | Not started | - |
| 9. Docker Deployment | v1.1 | 0/? | Not started | - |
| 10. Cleanup | v1.1 | 0/? | Not started | - |
