"""FastAPI dependencies for authentication."""

import hmac

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.auth.jwt import decode_access_token
from app.auth.models import User
from app.config import (
    AGENT_API_TOKEN,
    AGENT_USER_TELEGRAM_ID,
    DEV_MODE,
    DEV_USER_ID,
)

security = HTTPBearer(auto_error=False)

DEV_USER_TELEGRAM_ID = 0


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """Extract and validate the current user from JWT Bearer token.

    In DEV_MODE (localhost), if no token is provided, returns or creates
    a dev user automatically so you can use the API without Telegram auth.
    """
    # --- Dev mode bypass ---
    if DEV_MODE and (credentials is None):
        return await _get_or_create_dev_user()

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- Agent service token ---
    # A static opaque key (not a JWT) that authenticates an automated agent as
    # the configured user. Checked before JWT decode since it is not a JWT.
    # Constant-time compare; only active when AGENT_API_TOKEN is configured.
    if AGENT_API_TOKEN and hmac.compare_digest(
        credentials.credentials, AGENT_API_TOKEN
    ):
        agent_user = await User.find_one(
            User.telegram_id == AGENT_USER_TELEGRAM_ID
        )
        if not agent_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent user not found",
            )
        return agent_user

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            raise JWTError("Missing sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def _get_or_create_dev_user() -> User:
    """Get or create a dev user for local development without Telegram."""
    user = await User.find_one(User.id == DEV_USER_ID)
    if not user:
        user = User(
            id=DEV_USER_ID,
            telegram_id=DEV_USER_TELEGRAM_ID,
            username="dev",
            first_name="Dev",
            last_name="User",
        )
        await user.insert()
    return user
