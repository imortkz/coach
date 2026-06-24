"""Root conftest — sets env vars before any app module is imported at collection time.

app.config raises RuntimeError at import when DEV_MODE is off and JWT_SECRET is absent.
This file is loaded by pytest before backend/tests/conftest.py, so the env vars are
in place before the first `from app.config import ...` runs.
"""

import os

os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("JWT_SECRET", "test-secret")
