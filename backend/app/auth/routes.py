"""Auth API routes: Telegram login and current user info."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.auth.jwt import create_access_token
from app.auth.models import User
from app.auth.telegram import verify_telegram_auth
from app.config import DEV_MODE, DEV_USER_ID, TELEGRAM_BOT_TOKEN

router = APIRouter(prefix="/auth", tags=["auth"])


class TelegramLoginData(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    first_name: str
    username: str | None = None


class UserRead(BaseModel):
    id: str
    telegram_id: int
    username: str | None = None
    first_name: str
    last_name: str | None = None
    photo_url: str | None = None


@router.post("/telegram", response_model=TokenResponse)
async def telegram_login(data: TelegramLoginData) -> TokenResponse:
    """Verify Telegram login data and issue a JWT."""
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot token not configured",
        )

    # Verify HMAC signature
    data_dict: dict[str, Any] = {
        "id": data.id,
        "first_name": data.first_name,
        "auth_date": data.auth_date,
        "hash": data.hash,
    }
    if data.last_name:
        data_dict["last_name"] = data.last_name
    if data.username:
        data_dict["username"] = data.username
    if data.photo_url:
        data_dict["photo_url"] = data.photo_url

    if not verify_telegram_auth(data_dict, TELEGRAM_BOT_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data",
        )

    # Auto-create or update user
    user = await User.find_one({"telegram_id": data.id})
    if user is None:
        user = User(
            telegram_id=data.id,
            first_name=data.first_name,
            last_name=data.last_name,
            username=data.username,
            photo_url=data.photo_url,
        )
        await user.insert()
    else:
        user.first_name = data.first_name
        user.last_name = data.last_name
        user.username = data.username
        user.photo_url = data.photo_url
        user.last_login = datetime.now(timezone.utc)
        await user.save()

    token = create_access_token(user.id, user.telegram_id)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        first_name=user.first_name,
        username=user.username,
    )


@router.post("/dev-login", response_model=TokenResponse)
async def dev_login() -> TokenResponse:
    """Dev-mode auto-login endpoint. Only available when DEV_MODE=true."""
    if not DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    user = await User.find_one(User.id == DEV_USER_ID)
    if not user:
        user = User(
            id=DEV_USER_ID,
            telegram_id=0,
            username="dev",
            first_name="Dev",
            last_name="User",
        )
        await user.insert()

    token = create_access_token(user.id, user.telegram_id)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        first_name=user.first_name,
        username=user.username,
    )



