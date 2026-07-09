"""Pydantic schemas for workouts."""

from datetime import datetime

from pydantic import BaseModel

from app.exercises.schemas import ExerciseRead


# --- Set schemas ---


class WorkoutSetCreate(BaseModel):
    exercise_id: str
    set_number: int
    weight_kg: float | None = None
    reps: int | None = None
    is_warmup: bool = False


class WorkoutSetUpdate(BaseModel):
    weight_kg: float | None = None
    reps: int | None = None


class WorkoutSetRead(BaseModel):
    id: str
    workout_id: str
    exercise_id: str
    set_number: int
    weight_kg: float | None
    reps: int | None
    is_warmup: bool
    exercise: ExerciseRead | None = None


# --- Workout schemas ---


class WorkoutCreate(BaseModel):
    program_id: str


class WorkoutRead(BaseModel):
    id: str
    program_id: str | None
    program_version: int | None
    started_at: datetime
    completed_at: datetime | None
    sets: list[WorkoutSetRead] = []


class PreFillSet(BaseModel):
    set_number: int
    weight_kg: float | None
    reps: int | None
    is_warmup: bool


class SuggestionInfo(BaseModel):
    type: str  # "weight" | "reps" | "keep"
    suggested_weight_kg: float | None = None
    suggested_reps: int | None = None
    increment: float | None = None
    reason: str  # "hit_target" | "missed_reps"


class WorkoutStartResponse(BaseModel):
    id: str
    program_id: str | None
    started_at: datetime
    completed_at: datetime | None
    sets: list[WorkoutSetRead] = []
    pre_fill: dict[str, list[PreFillSet]] = {}
    suggestions: dict[str, SuggestionInfo] = {}


class WorkoutActiveResponse(BaseModel):
    """Active (in-progress) workout plus the history context the UI needs.

    Mirrors WorkoutStartResponse but carries the already-logged sets. Returning
    pre_fill + suggestions here (not only on POST /workouts) is what keeps the
    "last time" reference and progression suggestion alive across a page reload.
    """
    id: str
    program_id: str | None
    started_at: datetime
    completed_at: datetime | None
    sets: list[WorkoutSetRead] = []
    pre_fill: dict[str, list[PreFillSet]] = {}
    suggestions: dict[str, SuggestionInfo] = {}


class WorkoutListResponse(BaseModel):
    items: list[WorkoutRead]


class ExerciseSessionSet(BaseModel):
    set_number: int
    weight_kg: float | None
    reps: int | None
    is_warmup: bool


class ExerciseSession(BaseModel):
    date: datetime
    sets: list[ExerciseSessionSet]
    best_weight: float | None
    total_volume: float


class ExerciseHistoryResponse(BaseModel):
    sessions: list[ExerciseSession]
    suggestion: SuggestionInfo | None = None


# --- Settings schemas ---


class SettingRead(BaseModel):
    key: str
    value: str


class SettingUpdate(BaseModel):
    value: str


# --- Report schemas (M005) ---


class ReportVolumeEntry(BaseModel):
    week: str
    muscle_group: str
    volume_kg: float


class ReportFrequencyEntry(BaseModel):
    week: str
    count: int


class ReportPersonalRecord(BaseModel):
    exercise_name: str
    exercise_name_ru: str | None = None
    best_weight_in_period: float
    previous_best: float | None
    is_new_pr: bool


class ReportResponse(BaseModel):
    weeks: list[str]
    volume_by_week: list[ReportVolumeEntry]
    frequency_by_week: list[ReportFrequencyEntry]
    personal_records: list[ReportPersonalRecord]
