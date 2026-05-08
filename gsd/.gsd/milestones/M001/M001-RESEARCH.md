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

# Architecture Research

**Domain:** MongoDB migration, Telegram auth, Docker deployment for existing gym training app
**Researched:** 2026-03-09
**Confidence:** HIGH (verified against official docs and existing codebase)

## System Overview

### Current Architecture (v1.0)

```
                        Browser (mobile)
                            |
                    http://localhost:5173
                            |
                   ┌────────┴────────┐
                   │  Vue 3 SPA      │  (Vite dev server)
                   │  Pinia stores   │
                   │  Vue Router     │
                   └────────┬────────┘
                            |
                    fetch('/api/...')
                            |
                   ┌────────┴────────┐
                   │  FastAPI        │  :8000
                   │  sync def       │
                   │  SQLAlchemy ORM │
                   └────────┬────────┘
                            |
                   ┌────────┴────────┐
                   │  SQLite + WAL   │  ../data/gymcoach.db
                   └─────────────────┘
```

### Target Architecture (v1.1)

```
                        Browser (mobile)
                            |
                     https://bare-ip
                            |
               ┌────────────┴────────────┐
               │        nginx            │  :80/:443
               │  ┌──────────────────┐   │
               │  │ /         → SPA  │   │  static files (built Vue)
               │  │ /api/*    → proxy│   │  proxy_pass fastapi:8000
               │  └──────────────────┘   │
               └────────────┬────────────┘
                            |
               ┌────────────┴────────────┐
               │  FastAPI                │  :8000 (internal only)
               │  ┌──────────────────┐   │
               │  │ JWT auth midware │   │  Bearer token from cookie/header
               │  │ async def routes │   │  Motor async driver
               │  │ MongoDB driver   │   │  no ORM, raw collections
               │  └──────────────────┘   │
               └────────────┬────────────┘
                            |
               ┌────────────┴────────────┐
               │  MongoDB 7.x            │  :27017 (internal only)
               │  gymcoach database       │
               │  ├── users              │
               │  ├── exercises          │
               │  ├── programs           │  (embedded exercises + versioning)
               │  └── workouts           │  (self-contained documents)
               └─────────────────────────┘
```

### Docker Compose Service Topology

```
docker-compose.yml
├── nginx          :80 → host :80
│   ├── serves /usr/share/nginx/html (built SPA)
│   └── proxy_pass /api → http://fastapi:8000
├── fastapi        :8000 (internal)
│   ├── connects to mongodb:27017
│   └── env: MONGODB_URL, TELEGRAM_BOT_TOKEN, JWT_SECRET
└── mongodb        :27017 (internal)
    └── volume: mongodb_data:/data/db
```

## Component Responsibilities

| Component | Current (v1.0) | New (v1.1) | Change Type |
|-----------|---------------|------------|-------------|
| `app/database.py` | SQLAlchemy engine + `get_db()` | Motor `AsyncIOMotorClient` + `get_db()` | **REPLACE** |
| `app/config.py` | `DATABASE_URL` (SQLite path) | `MONGODB_URL`, `JWT_SECRET`, `TELEGRAM_BOT_TOKEN` | **REPLACE** |
| `app/main.py` | CORS middleware, router includes | + JWT middleware, + auth router, + lifespan (Motor init) | **MODIFY** |
| `app/exercises/models.py` | SQLAlchemy `Base` + `Exercise` class | Gone -- no ORM models | **DELETE** |
| `app/programs/models.py` | SQLAlchemy `Program`, `ProgramExercise`, `ProgramSet` | Gone -- no ORM models | **DELETE** |
| `app/workouts/models.py` | SQLAlchemy `Workout`, `WorkoutSet`, `Setting` | Gone -- no ORM models | **DELETE** |
| `app/exercises/routes.py` | `sync def` + `db.query(Exercise)` | `async def` + `db.exercises.find()` | **REWRITE** |
| `app/programs/routes.py` | SQLAlchemy relationships, eager loading | MongoDB embedded docs, version stamping | **REWRITE** |
| `app/workouts/routes.py` | SQLAlchemy joins, subqueries | MongoDB aggregation pipeline | **REWRITE** |
| `app/auth/` | Does not exist | **NEW**: Telegram verify, JWT issue/validate, user CRUD | **NEW** |
| `app/auth/dependencies.py` | Does not exist | **NEW**: FastAPI dependency extracting user from JWT | **NEW** |
| `frontend/src/stores/auth.ts` | Does not exist | **NEW**: login state, token storage, Telegram callback | **NEW** |
| `frontend/src/views/LoginView.vue` | Does not exist | **NEW**: Telegram Login Widget embed | **NEW** |
| `frontend/src/composables/useApi.ts` | Does not exist | **NEW**: centralized fetch with auth header | **NEW** |
| `frontend/src/router/index.ts` | No auth guards | + navigation guard checking auth state | **MODIFY** |
| `nginx/nginx.conf` | Does not exist | **NEW**: reverse proxy + SPA serving config | **NEW** |
| `docker-compose.yml` | Does not exist (Dockerfile only in backend) | **NEW**: 3-service orchestration | **NEW** |
| `frontend/Dockerfile` | Does not exist | **NEW**: multi-stage build (npm build + nginx) | **NEW** |
| `scripts/` repo | Alembic migrations, seed, analytics, export | **REMOVE** entirely -- functionality moves to backend/frontend | **DELETE REPO** |

## Recommended Project Structure

### Backend (modified)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, CORS, routers
│   ├── config.py            # env vars: MONGODB_URL, JWT_SECRET, BOT_TOKEN
│   ├── database.py          # Motor client init, get_db dependency
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py        # POST /api/auth/telegram (verify + JWT)
│   │   ├── dependencies.py  # get_current_user dependency
│   │   ├── telegram.py      # HMAC-SHA256 verification logic
│   │   └── jwt.py           # encode/decode JWT with PyJWT
│   ├── exercises/
│   │   ├── __init__.py
│   │   ├── routes.py        # async def, Motor queries
│   │   └── schemas.py       # Pydantic models (keep, adapt IDs)
│   ├── programs/
│   │   ├── __init__.py
│   │   ├── routes.py        # async def, embedded doc handling
│   │   └── schemas.py       # Pydantic models with version field
│   ├── workouts/
│   │   ├── __init__.py
│   │   ├── routes.py        # async def, aggregation pipelines
│   │   └── schemas.py       # Pydantic models
│   └── seed.py              # exercise seed data (moved from scripts/)
├── tests/
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

### Frontend (modified)

```
frontend/
├── src/
│   ├── App.vue
│   ├── main.ts
│   ├── router/
│   │   └── index.ts          # + auth guard, + /login route
│   ├── stores/
│   │   ├── auth.ts           # NEW: JWT token, user info, login/logout
│   │   ├── exercises.ts      # modify: use useApi composable
│   │   ├── programs.ts       # modify: use useApi composable
│   │   ├── workouts.ts       # modify: use useApi composable
│   │   └── history.ts        # modify: use useApi composable
│   ├── composables/
│   │   ├── useApi.ts         # NEW: centralized fetch with auth header
│   │   ├── useSwipeLeft.ts
│   │   └── useRestTimer.ts
│   ├── views/
│   │   ├── LoginView.vue     # NEW: Telegram Login Widget
│   │   └── ... (existing views unchanged)
│   └── components/
│       └── ... (existing components unchanged)
├── Dockerfile                 # NEW: multi-stage build
└── ...
```

### Root-level Docker files (at parent of all repos)

```
../
├── docker-compose.yml         # NEW: 3-service orchestration
├── nginx/
│   └── nginx.conf             # NEW: reverse proxy config
├── .env                       # NEW: secrets (not committed)
├── .env.example               # NEW: template for required vars
├── backend/
├── frontend/
└── gsd/
```

### Structure Rationale

