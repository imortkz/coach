"""Application configuration."""

import os
import secrets

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "gymcoach")

# Auth
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Dev mode: set to "true" to bypass auth on localhost
DEV_MODE = os.environ.get("DEV_MODE", "true").lower() in ("1", "true", "yes")
DEV_USER_ID = os.environ.get("DEV_USER_ID", "dev-user-000")

# Agent service token: a static, opaque API key that authenticates an automated
# agent as the user whose telegram_id == AGENT_USER_TELEGRAM_ID (full read+write,
# same scope as that user's own session). Kept separate from JWT_SECRET so it can
# be rotated/revoked independently — clearing AGENT_API_TOKEN disables the path
# without invalidating anyone's login session. Disabled when empty.
AGENT_API_TOKEN = os.environ.get("AGENT_API_TOKEN", "")
AGENT_USER_TELEGRAM_ID = int(os.environ.get("AGENT_USER_TELEGRAM_ID", "0"))
