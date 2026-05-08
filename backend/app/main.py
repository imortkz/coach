"""GymCoach API - FastAPI application with MongoDB/Beanie."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.routes import UserRead, router as auth_router
from app.database import close_db, init_db
from app.exercises.routes import router as exercises_router
from app.programs.routes import router as programs_router
from app.workouts.routes import router as workouts_router
from app.workouts.routes import settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: init and close MongoDB."""
    await init_db()
    await _startup_tasks()
    yield
    await close_db()


async def _startup_tasks() -> None:
    """Run once at startup: seed exercises and create compound indexes."""
    from app.database import client
    from app.seed import seed_exercises
    from app.config import MONGODB_DB_NAME

    # Seed exercise library via upsert (idempotent)
    seeded = await seed_exercises()
    if seeded:
        import logging
        logging.getLogger("gymcoach").info(f"Upserted {seeded} seed exercises into exercises collection")

    # Compound indexes for query performance (idempotent)
    if client:
        db = client[MONGODB_DB_NAME]
        await db["workouts"].create_index(
            [("user_id", 1), ("completed_at", -1)], name="workouts_user_completed"
        )
        await db["settings"].create_index(
            [("user_id", 1), ("key", 1)], unique=True, name="settings_user_key"
        )


app = FastAPI(title="GymCoach API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public auth routes (login, dev-login)
app.include_router(auth_router, prefix="/api")

# Protected routes
app.include_router(exercises_router, prefix="/api")
app.include_router(programs_router, prefix="/api")
app.include_router(workouts_router, prefix="/api")
app.include_router(settings_router, prefix="/api")


@app.get("/api/auth/me", response_model=UserRead, tags=["auth"])
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Get currently authenticated user info."""
    return UserRead(
        id=current_user.id,
        telegram_id=current_user.telegram_id,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        photo_url=current_user.photo_url,
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint with database connectivity verification."""
    try:
        from app.database import client
        if client:
            await client.admin.command("ping")
            return {"status": "ok", "database": "connected"}
        return {"status": "ok", "database": "disconnected"}
    except Exception:
        return {"status": "ok", "database": "disconnected"}
