# S07: MongoDB Data Layer

**Goal:** Replace SQLite/SQLAlchemy with MongoDB/Beanie ODM, convert all endpoints to async, implement program versioning with embedded version snapshots.
**Demo:** All existing API endpoints work against MongoDB, program edits preserve version history, workouts reference specific program versions.

## Must-Haves
- All 15+ endpoints return correct data from MongoDB (same API contracts as v1.0)
- Program updates archive the previous version in an embedded versions array
- Workout documents capture the program_version they were logged against
- All route handlers are async def (no sync SQLAlchemy code remains)
- Beanie document models defined for 4 collections: users, exercises, programs, workouts

## Tasks
TBD — pending slice planning

## Files Likely Touched
- backend/app/database.py (replace SQLAlchemy with Beanie/MongoDB init)
- backend/app/exercises/ (models → Beanie documents, routes → async)
- backend/app/programs/ (models → Beanie documents with versioning, routes → async)
- backend/app/workouts/ (models → Beanie documents, routes → async)
- backend/pyproject.toml (swap SQLAlchemy for beanie, pymongo)
