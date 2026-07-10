"""Workout and Setting Beanie document models."""

import uuid
from datetime import datetime, timezone

from beanie import Document
from pydantic import BaseModel, Field


class WorkoutSet(BaseModel):
    """Embedded set within a workout."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exercise_id: str
    exercise_name: str = ""
    exercise_muscle_group: str = ""
    exercise_equipment: str = ""
    exercise_is_custom: bool = False
    set_number: int
    weight_kg: float | None = None
    reps: int | None = None
    is_warmup: bool = False
    logged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rpe: int | None = None


class Workout(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    program_id: str | None = None
    program_version: int | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    sets: list[WorkoutSet] = []

    class Settings:
        name = "workouts"
        indexes = [
            "user_id",
        ]


class Setting(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    key: str
    value: str

    class Settings:
        name = "settings"
        indexes = [
            [("user_id", 1), ("key", 1)],
        ]
