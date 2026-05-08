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
