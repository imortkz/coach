"""Application configuration."""

import os

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "gymcoach")

# Dev mode: set to "true" to bypass auth on localhost. Defaults to OFF so
# a misconfigured prod container fails loudly rather than silently open.
DEV_MODE = os.environ.get("DEV_MODE", "false").lower() in ("1", "true", "yes")
DEV_USER_ID = os.environ.get("DEV_USER_ID", "dev-user-000")

# Auth — JWT_SECRET must be explicitly provided in production.
# In dev mode a stable fallback is used so tokens survive restarts.
# Outside dev mode, absence of JWT_SECRET raises at import to refuse silent insecurity.
_jwt_secret_env = os.environ.get("JWT_SECRET")
if _jwt_secret_env:
    JWT_SECRET = _jwt_secret_env
elif DEV_MODE:
    JWT_SECRET = "dev-insecure-jwt-secret"
else:
    raise RuntimeError(
        "JWT_SECRET must be set when DEV_MODE is disabled. "
        "Set the JWT_SECRET environment variable or enable DEV_MODE for local development."
    )

JWT_ALGORITHM = "HS256"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Agent service token: a static, opaque API key that authenticates an automated
# agent as the user whose telegram_id == AGENT_USER_TELEGRAM_ID (full read+write,
# same scope as that user's own session). Kept separate from JWT_SECRET so it can
# be rotated/revoked independently — clearing AGENT_API_TOKEN disables the path
# without invalidating anyone's login session. Disabled when empty.
AGENT_API_TOKEN = os.environ.get("AGENT_API_TOKEN", "")
AGENT_USER_TELEGRAM_ID = int(os.environ.get("AGENT_USER_TELEGRAM_ID", "0"))