- **No ODM (no Beanie/MongoEngine):** The app has 4 collections with straightforward queries. Motor with raw collection access is simpler and faster than adding an ODM abstraction layer. Pydantic schemas already handle validation.
- **auth/ as a module:** Keeps Telegram verification, JWT logic, and user dependency isolated. Easy to swap auth providers later.
- **useApi composable:** Centralizes Authorization header injection so individual stores do not manage tokens independently. All 4 existing stores currently use raw `fetch()` -- replacing with `useApi` is a targeted change.
- **scripts/ repo eliminated:** With MongoDB (no schema migrations needed), seed data moves to a backend startup hook. Analytics and export move to frontend views or backend endpoints.
- **models.py files deleted:** SQLAlchemy ORM models are not needed with MongoDB. Pydantic schemas in `schemas.py` handle validation. MongoDB collections are accessed directly via Motor.

## Architectural Patterns

### Pattern 1: Motor AsyncIOMotorClient via FastAPI Lifespan

**What:** Initialize the MongoDB client once at app startup, close on shutdown, inject via dependency.
**When to use:** Always -- this is the standard pattern for Motor + FastAPI.
**Trade-offs:** Simple and efficient. No connection pool management headaches since Motor handles pooling internally.

**IMPORTANT NOTE ON MOTOR VS PYMONGO ASYNC:** Motor was deprecated May 14, 2025 (EOL May 14, 2026). MongoDB recommends migrating to PyMongo's `AsyncMongoClient`. However, Motor 3.x is still supported and widely documented. For this project, **use Motor** because: (1) it is still supported through 2026, (2) the vast majority of tutorials and examples use it, (3) the migration to PyMongo Async is a straightforward find-replace (`AsyncIOMotorClient` to `pymongo.AsyncMongoClient`) when needed. **Confidence: HIGH** -- verified from official MongoDB deprecation notice.

**Example:**
```python
# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URL

client: AsyncIOMotorClient | None = None
db = None

async def init_db():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.gymcoach

async def close_db():
    global client
    if client:
        client.close()

async def get_db():
    return db

# app/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()

app = FastAPI(title="GymCoach API", lifespan=lifespan)
```

### Pattern 2: Sync-to-Async Endpoint Migration

**What:** All existing `def` endpoints become `async def` since Motor requires `await`.
**When to use:** Every route that touches the database.
**Trade-offs:** This is a full rewrite of every route function body. No partial migration path -- all DB-touching routes must be async when using Motor.

**Critical detail:** The existing codebase uses `sync def` for all 15 endpoints with SQLAlchemy ORM calls like `db.query(Exercise).filter(...)`. With Motor, every query becomes `await db.collection.find(...)`. The URL paths and response schemas stay the same, but the route bodies are completely rewritten.

**Example:**
```python
# BEFORE (SQLAlchemy sync)
@router.get("/", response_model=list[ExerciseRead])
def list_exercises(db: Session = Depends(get_db)):
    return db.query(Exercise).order_by(Exercise.name).all()

# AFTER (Motor async)
@router.get("/", response_model=list[ExerciseRead])
async def list_exercises(db=Depends(get_db), user=Depends(get_current_user)):
    cursor = db.exercises.find({"user_id": user["telegram_id"]}).sort("name", 1)
    exercises = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        exercises.append(ExerciseRead(**doc))
    return exercises
```

### Pattern 3: JWT Auth as FastAPI Dependency

**What:** A reusable `get_current_user` dependency that extracts and validates JWT from the Authorization header.
**When to use:** Every authenticated endpoint (all endpoints except `/api/auth/telegram` and `/api/health`).
**Trade-offs:** Clean, per-route injection. No global middleware needed. FastAPI auto-documents it in OpenAPI.

**Use PyJWT, not python-jose.** The FastAPI documentation has switched from recommending python-jose (last updated 2021, known security issues) to PyJWT (actively maintained). **Confidence: HIGH** -- verified from official FastAPI security tutorial and GitHub discussion #9587.

**Example:**
```python
# app/auth/jwt.py
import jwt
from datetime import datetime, timedelta, timezone
from app.config import JWT_SECRET

def create_token(telegram_id: int) -> str:
    payload = {
        "sub": str(telegram_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=365),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None

# app/auth/dependencies.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db),
):
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"telegram_id": int(payload["sub"])})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

### Pattern 4: Telegram Login Widget Authentication Flow

**What:** Frontend embeds the Telegram widget script, user authenticates with Telegram, widget calls a JS callback with user data + HMAC hash, frontend POSTs to backend, backend verifies the hash using the bot token and returns a JWT.
**When to use:** Single auth flow for the entire app.
**Trade-offs:** No password management, no email verification, no OAuth complexity. Requires the user to have a Telegram account. Requires a registered bot via @BotFather (but no bot logic -- just an identity provider).

**Verification algorithm** (from official Telegram docs at core.telegram.org/widgets/login):
1. Sort all received fields alphabetically (excluding `hash`)
2. Create a data-check-string by joining them as `key=value` with newline separators
3. Create secret key: `SHA256(bot_token)`
4. Compute: `HMAC-SHA256(data_check_string, secret_key)`
5. Compare the hex digest with the received `hash` field
6. Additionally check `auth_date` is not stale (reject if older than 5 minutes)

**Confidence: HIGH** -- verified directly from official Telegram documentation.

**Complete flow:**
```
1. User opens /login
2. Vue renders Telegram Login Widget <script> tag
3. User clicks "Log in with Telegram" -> Telegram popup
4. Telegram returns: {id, first_name, last_name, username, photo_url, auth_date, hash}
5. Frontend POSTs this payload to POST /api/auth/telegram
6. Backend:
   a. Verifies HMAC-SHA256 hash
   b. Checks auth_date freshness
   c. Upserts user document in users collection
   d. Returns JWT (1-year expiry, telegram_id as sub claim)
7. Frontend stores JWT in localStorage, updates auth store
8. All subsequent API calls include Authorization: Bearer <jwt>
```

**Backend verification example:**
```python
# app/auth/telegram.py
import hashlib
import hmac
from app.config import TELEGRAM_BOT_TOKEN

def verify_telegram_data(data: dict) -> bool:
    received_hash = data.get("hash")
    if not received_hash:
        return False

    # Build data-check-string (sorted, excluding hash)
    check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
        if k != "hash" and v is not None
    )

    secret = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    computed = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(computed, received_hash)
```

### Pattern 5: MongoDB Document Schema with Program Versioning

**What:** Programs store their exercise configuration as an embedded array. When a program is edited, the current version is archived into a `versions[]` array and the version number increments. Workouts reference a specific `program_version` so history stays consistent even if the program changes.
**When to use:** Every program update.
**Trade-offs:** Slightly larger program documents but eliminates the need for a separate history collection. Programs change infrequently (perfect fit for embedded versioning per MongoDB's official documentation).

**Confidence: HIGH** -- MongoDB's own documentation recommends embedded versioning for "documents that are updated infrequently" and "few documents that require version tracking."

**Schema design:**
```javascript
// programs collection
{
  _id: ObjectId,
  user_id: 123456789,                 // Telegram user ID
  name: "Push Pull Legs A",
  version: 3,                         // current version number
  rest_timer_disabled: false,
  exercises: [                         // current version's exercises
    {
      exercise_id: ObjectId,
      exercise_name: "Bench Press",    // denormalized for reads
      equipment: "Barbell",
      order: 1,
      sets: [
        { set_number: 1, target_reps: 5, target_weight_kg: 80.0, is_warmup: false }
      ]
    }
  ],
  versions: [                          // previous versions (append-only)
    {
      version: 2,
      archived_at: ISODate,
      exercises: [...]                 // snapshot of exercises at v2
    }
  ],
  created_at: ISODate,
  updated_at: ISODate
}

