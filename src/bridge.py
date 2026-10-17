#!/usr/bin/env python3

import os
import re
import hmac
import hashlib
import json
import time
import logging
import asyncio
from urllib.parse import parse_qsl
from typing import Dict, Any, Optional, Tuple

import logger
from config import config
from definitions import ROOT_DIR, ADMIN_PATH, ALLOWLIST_PATH, CHATID_PATH
import radarr
import sonarr

# Set up logging
logLevel = logging.DEBUG if config.get("debugLogging", False) else logging.INFO
logger = logger.getLogger("addarr.bridge", logLevel, config.get("logToConsole", False))

_app = None
_listener = None

# Per-user sliding window rate limiter: user_id -> list of request timestamps
_rate_limit_buckets: Dict[str, list] = {}
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 30
MAX_REQUEST_AGE_MS = 5 * 60 * 1000  # 5 minutes
_SAFE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_APIKEY_SCRUB_RE = re.compile(r"(apikey=)[^&\s\"']+", re.IGNORECASE)


def _is_safe_rtdb_key(key: str) -> bool:
    """Ensure RTDB path keys cannot traverse paths or exceed length limits."""
    return bool(key and isinstance(key, str) and _SAFE_KEY_RE.match(key))


def _check_rate_limit(user_id: str) -> bool:
    """Return True if user_id is within rate limits, False if throttled."""
    now = time.time()
    bucket = _rate_limit_buckets.get(user_id, [])
    bucket = [ts for ts in bucket if now - ts < RATE_LIMIT_WINDOW_SECONDS]
    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        _rate_limit_buckets[user_id] = bucket
        return False
    bucket.append(now)
    _rate_limit_buckets[user_id] = bucket
    return True


