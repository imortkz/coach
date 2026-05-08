"""User Beanie document model."""

import uuid
from datetime import datetime, timezone

from beanie import Document
from pydantic import Field


class User(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    telegram_id: int
    username: str | None = None
    first_name: str = ""
    last_name: str | None = None
    photo_url: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            "telegram_id",
        ]
