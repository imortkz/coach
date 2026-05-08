# Requirements: GymCoach

**Defined:** 2026-03-09
**Core Value:** Log workouts quickly at the gym and see what weight to lift next based on past performance

## v1.1 Requirements

Requirements for MongoDB migration and deployment milestone. Each maps to roadmap phases.

### Database Migration

- [ ] **DB-01**: All data storage uses MongoDB with Beanie ODM instead of SQLite/SQLAlchemy
- [ ] **DB-02**: Exercises stored as a shared collection with document-native schema
- [ ] **DB-03**: Programs stored as documents with embedded exercises and sets
- [ ] **DB-04**: Workouts stored as self-contained documents with full exercise/set data denormalized at write time
- [ ] **DB-05**: All backend endpoints converted from sync def to async def
- [ ] **DB-06**: Existing v1.0 test data dropped (clean start with MongoDB)

### Authentication

- [ ] **AUTH-01**: User can authenticate via Telegram Login Widget on the login page
- [ ] **AUTH-02**: Backend verifies Telegram login using HMAC-SHA-256 with bot token
- [ ] **AUTH-03**: Authenticated user receives a JWT session token valid for 1 year
- [ ] **AUTH-04**: User account is auto-created on first Telegram login with name/username from Telegram
- [ ] **AUTH-05**: All API endpoints except auth and health require valid JWT Bearer token
- [ ] **AUTH-06**: Dev-mode auth bypass available for localhost development without Telegram bot

### Multi-User

- [ ] **USER-01**: Every document (exercise, program, workout) has a user_id field
- [ ] **USER-02**: Every query filters by the authenticated user's ID
- [ ] **USER-03**: Compound indexes include user_id as prefix for query performance

### Program Versioning

- [ ] **VER-01**: Program document includes version tracking (version number increments on edit)
- [ ] **VER-02**: When a program is edited, previous version snapshot is preserved
- [ ] **VER-03**: Workout documents reference the specific program version they were logged against
- [ ] **VER-04**: User can view workout history with the correct program version context

### Docker Deployment

- [ ] **DOCK-01**: docker-compose.yml defines 3 services: nginx, backend, mongodb
- [ ] **DOCK-02**: nginx serves built Vue SPA and reverse proxies /api/* to backend
- [ ] **DOCK-03**: MongoDB data persists via Docker volume
- [ ] **DOCK-04**: Automated dev pipeline: docker-compose build + up + run tests (backend, frontend, integration)
- [ ] **DOCK-05**: Production docker-compose and nginx config for VPS deployment with bare IP
- [ ] **DOCK-06**: Telegram bot setup documented as deployment prerequisite (@BotFather steps)

### Cleanup

- [ ] **CLN-01**: SQLAlchemy and Alembic dependencies removed from backend
- [ ] **CLN-02**: Scripts repo archived (analytics/export deferred to future milestone)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Security

- **SEC-01**: SSL/TLS with Let's Encrypt and custom domain
- **SEC-02**: MongoDB authentication enabled (username/password)

### Operations

- **OPS-01**: CI/CD pipeline for automated deployment
- **OPS-02**: MongoDB backup/restore scripts
- **OPS-03**: Health monitoring and alerting

### Features

- **FEAT-01**: User profile page (display Telegram name/photo)
- **FEAT-02**: Admin dashboard (view all users)
- **FEAT-03**: Exercise sharing between users
- **FEAT-04**: Analytics reimplemented as web endpoints (from retired scripts repo)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Full OAuth2 / OpenID Connect | Telegram Login Widget uses HMAC, not OAuth. Simpler and equally secure. |
| Refresh token rotation | Overengineered for personal gym app. 1-year JWT sufficient. |
| MongoDB Atlas / cloud hosting | Self-hosted Docker is simpler, free, and keeps data local. |
| Role-based access control (RBAC) | All users are equal. Data isolated by user_id. |
| Real-time sync / WebSockets | One device at a time (phone at gym). REST is sufficient. |
| Per-collection multi-tenancy | Overkill for <100 users. Shared collections with user_id. |
| Bidirectional program version diff | Users just need to see the version, not a side-by-side diff. |
| Nutrition / calorie tracking | Separate domain |
| Mobile native app | Web only, mobile-responsive sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DB-01 | Phase 7 | Pending |
| DB-02 | Phase 7 | Pending |
| DB-03 | Phase 7 | Pending |
| DB-04 | Phase 7 | Pending |
| DB-05 | Phase 7 | Pending |
| DB-06 | Phase 7 | Pending |
| AUTH-01 | Phase 8 | Pending |
| AUTH-02 | Phase 8 | Pending |
| AUTH-03 | Phase 8 | Pending |
| AUTH-04 | Phase 8 | Pending |
| AUTH-05 | Phase 8 | Pending |
| AUTH-06 | Phase 8 | Pending |
| USER-01 | Phase 8 | Pending |
| USER-02 | Phase 8 | Pending |
| USER-03 | Phase 8 | Pending |
| VER-01 | Phase 7 | Pending |
| VER-02 | Phase 7 | Pending |
| VER-03 | Phase 7 | Pending |
| VER-04 | Phase 7 | Pending |
| DOCK-01 | Phase 9 | Pending |
| DOCK-02 | Phase 9 | Pending |
| DOCK-03 | Phase 9 | Pending |
| DOCK-04 | Phase 9 | Pending |
| DOCK-05 | Phase 9 | Pending |
| DOCK-06 | Phase 9 | Pending |
| CLN-01 | Phase 10 | Pending |
| CLN-02 | Phase 10 | Pending |

**Coverage:**
- v1.1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0

---
*Requirements defined: 2026-03-09*
*Last updated: 2026-03-09 after roadmap creation*
