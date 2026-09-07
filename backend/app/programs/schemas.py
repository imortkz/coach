"""Pydantic schemas for programs."""

from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from app.exercises.schemas import ExerciseRead


# --- Read schemas (flattened for frontend compatibility) ---


class ProgramSetRead(BaseModel):
    set_number: int
    target_reps: int
    target_weight_kg: float | None
    is_warmup: bool


class ProgramExerciseRead(BaseModel):
    exercise_id: str
    superset_group: str | None = None
    order: int
    sets: list[ProgramSetRead] = []
    exercise: ExerciseRead | None = None


class ProgramRead(BaseModel):
    id: str
    name: str
    created_at: datetime
    rest_timer_disabled: bool = False
    current_version: int = 1
    exercises: list[ProgramExerciseRead] = []


class ProgramVersionRead(BaseModel):
    """Read-only snapshot of a program as it looked at a given version."""
    version: int
    is_current: bool
    name: str
    rest_timer_disabled: bool = False
    exercises: list[ProgramExerciseRead] = []


# --- Create / Update schemas ---


class ProgramSetCreate(BaseModel):
    set_number: int
    target_reps: int
    target_weight_kg: float | None = None
    is_warmup: bool = False


class ProgramExerciseCreate(BaseModel):
    exercise_id: str
    superset_group: str | None = None
    order: int
    sets: list[ProgramSetCreate] = []


def check_superset_set_counts(exercises: list[ProgramExerciseCreate]) -> None:
    """Require every member of a superset to have the same set count."""
    counts_by_group: dict[str, set[int]] = {}
    for exercise in exercises:
        if exercise.superset_group is None:
            continue
        counts_by_group.setdefault(exercise.superset_group, set()).add(len(exercise.sets))
    if any(len(counts) > 1 for counts in counts_by_group.values()):
        raise ValueError("All exercises in a superset must have the same number of sets")


class ProgramCreate(BaseModel):
    name: str
    rest_timer_disabled: bool = False
    exercises: list[ProgramExerciseCreate] = []

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Program name must not be empty")
        return v

    @model_validator(mode="after")
    def superset_set_counts_must_match(self) -> "ProgramCreate":
        check_superset_set_counts(self.exercises)
        return self


class ProgramUpdate(BaseModel):
    name: str
    rest_timer_disabled: bool = False
    exercises: list[ProgramExerciseCreate] = []

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Program name must not be empty")
        return v

    @model_validator(mode="after")
    def superset_set_counts_must_match(self) -> "ProgramUpdate":
        check_superset_set_counts(self.exercises)
        return self
