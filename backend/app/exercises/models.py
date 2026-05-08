"""Exercise Beanie document model."""

import uuid

from beanie import Document
from pydantic import Field


class Exercise(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str | None = None  # None = shared/seeded exercise
    name: str
    muscle_group: str
    equipment: str
    is_custom: bool = Field(default=False)
    name_ru: str | None = None
    gif_url: str | None = None

    class Settings:
        name = "exercises"
        indexes = [
            "user_id",
        ]