def verify_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 86400
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Cryptographically verify Telegram WebApp initData HMAC-SHA256 signature.
    Returns (is_valid, user_dict).
    """
    if not init_data or not bot_token or not isinstance(init_data, str) or len(init_data) > 4096:
        return False, None

    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        if "hash" not in parsed:
            return False, None

        received_hash = parsed.pop("hash")

        auth_date = int(parsed.get("auth_date", 0))
        now = time.time()
        # Reject missing/expired timestamps or timestamps in the future (>60s clock skew)
        if auth_date <= 0 or (now - auth_date > max_age_seconds) or (auth_date > now + 60):
            return False, None

        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed.items())]
        data_check_string = "\n".join(data_check_arr)

        secret_key = hmac.new(b"WebAppData", str(bot_token).encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if hmac.compare_digest(calculated_hash, received_hash):
            user_data = json.loads(parsed.get("user", "{}"))
            if isinstance(user_data, dict) and "id" in user_data:
                return True, user_data

        return False, None
    except Exception:
        return False, None


def is_user_authorized(telegram_uid: str, username: Optional[str] = None, check_admin: bool = False) -> bool:
    """
    Validate user authorization against allowlist, admin, and chatid files.
    Fails closed (returns False) if no authorization source has granted access.
    """
    telegram_uid_str = str(telegram_uid).strip() if telegram_uid is not None else ""
    if not telegram_uid_str or telegram_uid_str == "None":
        return False

    username_str = str(username).strip() if username and str(username).strip() != "None" else ""
    explicitly_authorized = False

    # 1. Check allowlist if enabled
    if config.get("enableAllowlist", False):
        if not os.path.exists(ALLOWLIST_PATH):
            return False
        with open(ALLOWLIST_PATH, "r", encoding="utf8") as f:
            allowed = False
            for line in f:
                cid = line.strip().split(" - ")[0].strip()
                if cid and (cid == telegram_uid_str or (username_str and cid == username_str)):
                    allowed = True
                    break
            if not allowed:
                return False
            explicitly_authorized = True

    # 2. Check admin if required for this action
    if check_admin:
        if not os.path.exists(ADMIN_PATH):
            return False
        with open(ADMIN_PATH, "r", encoding="utf8") as f:
            is_admin = False
            for line in f:
                cid = line.strip().split(" - ")[0].strip()
                if cid and (cid == telegram_uid_str or (username_str and cid == username_str)):
                    is_admin = True
                    break
            if not is_admin:
                return False
            explicitly_authorized = True

    # 3. Check authenticated chats in chatid.txt
    if os.path.exists(CHATID_PATH):
        with open(CHATID_PATH, "r", encoding="utf8") as f:
            lines = [l.strip().split(" - ")[0].strip() for l in f if l.strip()]
            if lines:
                if telegram_uid_str not in lines:
                    return False
                explicitly_authorized = True

    return explicitly_authorized


def _requires_admin(action: str) -> bool:
    """Return True if the requested action requires admin privileges under current config."""
    if action == "delete_movie":
        return bool(config.get("enableAdmin", False) or config.get("radarr", {}).get("adminRestrictions", False))
    if action == "delete_series":
        return bool(config.get("enableAdmin", False) or config.get("sonarr", {}).get("adminRestrictions", False))
    if action in ("update_movie", "get_library_movies"):
        return bool(config.get("radarr", {}).get("adminRestrictions", False))
    if action in ("update_series", "get_library_series"):
        return bool(config.get("sonarr", {}).get("adminRestrictions", False))
    return False


def _get_filtered_root_folders(service_module, service_cfg: Dict[str, Any]) -> list:
    """Return root folders excluding any configured in excludedRootFolders."""
    folders = service_module.getRootFolders() or []
    excluded = [f for f in (service_cfg.get("excludedRootFolders") or []) if f]
    return [f for f in folders if isinstance(f, dict) and f.get("path") not in excluded]


def _get_filtered_quality_profiles(service_module, service_cfg: Dict[str, Any]) -> list:
    """Return quality profiles excluding any configured in excludedQualityProfiles."""
    profiles = service_module.getQualityProfiles() or []
    excluded = [p for p in (service_cfg.get("excludedQualityProfiles") or []) if p]
    return [p for p in profiles if isinstance(p, dict) and p.get("name") not in excluded]


def _validate_root_folder_path(path: Any, service_cfg: Dict[str, Any]) -> str:
    """Validate that a root folder path is a safe string and not excluded."""
    if not path or not isinstance(path, str):
        raise ValueError("Invalid root folder path")
    norm_path = path.strip()
    if not norm_path or ".." in norm_path.split("/") or ".." in norm_path.split("\\"):
        raise ValueError("Invalid root folder path")
    excluded = [f for f in (service_cfg.get("excludedRootFolders") or []) if f]
    if norm_path in excluded or norm_path.rstrip("/") in [str(x).rstrip("/") for x in excluded]:
        raise ValueError("Selected root folder is restricted")
    return norm_path


def _resolve_tags(service_module, service_cfg: Dict[str, Any], user_id: Optional[str] = None, raw_tags=None) -> list:
    """Resolve tag labels or requester ID into integer tag IDs required by Radarr/Sonarr."""
    if isinstance(raw_tags, list) and raw_tags and all(isinstance(t, int) for t in raw_tags):
        return raw_tags

    tags = []
    try:
        existing_tags = service_module.getTags() or []
        if service_cfg.get("addRequesterIdTag") and user_id:
            if str(user_id) not in [str(t.get("label")) for t in existing_tags]:
                service_module.createTag(str(user_id))
                existing_tags = service_module.getTags() or []
            for t in existing_tags:
                if str(t.get("label")) == str(user_id):
                    tags.append(int(t["id"]))
        if not tags:
            label_list = raw_tags if raw_tags is not None else service_cfg.get("defaultTags", [])
            if label_list:
                tags = [int(t["id"]) for t in existing_tags if t.get("label") in label_list]
    except Exception as e:
        logger.warning(f"Could not resolve tags, defaulting to []: {_APIKEY_SCRUB_RE.sub(r'\1***', str(e))}")
    return tags


def dispatch_action(action: str, payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute action against local Sonarr/Radarr APIs and return data."""
    if not isinstance(payload, dict):
        payload = {}

    try:
        if action == "search_movie":
            term = str(payload.get("term", "")).strip()
            if not term or len(term) > 256:
                return {"success": True, "results": []}
            raw = radarr.search(term)
            if raw:
                return {"success": True, "results": radarr.giveTitles(raw)}
            return {"success": True, "results": []}

        elif action == "search_series":
            term = str(payload.get("term", "")).strip()
            if not term or len(term) > 256:
                return {"success": True, "results": []}
            raw = sonarr.search(term)
            if raw:
                return {"success": True, "results": sonarr.giveTitles(raw)}
            return {"success": True, "results": []}

        elif action == "add_movie":
            radarr_cfg = config.get("radarr", {})
            tmdb_id = int(payload["tmdbId"])
            path = _validate_root_folder_path(payload.get("path"), radarr_cfg)
            quality_profile_id = int(payload["qualityProfileId"])
            tags = _resolve_tags(radarr, radarr_cfg, user_id=user_id, raw_tags=payload.get("tags"))
            success = radarr.addToLibrary(tmdb_id, path, quality_profile_id, tags)
            return {"success": bool(success)}

        elif action == "add_series":
            sonarr_cfg = config.get("sonarr", {})
            tvdb_id = int(payload["tvdbId"])
            path = _validate_root_folder_path(payload.get("path"), sonarr_cfg)
            quality_profile_id = int(payload["qualityProfileId"])
            tags = _resolve_tags(sonarr, sonarr_cfg, user_id=user_id, raw_tags=payload.get("tags"))
            seasons_selected = payload.get("seasonsSelected")
            if seasons_selected is None:
                # default to all seasons monitored
                seasons_selected = sonarr.getSeasons(tvdb_id)
            success = sonarr.addToLibrary(tvdb_id, path, quality_profile_id, tags, seasons_selected)
            return {"success": bool(success)}

        elif action == "get_library_movies":
            items = radarr.get_library_summary()
            return {"success": items is not False, "items": items or []}

        elif action == "get_library_series":
            items = sonarr.get_library_summary()
            return {"success": items is not False, "items": items or []}

        elif action == "update_movie":
            movie_id = int(payload["movieId"])
            profile_id = int(payload["qualityProfileId"]) if payload.get("qualityProfileId") is not None else None
            monitored = payload.get("monitored")
            result = radarr.update_movie(movie_id, quality_profile_id=profile_id, monitored=monitored)
            return {"success": bool(result), "data": result}

        elif action == "update_series":
            series_id = int(payload["seriesId"])
            profile_id = int(payload["qualityProfileId"]) if payload.get("qualityProfileId") is not None else None
            monitored = payload.get("monitored")
            seasons = payload.get("seasons")
            result = sonarr.update_series(series_id, quality_profile_id=profile_id, monitored=monitored, seasons=seasons)
            return {"success": bool(result), "data": result}

        elif action == "delete_movie":
            tmdb_id = int(payload["tmdbId"])
            result = radarr.removeFromLibrary(tmdb_id)
            return {"success": bool(result)}

        elif action == "delete_series":
            tvdb_id = int(payload["tvdbId"])
            result = sonarr.removeFromLibrary(tvdb_id)
            return {"success": bool(result)}

        elif action == "get_config_options":
            radarr_cfg = config.get("radarr", {})
            sonarr_cfg = config.get("sonarr", {})
            return {
                "success": True,
                "radarr": {
                    "qualityProfiles": _get_filtered_quality_profiles(radarr, radarr_cfg),
                    "rootFolders": _get_filtered_root_folders(radarr, radarr_cfg),
                },
                "sonarr": {
                    "qualityProfiles": _get_filtered_quality_profiles(sonarr, sonarr_cfg),
                    "rootFolders": _get_filtered_root_folders(sonarr, sonarr_cfg),
                }
            }

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    except (ValueError, KeyError, TypeError) as e:
        safe_msg = _APIKEY_SCRUB_RE.sub(r"\1***", str(e))
        logger.warning(f"Invalid parameters for action '{action}': {safe_msg}")
        return {"success": False, "error": f"Invalid request parameters: {safe_msg}"}
    except Exception as e:
        safe_msg = _APIKEY_SCRUB_RE.sub(r"\1***", str(e))
        logger.error(f"Error handling action '{action}': {safe_msg}")
        return {"success": False, "error": "Internal service error while processing request"}


