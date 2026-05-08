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
