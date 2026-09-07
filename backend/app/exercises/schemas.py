"""Pydantic schemas for exercises."""

from pydantic import BaseModel


class ExerciseRead(BaseModel):
    id: str
    name: str
    muscle_group: str
    equipment: str
    is_custom: bool
    is_assisted: bool = False
    name_ru: str | None = None
    gif_url: str | None = None


class ExerciseCreate(BaseModel):
    name: str
    muscle_group: str
    equipment: str
    is_assisted: bool = False


class ExerciseUpdate(BaseModel):
    name: str | None = None
    muscle_group: str | None = None
    equipment: str | None = None
    is_assisted: bool | None = None
