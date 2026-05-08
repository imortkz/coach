"""JWT creation and verification utilities."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import JWT_ALGORITHM, JWT_SECRET

TOKEN_EXPIRY_DAYS = 365


def create_access_token(user_id: str, telegram_id: int) -> str:
    """Create a JWT token valid for 1 year."""
    expire = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)
    payload = {
        "sub": user_id,
        "tg": telegram_id,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