def process_request(db_module, user_id: str, req_id: str, request_data: Dict[str, Any]):
    """Process an individual request node from Firebase RTDB."""
    if not isinstance(request_data, dict):
        return

    if not _is_safe_rtdb_key(str(user_id)) or not _is_safe_rtdb_key(str(req_id)):
        logger.warning("Ignoring bridge request with malformed user_id or req_id")
        return

    req_ref = db_module.reference(f"requests/{user_id}/{req_id}")

    # Discard stale requests older than MAX_REQUEST_AGE_MS
    req_ts = request_data.get("timestamp")
    if isinstance(req_ts, (int, float)) and req_ts > 0:
        now_ms = time.time() * 1000
        if now_ms - req_ts > MAX_REQUEST_AGE_MS:
            logger.warning(f"Discarding stale bridge request req_id={req_id} user_id={user_id}")
            try:
                req_ref.delete()
            except Exception:
                pass
            return

    # Enforce per-user rate limit
    if not _check_rate_limit(str(user_id)):
        logger.warning(f"Rate limit exceeded for bridge user_id={user_id}")
        try:
            req_ref.delete()
        except Exception:
            pass
        return

    action = str(request_data.get("action", ""))
    payload = request_data.get("payload", {})
    init_data = request_data.get("initData", "")
    bot_token = config.get("telegram", {}).get("token")
    allow_unverified_dev = bool(config.get("miniapp", {}).get("allowUnverifiedLocalDev", False))

    logger.info(f"Processing bridge request req_id={req_id} action={action} user_id={user_id}")

    verified_uid = str(user_id)
    verified_username = None

    # Cryptographically verify Telegram WebApp initData unless explicitly in local unverified dev mode
    if not allow_unverified_dev:
        is_valid_sig, tg_user = verify_telegram_init_data(init_data, str(bot_token or ""))
        if not is_valid_sig or not tg_user or str(tg_user.get("id")) != str(user_id).strip():
            logger.warning(
                f"Rejected bridge request req_id={req_id} from user_id={user_id}: invalid or missing Telegram initData signature"
            )
            try:
                resp_ref = db_module.reference(f"responses/{user_id}/{req_id}")
                resp_ref.set({"success": False, "error": "Unauthorized: invalid Telegram session"})
                req_ref.delete()
            except Exception as e:
                logger.error(f"Failed to clean up rejected request req_id={req_id}: {e}")
            return
        verified_uid = str(tg_user["id"])
        verified_username = tg_user.get("username")
    else:
        verified_username = request_data.get("username")

    # Verify user authorization (and admin privileges if action requires it)
    need_admin = _requires_admin(action)
    if not is_user_authorized(verified_uid, username=verified_username, check_admin=need_admin):
        logger.warning(f"Unauthorized bridge request from user_id={verified_uid} action={action} (admin_required={need_admin})")
        response_payload = {"success": False, "error": "Unauthorized"}
    else:
        response_payload = dispatch_action(action, payload, user_id=verified_uid)

    # Post response to /responses/{user_id}/{req_id} and delete request
    try:
        resp_ref = db_module.reference(f"responses/{user_id}/{req_id}")
        resp_ref.set(response_payload)
        req_ref.delete()
    except Exception as e:
        logger.error(f"Failed to write bridge response for req_id={req_id}: {e}")


