"""Pydantic schemas for exercises."""

from pydantic import BaseModel


class ExerciseRead(BaseModel):
    id: str
    name: str
    muscle_group: str
    equipment: str
    is_custom: bool
    name_ru: str | None = None
    gif_url: str | None = None


class ExerciseCreate(BaseModel):
    name: str
    muscle_group: str
    equipment: str


class ExerciseUpdate(BaseModel):
    name: str | None = None
    muscle_group: str | None = None
    equipment: str | None = None
