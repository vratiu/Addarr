#!/usr/bin/env python3

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl
from typing import Tuple, Dict, Any, Optional

import firebase_admin
from firebase_admin import auth

# Initialize firebase admin if not already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app()


def verify_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Verify Telegram WebApp initData HMAC-SHA256 signature.
    Returns (is_valid, user_dict).
    """
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        if "hash" not in parsed:
            return False, None

        received_hash = parsed.pop("hash")

        # Check auth_date for expiration
        auth_date = int(parsed.get("auth_date", 0))
        if time.time() - auth_date > max_age_seconds:
            return False, None

        # Build data-check-string (keys sorted alphabetically)
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed.items())]
        data_check_string = "\n".join(data_check_arr)

        # secret_key = HMAC_SHA256("WebAppData", bot_token)
        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()

        # calculated_hash = HMAC_SHA256(secret_key, data_check_string)
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if hmac.compare_digest(calculated_hash, received_hash):
            user_data = json.loads(parsed.get("user", "{}"))
            return True, user_data

        return False, None

    except Exception:
        return False, None


def create_token_for_telegram_user(user_id: int, username: Optional[str] = None) -> str:
    """Issue a Firebase custom auth token for the authenticated Telegram user ID."""
    uid = str(user_id)
    claims = {"username": username} if username else {}
    custom_token = auth.create_custom_token(uid, claims)
    return custom_token.decode("utf-8") if isinstance(custom_token, bytes) else custom_token


def handler(request_body: Dict[str, Any], bot_token: str) -> Dict[str, Any]:
    """Cloud Function handler for POST /auth/telegram."""
    init_data = request_body.get("initData")
    if not init_data:
        return {"statusCode": 400, "error": "Missing initData"}

    is_valid, user = verify_telegram_init_data(init_data, bot_token)
    if not is_valid or not user or "id" not in user:
        return {"statusCode": 401, "error": "Invalid Telegram signature"}

    token = create_token_for_telegram_user(user["id"], user.get("username"))
    return {
        "statusCode": 200,
        "token": token,
        "user": user
    }
