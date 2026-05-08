"""Telegram Login Widget HMAC-SHA-256 verification."""

import hashlib
import hmac
from typing import Any


def verify_telegram_auth(data: dict[str, Any], bot_token: str) -> bool:
    """Verify Telegram login data using HMAC-SHA-256.

    Per Telegram docs: hash = HMAC-SHA-256(data_check_string, SHA-256(bot_token))
    where data_check_string is sorted key=value pairs joined by newlines (excluding 'hash').
    """
    received_hash = data.get("hash")
    if not received_hash:
        return False

    # Build the data check string (sorted, excluding hash)
    check_items = sorted(
        f"{k}={v}" for k, v in data.items() if k != "hash"
    )
    data_check_string = "\n".join(check_items)

    # Secret key = SHA-256 of bot token
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # Compute expected hash
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_hash, received_hash)