// workouts collection -- self-contained document
{
  _id: ObjectId,
  user_id: 123456789,
  program_id: ObjectId,
  program_name: "Push Pull Legs A",    // denormalized
  program_version: 3,                  // which version was active when workout started
  started_at: ISODate,
  completed_at: ISODate | null,
  sets: [                              // embedded, not a separate collection
    {
      exercise_id: ObjectId,
      exercise_name: "Bench Press",    // denormalized
      equipment: "Barbell",
      set_number: 1,
      weight_kg: 82.5,
      reps: 5,
      is_warmup: false
    }
  ]
}

// exercises collection
{
  _id: ObjectId,
  user_id: 123456789 | null,          // null = seeded/global exercise
  name: "Bench Press",
  muscle_group: "Chest",
  equipment: "Barbell",
  is_custom: false
}

// users collection
{
  _id: ObjectId,
  telegram_id: 123456789,             // unique index
  first_name: "John",
  last_name: "Doe",
  username: "johndoe",
  photo_url: "https://...",
  created_at: ISODate,
  last_login: ISODate
}
```

**Key schema decisions:**
- **Workout sets embedded, not a separate collection:** In v1.0, `workout_sets` is a separate SQL table joined to `workouts`. In MongoDB, sets are embedded in the workout document. A single workout has at most ~30 sets -- well within MongoDB's 16MB document limit. This eliminates joins and makes workout reads a single document fetch.
- **Exercise name denormalized into workout sets:** Avoids needing to look up the exercises collection when displaying workout history. If an exercise is renamed, old workouts still show the original name.
- **Program version snapshot in workouts:** `program_version` is a number, not a copy of the program. If needed, the full program state at that version can be reconstructed from the program's `versions[]` array.

### Pattern 6: nginx Reverse Proxy + SPA Serving

**What:** Single nginx container serves the built Vue SPA for all non-API routes and proxies `/api/*` to the FastAPI container.
**When to use:** Production deployment.

**Example nginx.conf:**
```nginx
server {
    listen 80;

    root /usr/share/nginx/html;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://fastapi:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SPA fallback -- serve index.html for all non-file routes
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Frontend Dockerfile (multi-stage):**
```dockerfile
# Build stage
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

## Data Flow

### Authentication Flow

```
[Telegram Widget]
    | JS callback with {id, first_name, ..., hash}
    v
[LoginView.vue] --> POST /api/auth/telegram --> [auth/routes.py]
                                                     |
                                                verify HMAC hash
                                                     |
                                                upsert user in MongoDB
                                                     |
                                                sign JWT (PyJWT, 1yr)
                                                     |
[auth store] <-- { token, user } <------------- return JWT + user info
    |
localStorage.setItem('token', jwt)
    |
[useApi composable] adds Authorization header to all fetches
```

### Authenticated API Request Flow

```
[Pinia Store action]
    |
[useApi] --> fetch('/api/exercises', { headers: { Authorization: Bearer <jwt> } })
    |
[nginx] --> proxy_pass --> [FastAPI]
    |
[get_current_user dependency] --> decode JWT --> find user --> inject user dict
    |
[route handler] --> await db.exercises.find({"user_id": user["telegram_id"]})
    |
[Motor] --> MongoDB query --> async cursor --> list
    |
[Pydantic schema] --> JSON response --> [nginx] --> [frontend]
```

### Program Update with Versioning

```
[ProgramEditView.vue] --> PUT /api/programs/{id}
    |
[route handler]:
    1. Load current program document from MongoDB
    2. Push current {version, archived_at, exercises} into versions[] array
    3. Increment version number
    4. Replace exercises[] with new data from request
    5. Set updated_at to now
    6. await db.programs.replace_one({"_id": program_id, "user_id": user_id}, updated_doc)
    |
[response] --> updated program with new version number
```

### Workout Start with Pre-fill + Progression

```
[ProgramPicker] --> POST /api/workouts { program_id }
    |
[route handler]:
    1. Load program (current version) from MongoDB
    2. For each exercise, query last completed workout with that exercise
       (db.workouts.find({"user_id": uid, "completed_at": {$ne: null},
        "sets.exercise_id": eid}).sort("completed_at", -1).limit(1))
    3. Compute pre-fill: last session actuals or program template targets
    4. Compute progression: check if all non-warmup sets hit target reps
       --> if yes, suggest weight increase by equipment increment
       --> if no, suggest keeping current weight
    5. Create workout document with program_version stamp
    |
[response] --> { workout, pre_fill, suggestions }
```

## Key Integration Points

### What Changes in Each Repo

**backend/ (major changes -- rewrite scope)**
- **Remove:** SQLAlchemy, all `models.py` files (3 files)
- **Add:** Motor, PyJWT, python-dotenv
- **Rewrite:** All route handlers in 3 modules (sync to async, ORM to raw MongoDB)
- **New:** `app/auth/` module (4 files), `app/seed.py`
- **Modify:** `Dockerfile` (remove SQLite references), `pyproject.toml` (swap dependencies)
- **Keep:** Pydantic schemas (`schemas.py` files) with minor changes (int IDs to str)

**frontend/ (moderate changes -- additive scope)**
- **New:** `LoginView.vue`, `stores/auth.ts`, `composables/useApi.ts`, `Dockerfile`
- **Modify:** Router (add `/login` route, add auth guard), all 4 stores (replace raw `fetch` with `useApi`)
- **Unchanged:** All existing Vue components. API response shapes stay the same (only ID types change from int to string)

**scripts/ (eliminated)**
- Alembic migrations: Not needed with MongoDB (schemaless)
- Exercise seed: Moves to backend `app/seed.py` (run on first startup or via endpoint)
- Analytics CLI: Deferred -- can be reimplemented as backend endpoints later
- JSON/CSV export: Deferred -- can be reimplemented as backend endpoints later

**Root level (new files)**
- `docker-compose.yml`: 3 services (nginx, fastapi, mongodb)
- `nginx/nginx.conf`: reverse proxy + SPA config
- `.env.example`: required environment variables template

### ID Migration: Integer to String

The most pervasive frontend change. Current app uses integer IDs:
- Route params: `/exercises/42/history`
- API responses: `{ id: 42, program_id: 7 }`
- TypeScript types: `id: number`

With MongoDB, IDs become 24-character hex strings (`"507f1f77bcf86cd799439011"`).

**Migration strategy:** Change `id: number` to `id: string` in TypeScript types. Pydantic schemas change `id: int` to `id: str`. Vue Router params already handle strings natively. No other frontend logic changes needed since IDs are opaque tokens used only for API calls and route params.

### Multi-User Data Isolation

Every database query must filter by `user_id`. Enforced by:
1. The `get_current_user` dependency injects the authenticated user into every route
2. Every route handler includes `{"user_id": user["telegram_id"]}` in all MongoDB queries

Seeded exercises (`is_custom: false`) have `user_id: null` and are visible to all users via `{"$or": [{"user_id": uid}, {"user_id": null}]}`.

### CORS Changes

- **Dev mode:** Keep CORS middleware allowing `localhost:5173` (Vite dev server talks directly to FastAPI on port 8000)
- **Production:** nginx serves both SPA and proxies API on the same origin -- no CORS needed

### Required MongoDB Indexes

```javascript
// Create at app startup
db.users.createIndex({"telegram_id": 1}, {unique: true})
db.exercises.createIndex({"user_id": 1, "name": 1})
db.programs.createIndex({"user_id": 1})
db.workouts.createIndex({"user_id": 1, "completed_at": -1})
db.workouts.createIndex({"user_id": 1, "completed_at": null})  // active workout lookup
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-5 users | Current plan is sufficient. Single MongoDB instance, no replicas. |
| 50-100 users | Add compound indexes listed above. Still single instance. |
| 1000+ users | Add MongoDB replica set for availability. Consider read replicas. |

### Scaling Priorities

1. **First bottleneck:** Missing indexes. Without `{user_id: 1}` index, queries scan all documents. Create indexes at startup.
2. **Second bottleneck:** Workout history aggregation in progression computation. The `compute_progression` function queries across workout documents. Index on `{user_id: 1, completed_at: -1}` is essential.

For a personal tool with a handful of users, scaling is not a real concern. The architecture is right-sized.

## Anti-Patterns

### Anti-Pattern 1: Using Beanie/MongoEngine ODM

**What people do:** Add an ODM layer to get "ORM-like" convenience with MongoDB.
**Why it's wrong for this project:** The app has 4 collections with simple CRUD. An ODM adds dependency weight, learning curve, and abstraction leaks (especially around embedded documents and aggregation pipelines). Motor's raw API is more transparent and sufficient.
**Do this instead:** Use Motor directly with Pydantic schemas for validation. The schemas already exist from v1.0.

### Anti-Pattern 2: Separate Collection for Program Version History

**What people do:** Create a `program_versions` collection and store version history separately from the program.
**Why it's wrong for this project:** Programs change rarely (user edits their routine every few weeks/months). Embedded versioning keeps the document self-contained and avoids cross-collection lookups. MongoDB explicitly recommends embedded versioning for infrequently updated documents.
**Do this instead:** Embed `versions[]` array inside the program document. Archive old version before updating.

### Anti-Pattern 3: Storing JWT in httpOnly Cookie with CSRF Protection

**What people do:** Set JWT as httpOnly cookie for "security" against XSS.
**Why it's wrong for this project:** This is a personal training app accessed by its owner, not a multi-tenant banking app. httpOnly cookies require CSRF token management, complicate the API proxy setup, and prevent easy token inspection during development. The threat model does not justify the complexity.
**Do this instead:** Store JWT in localStorage. The token has a 1-year expiry. The app runs on a personal VPS accessed by the owner.

### Anti-Pattern 4: Partial Async Migration (Mixed Sync/Async Routes)

**What people do:** Convert some endpoints to async while leaving others as sync, planning to migrate incrementally.
**Why it's wrong:** Motor requires `await` for all database operations. Any route touching the database must be `async def`. Mixing sync SQLAlchemy routes with async Motor routes in the same app creates confusion and fragile code. A clean cutover is better.
**Do this instead:** Rewrite all routes as async in one pass per module. Keep the same URL structure and response shapes so the frontend needs only minimal changes.

### Anti-Pattern 5: Using python-jose for JWT

**What people do:** Follow older FastAPI tutorials that recommend python-jose.
**Why it's wrong:** python-jose has not been updated since 2021 and has known security issues. FastAPI's official documentation has switched to recommending PyJWT.
**Do this instead:** Use `pyjwt` package. Actively maintained, has all needed features (HS256 signing, expiry validation, claim verification).

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Telegram BotFather | One-time setup: create bot, `/setdomain` command | No ongoing bot logic. Bot serves only as identity provider. |
| Telegram Login Widget | Frontend `<script>` tag embed with `data-onauth` JS callback | Widget returns user data + HMAC hash. Callback mode preferred over redirect mode for SPA. |
| MongoDB 7.x | Motor `AsyncIOMotorClient` via Docker internal network | Connection string: `mongodb://mongodb:27017/gymcoach` (no auth in Docker internal network) |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| nginx to FastAPI | HTTP reverse proxy on Docker network | `proxy_pass http://fastapi:8000` -- no authentication between containers |
| FastAPI to MongoDB | Motor async driver on Docker network | `mongodb://mongodb:27017` -- internal network, no auth needed |
| Frontend to Backend | REST API via nginx proxy | Same origin in production (no CORS). CORS middleware for local dev only. |
| Auth module to Route handlers | FastAPI dependency injection | `Depends(get_current_user)` added to every route except auth and health |

### Environment Variables

```bash
# Required in backend container / .env file
MONGODB_URL=mongodb://mongodb:27017/gymcoach
TELEGRAM_BOT_TOKEN=<from @BotFather>
JWT_SECRET=<random 64-char hex string>

# Frontend build-time (Vite env)
VITE_TELEGRAM_BOT_NAME=<bot username without @>
```

## Build Order Recommendation

Based on dependency analysis, the recommended implementation order:

1. **Docker Compose + MongoDB** -- get the 3-service stack running first. Backend connects to MongoDB, nginx proxies. Validates infrastructure before rewriting code.
2. **MongoDB data layer** -- rewrite `database.py` (Motor client), delete all `models.py` files. Rewrite one route module at a time starting with exercises (simplest, no relationships).
3. **Exercise seed migration** -- move seed data from scripts repo to backend. Run on startup or via endpoint.
4. **Auth (Telegram + JWT)** -- add `app/auth/` module. Requires Docker (for consistent domain for Telegram widget) and MongoDB (for users collection).
5. **Multi-user data isolation** -- add `user_id` filters to all queries and `Depends(get_current_user)` to all routes. Requires auth to be working.
6. **Program versioning** -- modify program update logic to archive versions. Independent of auth but needs MongoDB.
7. **Frontend auth integration** -- login page, auth store, useApi composable, router guard. Requires backend auth endpoints to be working.
8. **Scripts repo cleanup** -- verify all needed functionality has moved, then archive the repo.

**Ordering rationale:** Infrastructure (Docker) must work before code changes can be tested in the target environment. The database layer rewrite is the largest single change and unblocks everything else. Auth must work before multi-user isolation can be verified. Frontend auth changes are last because they depend on all backend auth being complete.

## Sources

- [Motor (Async Driver) - MongoDB Docs](https://www.mongodb.com/docs/drivers/motor/) -- Motor deprecation notice (May 2025, EOL May 2026), PyMongo Async migration path
- [PyMongo AsyncMongoClient FastAPI Tutorial](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/integrations/fastapi-integration/) -- official integration patterns
- [Telegram Login Widget - Official Docs](https://core.telegram.org/widgets/login) -- widget embed, HMAC-SHA256 verification algorithm, data fields, domain setup
- [FastAPI Security - OAuth2 with JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) -- PyJWT recommendation over python-jose
- [python-jose deprecation discussion](https://github.com/fastapi/fastapi/discussions/9587) -- FastAPI community discussion on switching to PyJWT
- [Document Versioning Pattern - MongoDB](https://www.mongodb.com/docs/manual/data-modeling/design-patterns/data-versioning/document-versioning/) -- embedded vs separate collection versioning
- [8 FastAPI + MongoDB Best Practices](https://www.mongodb.com/developer/products/mongodb/8-fastapi-mongodb-best-practices/) -- connection pooling, indexes, error handling
- [Migrate to PyMongo Async](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/) -- Motor to PyMongo Async migration guide
- [FastAPI-Telegram-Auth Example](https://github.com/pavel-glukhov/FastAPI-Telegram-Auth) -- reference implementation for Telegram auth with FastAPI

---
*Architecture research for: GymCoach v1.1 -- MongoDB migration, Telegram auth, Docker deployment*
*Researched: 2026-03-09*

# Stack Research

**Domain:** MongoDB migration, Telegram auth, Docker deployment for gym training app
**Researched:** 2026-03-09
**Confidence:** HIGH

## Current Stack (Keep As-Is)

These are already validated in v1.0. Listed for context only -- do NOT reinstall or reconfigure.

| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | >=0.135.1 | REST API framework |
| Pydantic | >=2.12.5 | Data validation / serialization |
| Vue 3 | ^3.5.29 | Frontend SPA |
| Tailwind CSS | ^4.2.1 | Styling |
| Vite | ^7.3.1 | Frontend build tool |
| uvicorn | >=0.41.0 | ASGI server |
| Python | >=3.13 | Runtime |

## New Stack Additions

### Database: MongoDB via Beanie ODM

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Beanie | 2.0.1 | Async MongoDB ODM with Pydantic models | Native Pydantic v2 integration means document models double as API schemas. Built-in migration support. Already migrated from Motor to PyMongo Async internally -- future-proof. |
| pymongo | >=4.16.0 | Underlying async MongoDB driver | Beanie 2.0 uses PyMongo's AsyncMongoClient under the hood. Motor is deprecated (May 2026 EOL) -- PyMongo Async is the official replacement with better performance. |

**Why Beanie over raw PyMongo Async:** The existing codebase uses SQLAlchemy models mapped to Pydantic schemas. Beanie documents ARE Pydantic models, so the migration path is straightforward: replace SQLAlchemy models with Beanie Documents that serve as both DB documents and API schemas. This eliminates the model-schema duplication pattern.

**Why NOT Motor:** Motor is officially deprecated as of May 14, 2025. EOL is May 14, 2026, with only critical bug fixes until May 2027. Beanie 2.0 already migrated away from Motor to PyMongo Async. Starting a new project on Motor would be building on deprecated infrastructure.

### Authentication: Telegram Login Widget + JWT

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| PyJWT | 2.11.0 | JWT token encode/decode | Standard Python JWT library. Lightweight, well-maintained. Only dependency needed for JWT -- no framework bloat. |
| (stdlib) hashlib + hmac | -- | Telegram Login Widget hash verification | Telegram auth verification is ~15 lines of stdlib Python (HMAC-SHA256). No third-party library needed or recommended. |

**Why PyJWT over python-jose:** python-jose is less actively maintained. PyJWT is the de facto standard, lighter, and does exactly what is needed for HS256 JWT tokens.

**Why NOT fastapi-security / authlib / fastapi-users:** This is a single identity provider (Telegram) with a simple JWT session. The verification is HMAC-SHA256 (stdlib), token creation is PyJWT. An auth framework would add dependency weight and learning curve for zero benefit.

**Telegram Login Widget flow:**
1. Frontend embeds Telegram Login Widget JS snippet (CDN script tag, no npm package)
2. User authenticates via Telegram, widget calls backend callback URL with signed data
3. Backend verifies HMAC-SHA256 hash using bot token (stdlib hashlib/hmac)
4. Backend creates/finds user, issues JWT with 1-year expiry
5. Frontend stores JWT, sends as `Authorization: Bearer <token>` header

### Docker / Deployment

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| MongoDB | 8.0 (Docker: `mongo:8.0`) | Document database | LTS release line. 8.0 is production-stable. Use `mongo:8.0` tag, not `latest` or 8.2 (rapid release, shorter support). |
| nginx | 1.28-alpine (Docker: `nginx:1.28-alpine`) | Reverse proxy + SPA static file serving | Stable branch Alpine variant. ~45MB image. Serves built Vue SPA and proxies `/api` to FastAPI. |
| Docker Compose | v2 (built-in) | Multi-container orchestration | `docker compose` (v2, no hyphen) is built into Docker Desktop and Docker Engine. No separate install. |

**Why MongoDB 8.0 over 8.2:** MongoDB even-numbered releases (8.0) are LTS with long support windows. Odd/rapid releases (8.2) get shorter support. For a personal deployment, LTS stability wins.

**Why nginx Alpine over non-Alpine:** ~45MB vs ~190MB image. For a reverse proxy + static file server, Alpine is the standard choice.

### Backend Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | >=1.2.2 | Environment variable loading | Already installed. Will load TELEGRAM_BOT_TOKEN, MONGODB_URL, JWT_SECRET from .env |
| httpx | >=0.28.1 | Async HTTP client for tests | Already in dev deps. Use for integration testing auth flow. |

### Frontend Additions

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none) | -- | -- | No new npm packages needed |

**Why no frontend auth library:** JWT handling is trivial -- store token in localStorage, add to fetch headers via a composable. Telegram Login Widget is a `<script>` tag from Telegram's CDN, not an npm package. Adding an auth library would be over-engineering.

## Packages to REMOVE (After Migration)

| Package | Why Remove | Replacement |
|---------|-----------|-------------|
| sqlalchemy | No longer using SQL database | Beanie ODM |
| (scripts repo) alembic | No SQL migrations needed | Beanie built-in migration support; MongoDB schema is flexible |

**Timing:** Remove AFTER migration is complete and verified, not before. Keep SQLAlchemy importable during data migration phase so you can extract data from SQLite.

## Installation

### Backend (add to pyproject.toml)

```bash
cd ../backend

# Add new dependencies
uv add beanie pyjwt

# Remove old dependencies (AFTER migration is verified)
# uv remove sqlalchemy
```

### Frontend (no changes needed)

```bash
# No new packages needed
```

### Docker (new files, location TBD by architecture)

```yaml
# docker-compose.yml sketch
services:
  mongodb:
    image: mongo:8.0
    volumes:
      - mongo_data:/data/db

  backend:
    build: ./backend
    environment:
      - MONGODB_URL=mongodb://mongodb:27017/gymcoach
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - mongodb

  nginx:
    image: nginx:1.28-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - backend

volumes:
  mongo_data:
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Beanie 2.0 | Raw PyMongo AsyncMongoClient | If you need fine-grained aggregation pipelines or find Beanie's abstractions limiting. Not the case here -- CRUD operations map perfectly to ODM. |
| Beanie 2.0 | MongoEngine | Never for async FastAPI. MongoEngine is synchronous only. |
| PyJWT | python-jose | If you need JWS/JWE/JWK beyond basic JWT. Overkill for HS256 session tokens. |
| PyJWT | authlib | If you need full OAuth2 provider/client. We only need token creation/verification. |
| MongoDB 8.0 | PostgreSQL + asyncpg | If you wanted to stay relational. Project decision is to go document-based. |
| nginx Alpine | Caddy | If you wanted automatic HTTPS with zero config. Deferred to future milestone; nginx is more standard for Docker Compose setups. |
| Telegram Login Widget | OAuth2 (Google/GitHub) | If targeting users without Telegram. Project requirement specifies Telegram. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Motor | Deprecated May 2025, EOL May 2026. No new features. MongoDB recommends migrating to PyMongo Async. | Beanie 2.0 (uses PyMongo Async internally) |
| MongoEngine | Synchronous only. Would block FastAPI's event loop or waste threadpool. | Beanie (async-native) |
| fastapi-users | Heavy framework for simple auth. Designed for email/password + OAuth, not Telegram widget. Pulls in many transitive dependencies. | Manual JWT + HMAC verification (~50 lines total) |
| python-jose | Less maintained than PyJWT. Larger dependency surface. | PyJWT |
| mongo:latest Docker tag | Could pull 8.2 rapid release or future breaking version unpredictably. | `mongo:8.0` pinned tag |
| MongoDB server-side JSON Schema validation | Beanie + Pydantic handles validation at the application layer. Double validation adds complexity for no benefit. | Pydantic validation via Beanie Documents |
| aiosqlite | Was needed for async SQLAlchemy + SQLite. Not needed with MongoDB. | (remove when SQLAlchemy is removed) |

## Async Migration Notes

The existing backend uses `def` (sync) endpoints with SQLAlchemy. For MongoDB with Beanie:

**All endpoints must become `async def`** because Beanie operations are coroutines that must be awaited. Calling `await` inside a `def` endpoint is a syntax error.

```python
# BEFORE (v1.0 sync with SQLAlchemy)
@router.get("/exercises")
def list_exercises(db: Session = Depends(get_db)):
    return db.query(Exercise).all()

# AFTER (v1.1 async with Beanie)
@router.get("/exercises")
async def list_exercises():
    return await Exercise.find_all().to_list()
```

FastAPI allows mixing sync and async endpoints during migration, so conversion can be incremental. But the target is: all endpoints async by end of migration.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Beanie 2.0.1 | PyMongo >=4.6 | Beanie 2.0 requires PyMongo Async API (available since PyMongo 4.7+). Installs correct pymongo as dependency automatically. |
| Beanie 2.0.1 | Pydantic v2 | Beanie 2.0 requires Pydantic v2. Already using >=2.12.5 -- no conflict. |
| Beanie 2.0.1 | Python <=3.13 | Supports up to 3.13. Does NOT yet support 3.14+. Project uses >=3.13 -- compatible. |
| PyJWT 2.11.0 | Python 3.13 | Full compatibility. |
| mongo:8.0 (Docker) | PyMongo >=4.16 | MongoDB 8.0 wire protocol fully supported by current PyMongo. |

## Environment Variables (New)

| Variable | Purpose | Example |
|----------|---------|---------|
| MONGODB_URL | MongoDB connection string | `mongodb://localhost:27017/gymcoach` (dev) / `mongodb://mongodb:27017/gymcoach` (Docker) |
| TELEGRAM_BOT_TOKEN | Bot token from @BotFather for HMAC verification | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| JWT_SECRET | Secret key for signing JWT tokens | Random 64-char hex string (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| JWT_EXPIRY_DAYS | Token lifetime | `365` (1 year, per project requirements) |

## Sources

- [Motor deprecation notice](https://www.mongodb.com/docs/drivers/motor/) -- Motor deprecated May 2025, EOL May 2026 (HIGH confidence)
- [PyMongo Async migration guide](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/) -- Official Motor to PyMongo Async migration (HIGH confidence)
- [PyMongo 4.16.0 docs](https://pymongo.readthedocs.io/en/stable/) -- AsyncMongoClient API (HIGH confidence)
- [Beanie ODM documentation](https://beanie-odm.dev/) -- Async MongoDB ODM, v2.0 changelog confirms PyMongo Async migration (HIGH confidence)
- [Beanie changelog](https://beanie-odm.dev/changelog/) -- v2.0 breaking changes, Motor removal, Python 3.13 support ceiling (HIGH confidence)
- [Beanie PyPI](https://pypi.org/project/beanie/) -- Version 2.0.1 confirmed (HIGH confidence)
- [PyJWT 2.11.0 docs](https://pyjwt.readthedocs.io/en/latest/) -- Latest stable (HIGH confidence)
- [Telegram Login Widget](https://core.telegram.org/widgets/login) -- Official HMAC-SHA256 verification spec (HIGH confidence)
- [MongoDB Docker Hub](https://hub.docker.com/_/mongo) -- Official image, 8.0 LTS tag (HIGH confidence)
- [nginx Docker Hub](https://hub.docker.com/_/nginx/) -- 1.28-alpine stable branch (HIGH confidence)
- [FastAPI async/await docs](https://fastapi.tiangolo.com/async/) -- Sync vs async endpoint behavior (HIGH confidence)

---
*Stack research for: GymCoach v1.1 MongoDB Migration & Deployment*
*Researched: 2026-03-09*

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

# Pitfalls Research

**Domain:** Adding MongoDB, Telegram auth, multi-user support, program versioning, and Docker deployment to existing single-user FastAPI + Vue gym app
**Researched:** 2026-03-09
**Confidence:** HIGH (verified against official docs and current ecosystem state)

## Critical Pitfalls

### Pitfall 1: Motor is Deprecated -- Use PyMongo Async Instead

**What goes wrong:**
Building the MongoDB layer on Motor, which was deprecated on May 14, 2025. Motor reaches end-of-life May 14, 2026 (bug fixes only) and final support ends May 14, 2027. Starting a new project on a deprecated driver means a forced migration within a year.

**Why it happens:**
Most tutorials and blog posts (even recent ones) still reference Motor as the async MongoDB driver for Python. Developers search "FastAPI MongoDB async" and find Motor-based examples everywhere.

**How to avoid:**
Use the PyMongo Async API (`pymongo` with `AsyncMongoClient`) directly. It is the GA replacement, offers better performance than Motor, and is actively maintained. Import from `pymongo` not `motor`.

```python
# Correct (PyMongo Async)
from pymongo import AsyncMongoClient
client = AsyncMongoClient("mongodb://localhost:27017")

# Wrong (deprecated Motor)
from motor.motor_asyncio import AsyncIOMotorClient
```

**Warning signs:**
- Any `import motor` in the codebase
- Tutorial code referencing `AsyncIOMotorClient`
- `motor` appearing in requirements/pyproject.toml

**Phase to address:** Phase 1 (MongoDB migration) -- choose the right driver from day one.

---

### Pitfall 2: Mirroring SQL Tables as MongoDB Collections (1:1 Relational Mapping)

**What goes wrong:**
Developers create `exercises`, `program_exercises`, `program_sets`, `workout_sets` as separate collections with ObjectId references between them, exactly mirroring the SQLAlchemy models. This produces the worst of both worlds: no referential integrity (MongoDB has none) AND no query performance benefit (requires multiple round-trips or $lookup aggregations for every read).

**Why it happens:**
The existing codebase has 6 SQLAlchemy models across 6 tables with foreign keys (`exercises`, `programs`, `program_exercises`, `program_sets`, `workouts`, `workout_sets`). The path of least resistance is to map each table to a collection. The current models (Program -> ProgramExercise -> ProgramSet, Workout -> WorkoutSet) are normalized for SQL but should be embedded documents in MongoDB.

**How to avoid:**
Design document schemas based on access patterns, not existing SQL tables:
- **Programs collection:** Embed exercises array with nested sets directly in the program document. One read = full program.
- **Workouts collection:** Self-contained documents with all set data embedded. One read = full workout with exercise names, weights, reps.
- **Exercises collection:** Flat catalog, referenced by name/ID in programs and workouts but not joined at query time.

The current `program_exercises` and `program_sets` tables are join tables -- these become embedded arrays, not collections.

**Warning signs:**
- More than 3-4 collections for this domain
- Any collection named with an underscore suggesting a join table (e.g., `program_exercises`)
- Frequent use of `$lookup` in queries
- Multiple database calls to render a single page

**Phase to address:** Phase 1 (MongoDB migration) -- schema design must happen before any code is written.

---

### Pitfall 3: Missing user_id Filtering on ANY Query (Multi-User Data Leakage)

**What goes wrong:**
After adding multi-user support, a single forgotten query without `user_id` filtering exposes one user's workouts, programs, or exercises to another user. In a single-user app converted to multi-user, EVERY existing query is a potential leak because none of them filter by user.

**Why it happens:**
The existing codebase has 15 endpoints, none of which have any concept of user identity. Every `db.find()` and `db.find_one()` call must be audited. It only takes one missed endpoint (e.g., the settings endpoint, or a count query for analytics) to leak data.

**How to avoid:**
1. Create a repository/data-access layer that ALWAYS injects `user_id` into every query. Never call `collection.find()` directly from route handlers.
2. Use a helper function or base class that wraps all MongoDB operations and automatically adds the user filter:
   ```python
   async def find_for_user(collection, user_id, filter=None):
       query = {"user_id": user_id}
       if filter:
           query.update(filter)
       return collection.find(query)
   ```
3. Write integration tests that create data for User A, authenticate as User B, and verify zero results on every endpoint.

**Warning signs:**
- Any `collection.find({})` without user_id in the filter
- Route handlers that query the database without extracting user identity from the request
- Missing integration tests for cross-user data isolation
- The exercises collection (shared catalog vs. user-specific) having ambiguous ownership

**Phase to address:** Phase 2 (auth + multi-user) -- but the data access layer pattern should be established in Phase 1 so user_id can be added cleanly.

---

### Pitfall 4: Telegram Login Widget Hash Verification Done Wrong

**What goes wrong:**
The Telegram Login Widget sends auth data (id, first_name, username, auth_date, hash) to your backend. If hash verification is implemented incorrectly, an attacker can forge authentication data and impersonate any Telegram user. This is the entire security boundary of the app.

**Why it happens:**
Telegram's auth is not standard OAuth. The verification requires a specific HMAC-SHA-256 process that is easy to get subtly wrong:
1. Construct `data_check_string` by sorting all fields (except `hash`) alphabetically, formatting as `key=value`, and joining with `\n`
2. Create secret key as `SHA256(bot_token)`
3. Compare `HMAC_SHA256(data_check_string, secret_key)` against the received `hash`

Common mistakes: wrong sort order, including `hash` in the check string, using bot_token directly instead of SHA256(bot_token), not checking `auth_date` staleness.

**How to avoid:**
```python
import hashlib
import hmac
import time

def verify_telegram_auth(data: dict, bot_token: str, max_age_seconds: int = 86400) -> bool:
    check_hash = data.pop("hash")
    # 1. Sort and format
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    # 2. Secret = SHA256 of bot token
    secret = hashlib.sha256(bot_token.encode()).digest()
    # 3. HMAC-SHA256
    computed = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    # 4. Check staleness
    if time.time() - int(data["auth_date"]) > max_age_seconds:
        return False
    return hmac.compare_digest(computed, check_hash)
```

Always use `hmac.compare_digest()` (constant-time comparison) instead of `==` to prevent timing attacks.

**Warning signs:**
- Using `==` instead of `hmac.compare_digest()` for hash comparison
- Not checking `auth_date` field for replay attack prevention
- Bot token stored in code rather than environment variable
- No unit tests covering the hash verification with known test vectors

**Phase to address:** Phase 2 (authentication) -- this is the core security gate.

---

### Pitfall 5: Existing v1.0 Data Lost During Migration

**What goes wrong:**
The app has real workout history in SQLite from v1.0 usage. A migration that only sets up new MongoDB schemas without migrating existing data loses valuable workout history. Alternatively, a migration script that runs but silently drops data (e.g., orphaned workout sets, exercises with no program) gives a false sense of success.

**Why it happens:**
Developers focus on "make the new system work" and treat data migration as an afterthought. The SQLite schema has 6 tables with foreign key relationships that need to be denormalized into MongoDB's embedded document structure -- this is a non-trivial transformation, not a simple copy.

**How to avoid:**
1. Write a dedicated migration script that reads from SQLite and writes to MongoDB with the new document structure
2. Include validation: count records before and after, verify all foreign key relationships resolved
3. Run migration on a copy of the production database first
4. Keep the SQLite file as backup until the MongoDB system is verified working

**Warning signs:**
- No migration script exists
- Migration script does record counts but does not validate embedded document integrity
- SQLite database deleted before MongoDB is verified

**Phase to address:** Phase 1 (MongoDB migration) -- migration script should be part of the same phase as schema design.

---

### Pitfall 6: Program Versioning That Breaks Workout History

**What goes wrong:**
When a user edits a program (adds/removes exercises, changes set counts), all past workouts that referenced that program now show incorrect information. The user sees "I did 5x5 squats last month" but the current program says "3x8 squats" -- the history looks wrong because it reflects the current program state, not what was actually prescribed at the time.

**Why it happens:**
The current v1.0 schema has `workout.program_id` as a foreign key to the programs table. When the program changes, old workouts still point to the same program but now see different data. In MongoDB, if workouts reference a program document by ID, editing that document retroactively changes what old workouts appear to show.

**How to avoid:**
Two viable approaches for this app:
1. **Snapshot approach (recommended for this app):** When a workout starts, snapshot the full program state (exercises, sets, weights) into the workout document. The workout is self-contained and immutable. Program edits only affect future workouts.
2. **Version counter approach:** Programs get a `version` field that increments on edit. Old versions are kept in a history collection. Workouts reference `program_id + version`. More complex but allows querying "what changed between versions."

For a gym app, the snapshot approach is simpler and more appropriate. Workout documents should contain all the data needed to display what was prescribed, without joining to the programs collection.

**Warning signs:**
- Workout documents that reference a program by ID without a version or snapshot
- Editing a program and checking old workout history -- does it still show the original prescription?
- No test covering "edit program then check old workout"

**Phase to address:** Phase 1 (MongoDB schema design) -- this must be baked into the document structure from the start, not bolted on later.

---

### Pitfall 7: Docker Networking -- Services Cannot Reach Each Other

**What goes wrong:**
The FastAPI backend cannot connect to MongoDB, or nginx cannot proxy to the backend. Common symptoms: `Connection refused`, `Name resolution failed`, or requests timing out. The app works with `docker-compose up` locally but fails when any service restarts.

**Why it happens:**
Docker Compose services communicate via internal DNS using service names, not `localhost`. Developers hardcode `localhost:27017` for MongoDB or `localhost:8000` for the backend. Additionally, nginx config may reference `127.0.0.1` instead of the Docker service name.

**How to avoid:**
- MongoDB connection string: `mongodb://mongodb:27017/gymcoach` (service name, not localhost)
- Nginx upstream: `proxy_pass http://backend:8000;` (service name, not localhost)
- Use environment variables for all service URLs, with different defaults for local dev vs Docker
- Add `depends_on` with health checks so services start in order
- Use a single Docker network for all services

```yaml
services:
  backend:
    environment:
      - MONGODB_URL=mongodb://mongodb:27017/gymcoach
    depends_on:
      mongodb:
        condition: service_healthy
  mongodb:
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
```

**Warning signs:**
- `localhost` or `127.0.0.1` appearing in any Docker-related configuration
- Services starting but immediately crashing with connection errors
- Missing `depends_on` in docker-compose.yml
- App works on first `docker-compose up` but fails after restarting a single service

**Phase to address:** Phase 3 (Docker deployment) -- but connection string abstraction should be in Phase 1 so the backend supports both local and Docker modes.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skipping PyMongo Async, using Motor | Faster start with more tutorial examples | Forced migration within 12 months when Motor EOLs | Never -- PyMongo Async API is nearly identical |
| No data access layer (queries in route handlers) | Fewer files, faster initial dev | Every new feature risks data leakage; user_id filtering scattered everywhere | Never for multi-user apps |
| Storing JWT secret in code | Quick dev setup | Secret exposed in version control | Only during initial local dev, must move to env var before deployment |
| Skipping program version snapshots | Simpler workout creation | Corrupted workout history when programs are edited | Never -- this is core data integrity |
| Single Dockerfile for frontend + backend | Simpler compose file | Cannot scale or update independently; larger image | Never -- separate containers is barely more work |
| No MongoDB indexes | Works fine with small data | Queries degrade as workout history grows | Acceptable for first week of dev, must add before deployment |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Telegram Login Widget | Using `data-auth-url` callback which does not work on localhost (Telegram requires a public domain) | Use `data-onauth` JavaScript callback during development; POST the auth data to your backend API manually. Only switch to `data-auth-url` in production |
| Telegram Login Widget | Not registering domain with @BotFather | Must use `/setdomain` command in BotFather to whitelist your domain before the widget works |
| Telegram Login Widget | Popup blocked by browser with no user feedback | Detect popup blocker state, show fallback instructions if the Telegram popup fails to open |
| MongoDB in Docker | Using `latest` tag for MongoDB image | Pin to a specific version (e.g., `mongo:7.0`) to avoid surprise breaking changes |
| MongoDB in Docker | No volume mount for data | Data is lost when container restarts. Must mount a named volume: `volumes: - mongodb_data:/data/db` |
| Nginx + Vue SPA | Nginx returns 404 for client-side routes (e.g., `/workouts/123`) | Add `try_files $uri $uri/ /index.html;` to nginx config so all routes fall through to the SPA |
| Nginx + FastAPI | Missing `proxy_set_header` directives | Must forward `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto` headers for FastAPI to generate correct URLs |
| FastAPI behind proxy | Not setting `--proxy-headers` on Uvicorn | Uvicorn ignores forwarded headers by default. Add `--proxy-headers` and `--forwarded-allow-ips='*'` (or restrict to proxy IP) |
| FastAPI behind proxy | ROOT_PATH duplication causing double-prefixed API paths (e.g., `/api/api/exercises`) | Set `root_path` in FastAPI OR in Uvicorn, not both. If nginx strips the prefix, do not set root_path |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| No index on `user_id` in MongoDB collections | Queries slow as user count or workout count grows | Create compound index `{user_id: 1, created_at: -1}` on workouts and programs collections | 1000+ workouts per user |
| Loading full workout history on dashboard | Page load time increases linearly with workout count | Paginate workout queries, use `.limit()` and `.skip()` or cursor-based pagination | 100+ workouts |
| Embedding unbounded arrays in documents | MongoDB 16MB document limit hit; large documents slow to transfer | Workouts are bounded (one session = ~20-30 sets), so embedding is fine. Programs similarly bounded. Not a real risk for this domain | 16MB doc limit (unlikely for gym data) |
| No connection pooling for MongoDB | Connection storm under concurrent requests | PyMongo AsyncMongoClient handles pooling by default (100 connections). Create ONE client instance at startup, not per-request | 50+ concurrent users |
| Serving Vue build files through FastAPI | Python serving static files is slow | Serve built Vue files through nginx directly; only proxy `/api/*` to FastAPI | Any production traffic |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Not validating `auth_date` in Telegram callback | Replay attacks -- captured auth tokens can be reused indefinitely | Reject auth data older than 5 minutes (300 seconds) for initial login verification |
| Storing bot token in frontend code or git | Anyone with the token can impersonate your bot and forge auth | Store in environment variable, add to `.gitignore`, never send to frontend. The frontend only loads the widget script with bot username (not token) |
| JWT with no expiration | Stolen tokens grant permanent access | Set 1-year expiry (per requirements), but implement a token revocation mechanism or at minimum a "sign out all devices" feature |
| No CORS restriction in production | Any website can make authenticated API calls on behalf of the user | Replace dev CORS (`localhost:5173`) with the production domain. In Docker/nginx setup, CORS may not be needed since frontend and API share the same origin |
| MongoDB without authentication | Anyone with network access to port 27017 can read/write all data | Enable MongoDB auth in Docker: create admin user, use credentials in connection string. Do not expose MongoDB port to host in production |
| Telegram user ID as sole internal identifier | Tight coupling to external identity provider | Store Telegram user ID as external reference, generate an internal user_id (ObjectId or UUID) for all data relationships |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Forcing Telegram login before showing any UI | User cannot evaluate the app before committing to auth | Show the app in read-only/demo mode, or just require login since this is a personal tool with known users |
| Login button does nothing on localhost during development | Developer cannot test auth flow locally | Provide a dev-mode bypass: when `ENVIRONMENT=dev`, auto-authenticate with a test user. Guard this with an env check so it never runs in production |
| No feedback when Telegram popup is blocked | User clicks login, nothing happens, no error shown | Detect popup blocker, show manual instructions or a direct link to the Telegram bot |
| Losing in-progress workout data during auth flow | User is mid-workout, token expires, re-auth causes page state loss | Use SPA with JWT in memory/localStorage. Token refresh should be invisible. Never force a full page reload for re-auth |
| No indication of which Telegram account is connected | User unsure if they are logged in as the right account | Show Telegram first name and photo_url in the app header after login |

## "Looks Done But Isn't" Checklist

- [ ] **MongoDB migration:** Data transferred but not validated -- verify record counts match AND embedded documents have correct nested data (e.g., program exercises actually contain their sets)
- [ ] **Telegram auth:** Login works but `auth_date` is not checked -- verify by sending a request with an old `auth_date` and confirming it is rejected
- [ ] **Multi-user isolation:** All GET endpoints filtered but POST/PUT/DELETE endpoints allow cross-user mutation -- test that User B cannot modify or delete User A's workout by ID
- [ ] **Program versioning:** Snapshots created but workout display still reads from current program -- verify by editing a program and checking that old workout history is unchanged
- [ ] **Docker deployment:** Containers start but frontend cannot reach backend -- verify full user flow (login, create program, log workout) works through nginx proxy, not just health check
- [ ] **CORS in production:** Dev CORS works but production nginx may add duplicate headers -- verify preflight OPTIONS requests succeed through the proxy
- [ ] **MongoDB indexes:** Collections exist but no indexes beyond `_id` -- run `db.collection.getIndexes()` and verify user_id compound indexes exist
- [ ] **Volume persistence:** Docker works but `docker-compose down && docker-compose up` loses all data -- verify MongoDB volume is a named volume, not anonymous
- [ ] **Exercises ownership:** Shared exercise catalog works but custom user exercises are visible to other users -- verify custom exercises are scoped to the creating user

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Used Motor instead of PyMongo Async | LOW | API is nearly identical. Replace `AsyncIOMotorClient` with `AsyncMongoClient`, update imports. Most code works unchanged |
| SQL-style schema in MongoDB | HIGH | Requires redesigning document structure, rewriting all queries, and migrating data again. Effectively starting Phase 1 over |
| Data leakage (missing user_id filter) | MEDIUM | Audit all endpoints, add data access layer, write isolation tests. Data already exposed cannot be un-exposed -- severity depends on number of users |
| Wrong Telegram hash verification | LOW | Fix the verification function, invalidate all existing sessions (force re-login) |
| Lost SQLite data during migration | LOW if backup exists, HIGH if not | Re-run migration script from SQLite backup. If no backup was kept, data is permanently lost |
| Program versioning not implemented | HIGH | Requires schema change to add snapshots to existing workout documents, backfill historical data (may be impossible if program edits already occurred and original state was not captured) |
| Docker networking issues | LOW | Fix service names in config, rebuild containers. No data loss risk |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Motor deprecation | Phase 1 (MongoDB setup) | Confirm no `motor` in dependencies; only `pymongo` with AsyncMongoClient |
| SQL-style schema mapping | Phase 1 (schema design) | Review collection count (should be 3-4, not 6+); verify programs embed exercises/sets |
| Data migration loss | Phase 1 (migration script) | Run migration, compare SQLite record counts with MongoDB document counts; spot-check 3 workouts manually |
| Program versioning | Phase 1 (schema design) | Edit a program, verify old workout history unchanged |
| Telegram hash verification | Phase 2 (auth) | Unit test with known test vectors; integration test with expired auth_date returns 401 |
| Multi-user data leakage | Phase 2 (multi-user) | Integration test: create as User A, query as User B, verify empty results on ALL endpoints |
| Docker networking | Phase 3 (deployment) | `docker-compose up` from clean state; full user flow test through nginx |
| Nginx SPA routing | Phase 3 (deployment) | Navigate directly to `/workouts/123` via browser URL bar; verify no 404 |
| MongoDB auth/security | Phase 3 (deployment) | Verify connection string includes credentials; test that unauthenticated connection is refused |

## Sources

- [PyMongo Async Migration Guide](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/) -- Motor deprecation and migration path (HIGH confidence)
- [Motor Deprecation Notice](https://www.mongodb.com/docs/drivers/motor/) -- Official EOL timeline: deprecated May 2025, EOL May 2026, final support May 2027 (HIGH confidence)
- [Telegram Login Widget](https://core.telegram.org/widgets/login) -- Official security requirements and hash verification process (HIGH confidence)
- [MongoDB Document Versioning Pattern](https://www.mongodb.com/docs/manual/data-modeling/design-patterns/data-versioning/document-versioning/) -- Official versioning guidance and anti-patterns (HIGH confidence)
- [3 Pitfalls Migrating to MongoDB](https://medium.com/mongodb/3-pitfalls-to-avoid-when-migrating-postgresql-to-mongodb-f40ef2f7cf15) -- Schema design anti-patterns when migrating from SQL (MEDIUM confidence)
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/) -- Official container guidance and proxy configuration (HIGH confidence)
- [FastAPI Proxy Headers Discussion](https://github.com/fastapi/fastapi/discussions/7541) -- ROOT_PATH duplication issues behind nginx (MEDIUM confidence)

---
*Pitfalls research for: GymCoach v1.1 MongoDB Migration and Deployment*
*Researched: 2026-03-09*