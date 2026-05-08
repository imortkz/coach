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
