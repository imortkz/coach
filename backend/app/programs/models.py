"""Program Beanie document model — versioned rows (current = max version)."""

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


class Program(Document):
    """A single VERSIONED ROW of a program.

    Each edit inserts a new row instead of mutating in place:
      - ``id`` (Mongo ``_id``) is unique per row.
      - ``program_id`` is the LINEAGE id, shared by every version of the same
        program. ``Workout.program_id`` pins this lineage id.
      - ``version`` increases monotonically within a lineage.

    "Current program" = the row with max(version) for a (user_id, program_id).
    Historical templates are resolved by a workout's pinned ``program_version``.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    program_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    user_id: str
    name: str
    rest_timer_disabled: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    exercises: list[ProgramExercise] = []

    class Settings:
        name = "programs"
        indexes = [
            # Unique compound index covering lineage resolution, per-user
            # listing, AND concurrency: a racing double-edit that computes the
            # same next version raises a clean DuplicateKeyError instead of
            # silently creating two rows at the same version.
            IndexModel(
                [("user_id", ASCENDING), ("program_id", ASCENDING), ("version", DESCENDING)],
                unique=True,
                name="uniq_user_program_version",
            ),
        ]
