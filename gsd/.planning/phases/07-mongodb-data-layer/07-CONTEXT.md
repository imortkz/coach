# Phase 7: MongoDB Data Layer - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace SQLite/SQLAlchemy with MongoDB/Beanie ODM, convert all backend endpoints from sync to async, implement program versioning with embedded version snapshots, and update the frontend to work with the new API shape. All application data stored in MongoDB with document-native schemas. Clean start — no data migration from SQLite.

</domain>

<decisions>
## Implementation Decisions

### Frontend adaptation
- Frontend updated in this phase alongside the backend (not deferred)
- Only the API service layer and TypeScript types are updated — Vue components stay as-is
- TypeScript types manually maintained (no auto-generation from OpenAPI)
- Claude's Discretion: whether to update existing frontend tests or rely on manual verification

### Program version visibility
- Version badge on workout card (small "v3" next to program name in workout history)
- Clicking the version badge shows the program configuration at that version
- Versions only accessible through workout history — no dedicated version history page
- Every program edit creates a new version (simple rule, no structural-change detection)
- In-progress workouts keep their snapshot — program edits don't affect active workouts

### Settings storage
- Settings embedded in user document (prepares for Phase 8 multi-user)
- Phase 7 uses a single "default" user document to hold settings (Phase 8 replaces with real Telegram users)
- Only migrate rest_timer_disabled — no new settings, no extensibility planning
- Settings API endpoint stays the same (/api/settings), backend reads from default user doc

### API contract changes
- Resource IDs use native MongoDB ObjectId strings (24-char hex)
- MongoDB _id serialized as "id" in JSON responses (Pydantic alias, standard REST convention)
- API response shape embraces the embedded document model (programs include exercises/sets inline)
- REST timer endpoint (/api/settings) keeps same contract — backend source changes, frontend URL unchanged

### Claude's Discretion
- Test strategy for frontend (update existing tests vs manual verification)
- Exact Pydantic response model structure for embedded documents
- MongoDB index design
- Error handling patterns for async endpoints
- Connection pooling and Beanie initialization approach

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Research already established:
- Beanie 2.0 ODM (PyMongo Async internally)
- 4 collections: users, exercises, programs, workouts
- Exercises/sets embedded in program documents
- Self-contained workout documents (denormalized at write time)
- Program versioning via embedded versions array in program documents

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- Backend module structure (app/exercises, app/programs, app/workouts): Same module layout can be preserved, replacing SQLAlchemy models with Beanie documents
- Pydantic schemas (schemas.py in each module): Can be adapted for MongoDB response shapes
- Frontend API service layer: Single point of change for all backend calls

### Established Patterns
- FastAPI router pattern with prefix/tags: Preserved as-is, just switch to async def
- Dependency injection (get_db): Replaced with Beanie's built-in document methods (no session dependency needed)
- Eager loading with selectinload: No longer needed — embedded documents returned directly
- Full-replace update pattern (delete all children, recreate): Replaced by version snapshot + new current state

### Integration Points
- app/database.py: Complete rewrite — MongoDB connection via Beanie init instead of SQLAlchemy engine
- app/main.py: Add Beanie initialization on startup event, update CORS for production
- Frontend API calls: All fetch/axios calls update to handle string IDs and embedded response shapes
- Frontend TypeScript types: Update interfaces to match new document-based responses (string id, embedded exercises)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-mongodb-data-layer*
*Context gathered: 2026-03-09*
