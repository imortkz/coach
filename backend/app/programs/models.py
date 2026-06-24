"""Program Beanie document model with embedded exercises and versioning."""

import uuid
from datetime import datetime, timezone

from beanie import Document
from pydantic import BaseModel, Field


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

    class Settings:
        name = "programs"
        indexes = [
            "user_id",
        ]
