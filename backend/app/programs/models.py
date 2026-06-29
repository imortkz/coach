"""Program Beanie document model with embedded exercises and versioning."""

import uuid
from datetime import datetime, timezone

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel


class ProgramSet(BaseModel):
    """Embedded set target within a program exercise."""
    set_number: int
    target_reps: int
    target_weight_kg: float | None = None
    is_warmup: bool = False


class ProgramExercise(BaseModel):
    """Embedded exercise within a program."""
    exercise_id: str
    exercise_name: str = ""
    exercise_muscle_group: str = ""
    exercise_equipment: str = ""
    order: int
    sets: list[ProgramSet] = []


class ProgramVersion(BaseModel):
    """Snapshot of a previous program version."""
    version: int
    name: str
    rest_timer_disabled: bool = False
    exercises: list[ProgramExercise] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Program(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    rest_timer_disabled: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_version: int = 1
    exercises: list[ProgramExercise] = []
    versions: list[ProgramVersion] = []

    # --- Versioned-rows groundwork (expand phase, PR-A1) ---
    # Additive only: lineage id + per-row version, NOT yet used by routes and
    # deliberately NON-UNIQUE here. The unique constraint is added in a later
    # PR once every legacy row is backfilled — declaring it unique now would
    # rebuild the index against rows missing these fields (all -> null) and
    # crash init_beanie with DuplicateKeyError (this is exactly what took prod
    # down in #48). See backfill_program_lineage().
    program_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1

    class Settings:
        name = "programs"
        indexes = [
            "user_id",
            IndexModel(
                [("user_id", ASCENDING), ("program_id", ASCENDING), ("version", DESCENDING)],
                name="user_program_version",
            ),
        ]