def init_firebase_app():
    """Initialize Firebase Admin app using configured credentials."""
    import firebase_admin
    from firebase_admin import credentials

    miniapp_cfg = config.get("miniapp", {})
    if not miniapp_cfg.get("enable", False):
        logger.info("Telegram Mini App bridge is disabled in config.")
        return None

    db_url = miniapp_cfg.get("databaseURL")
    if not db_url:
        logger.error("Mini App bridge is enabled but 'miniapp.databaseURL' is not configured.")
        return None

    sa_path = miniapp_cfg.get("serviceAccountPath", "serviceAccountKey.json")
    if not os.path.isabs(sa_path):
        sa_path = os.path.join(ROOT_DIR, sa_path)

    if not os.path.exists(sa_path):
        logger.warning(f"Service account file not found at: {sa_path}. Bridge will not start.")
        return None

    try:
        cred = credentials.Certificate(sa_path)
        app = firebase_admin.initialize_app(cred, {"databaseURL": db_url})
        logger.info("Firebase Admin initialized successfully for Mini App bridge.")
        return app
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin: {e}")
        return None


async def start_bridge_listener():
    """Asynchronous entry point that listens for requests on Firebase RTDB."""
    global _app, _listener
    miniapp_cfg = config.get("miniapp", {})
    if not miniapp_cfg.get("enable", False):
        return

    app = init_firebase_app()
    if not app:
        return

    _app = app
    from firebase_admin import db

    def on_request_event(event):
        """Callback triggered on Realtime Database change events."""
        try:
            # Event path could be '/' (initial load), '/{userId}', or '/{userId}/{reqId}'
            path = event.path.strip("/")
            data = event.data

            if not data:
                return

            parts = [p for p in path.split("/") if p]
            if len(parts) == 0:
                # Top-level: dict of user_id -> dict of req_id -> request_data
                if isinstance(data, dict):
                    for u_id, user_reqs in data.items():
                        if isinstance(user_reqs, dict):
                            for r_id, req in user_reqs.items():
                                process_request(db, u_id, r_id, req)
            elif len(parts) == 1:
                # /requests/{user_id}
                u_id = parts[0]
                if isinstance(data, dict):
                    for r_id, req in data.items():
                        process_request(db, u_id, r_id, req)
            elif len(parts) == 2:
                # /requests/{user_id}/{req_id}
                u_id, r_id = parts[0], parts[1]
                process_request(db, u_id, r_id, data)
        except Exception as err:
            logger.error(f"Error handling RTDB event: {err}", exc_info=True)

    requests_ref = db.reference("requests")
    # listen() runs in a background thread provided by Firebase Admin
    _listener = requests_ref.listen(on_request_event)
    logger.info("Mini App bridge is actively listening for incoming requests.")

    while True:
        await asyncio.sleep(60)

