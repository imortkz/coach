"""Pydantic schemas for programs."""

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.exercises.schemas import ExerciseRead


# --- Read schemas (flattened for frontend compatibility) ---


class ProgramSetRead(BaseModel):
    set_number: int
    target_reps: int
    target_weight_kg: float | None
    is_warmup: bool


class ProgramExerciseRead(BaseModel):
    exercise_id: str
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
    order: int
    sets: list[ProgramSetCreate] = []


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
