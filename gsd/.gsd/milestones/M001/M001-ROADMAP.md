# M001: GymCoach v1.1 — MongoDB Migration & Deployment

**Vision:** Replace SQLite with MongoDB, add Telegram auth with multi-user support, program versioning, and Docker-based deployment for the GymCoach personal gym training companion.

## Success Criteria
- All application data stored in MongoDB with document-native schemas
- Users authenticate via Telegram Login Widget; data isolated per user
- Program versioning preserves history across edits; workouts reference specific versions
- Docker Compose runs nginx + FastAPI + MongoDB; app accessible in browser
- Legacy SQLite/SQLAlchemy dependencies removed; scripts repo archived

## Slices

- [x] **S01: Foundation and Schema** `risk:low` `depends:[]`
  > After this: Backend scaffolded with FastAPI + SQLAlchemy + SQLite, DB schema with migrations, exercise seed data loaded.

- [x] **S02: Exercise and Program Management** `risk:low` `depends:[S01]`
  > After this: User can create/edit/delete exercises and build programs with sets/reps/weight targets through the Vue frontend.

- [x] **S03: Workout Logging** `risk:medium` `depends:[S02]`
  > After this: User can start a workout from a program, log sets with weight/reps, use rest timer, and finish/discard workouts.

- [x] **S04: History and Progression** `risk:medium` `depends:[S03]`
  > After this: User can view workout history with charts and gets automatic weight progression suggestions based on past performance.

- [x] **S05: Analytics and Data Tools** `risk:low` `depends:[S04]`
  > After this: CLI tools produce analytics reports and can export/import data as JSON/CSV.

- [x] **S06: Integration Fixes and Polish** `risk:low` `depends:[S05]`
  > After this: Bug fixes applied, UI polish complete, v1.0 MVP shipped.

- [x] **S07: MongoDB Data Layer** `risk:high` `depends:[S06]`
  > After this: All data stored in MongoDB with Beanie ODM, all endpoints async, program versioning with embedded version snapshots.

- [x] **S08: Authentication and Multi-User** `risk:medium` `depends:[S07]`
  > After this: Users authenticate via Telegram Login Widget, JWT sessions, all data isolated per user with dev-mode auth bypass.

- [x] **S09: Docker Deployment** `risk:medium` `depends:[S08]`
  > After this: docker-compose up starts nginx + FastAPI + MongoDB, app accessible in browser, MongoDB data persists across restarts.

- [x] **S10: Cleanup** `risk:low` `depends:[S09]`
  > After this: SQLAlchemy/Alembic removed from backend, scripts repo archived, clean MongoDB-only codebase.
