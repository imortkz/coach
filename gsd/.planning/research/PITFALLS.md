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
